import logging
import os.path
import traceback
from threading import Thread, Event, Lock
from typing import List, Tuple

import devlog

from src import config, helper, database
from src.client.interface import Torrent
from src.filter.rule import RuleManager
from src.rss.parser import parser

logger = logging.getLogger(__name__)


class RSS(Thread):
    """
    This thread will check RSS feed.

    This thread are meant to be run in one instance. But it's possible to run multiple instance of this service.
    """

    def __init__(self, stop_event: Event, queue_lock: Lock, waiting_queue, rules):
        super().__init__()
        self.stop_event = stop_event
        self.queue_lock = queue_lock
        self.waiting_queue: List[Torrent] = waiting_queue

        self.clients: List[Tuple[Lock, List[Torrent]]] = []
        if rules:
            self.rule_manager = RuleManager.from_json(rules)
        else:
            self.rule_manager = RuleManager()

    def add_client(self, lock, downloads):
        self.clients.append((lock, downloads))

    @devlog.log_on_error(trace_stack=True)
    def run(self) -> None:
        while not self.stop_event.is_set():
            logger.info(f"Checking RSS feeds...")
            try:
                for log_file_path, link in config.RSS_LIST.items():
                    full_path = os.path.join(f"{config.DATA_DIR['log']}/rss/", log_file_path)
                    log_file = helper.file.read_file(full_path)

                    links = parser(link, log_file)

                    self.add_to_queue(links, full_path)

                logger.info(f"All rss downloaded. Sleeping for {helper.duration_humanizer(config.SLEEP['rss_check'])}")
                self.stop_event.wait(config.SLEEP["rss_check"])
            except Exception as e:
                with open(config.LOG_FILE['rss'], "a+") as f:
                    f.write(f"{e}\n{traceback.format_exc()}")
                self.stop_event.wait(10)  # timout before retrying

    def add_to_queue(self, links: dict, file_log: str) -> None:
        for title, link in links.items():
            if title in file_log:
                continue

            anime = helper.parse(title, True)

            self.validator(anime, link, file_log, title)

    def validator(self, anime, link, file_log, title) -> None:
        """
        In this project, the anime rule are follow.
        If it's unknown, it will be added to the waiting queue.
        if the same anime is already in the waiting queue, check which one is the best.
        - If the new one are uncensored and the old one not. The new one will replace the old one.
        - If the new one are censored and the old one not. The new one will be ignored.
        - If the new one have higher priority release group. The new one will replace the old one.
        - if the new one have newer release version. The new one will replace the old one.
        - Otherwise, the new one will be ignored.

        The same rule applies to the download queue, With slight modification.
        - If the old one is replaced (removed). Then if new one are in upload state.
          It will stay and the new one will add to queue/
        - Otherwise the old one will be removed
        """

        if self.rule_manager.check(anime):
            # If the anime unrecognized, we will add it to the waiting queue
            if anime.get("anime_type", "unknown").lower() == "unknown" or anime.get("anilist", 0) == 0:
                with self.queue_lock:
                    self.waiting_queue.append(Torrent(anime, link, file_log, title))
                return

            # uncensored will take over the censored version
            uncensored = "uncensored" in str(anime.get("other", "")).lower()
            identifier = f"{anime['anilist']}{anime['episode']}"

            # Extended check. Make sure the torrent is not in the waiting queue
            with self.queue_lock:
                for torrent in self.waiting_queue.copy():
                    existing_anime = torrent.anime
                    existing_identifier = f"{existing_anime['anilist']}{existing_anime.get('episode_number', 0)}"
                    if identifier == existing_identifier:
                        if not helper.should_download(anime, existing_anime, uncensored):
                            helper.file.add_to_log(file_log, title)
                            return
                        # the new torrent is better, remove the old one
                        self.waiting_queue.remove(torrent)

                        # should we break? because in the intended use case,
                        # there's should only one identifier in the waiting queue
                        break

            # Extend Check. Make sure the torrent is not in the download queue
            for lock, downloads in self.clients:
                with lock, self.queue_lock:
                    for download in downloads.copy():
                        existing_anime = download.anime
                        existing_identifier = f"{existing_anime['anilist']}{existing_anime.get('episode_number', 0)}"
                        if identifier == existing_identifier:
                            if not helper.should_download(anime, existing_anime, uncensored):
                                helper.file.add_to_log(file_log, title)
                                return
                            # the new torrent is better, remove the old one
                            # download.remove_torrent()
                            downloads.remove(download)

                            # should we break? because in the intended use case,
                            # there's should only one identifier in the download queue
                            break

            # Check the fansub preference from the database
            from_db = database.db.select("preference", {"anime_id": anime["anilist"]})
            if from_db:
                # the anime is in the database
                if uncensored and not from_db[0]["uncensored"]:
                    from_db[0]["release_group"] = anime["release_group"]
                    from_db[0]["uncensored"] = True
                    database.db.insert("preference", from_db[0])
                elif not uncensored and from_db[0]["uncensored"]:
                    # we want to download it anyway
                    # probably the uncensored version is not available yet
                    pass
                else:
                    priority = helper.fansub_priority(from_db[0]["release_group"], anime["release_group"])
                    if priority == 1:
                        pass  # we want to download it anyway and remove it when the desired fansub is available
                    elif priority == 0:
                        pass
                    else:
                        # this anime fansub has higher priority,
                        # so we update the fansub preference with the new one.
                        from_db[0]["release_group"] = anime["release_group"]
                        database.db.insert("preference", from_db[0])

            else:
                # if the preference is empty,
                # then create new preference entry
                to_db = {
                    "anime_name": anime["anime_title"],
                    "anime_id": anime["anilist"],
                    "release_group": anime["release_group"],
                    "uncensored": uncensored
                }
                database.db.insert("preference", to_db)

            with self.queue_lock:
                self.waiting_queue.append(Torrent(anime, link, file_log, title))

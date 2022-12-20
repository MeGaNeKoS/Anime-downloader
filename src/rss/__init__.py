import logging
import os.path
import traceback
from threading import Thread, Event, Lock
from typing import List, Tuple

import devlog

from src import config, helper
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
        if self.rule_manager.check(anime):
            with self.queue_lock:
                self.waiting_queue.append(Torrent(anime, link, file_log, title))

import logging
import os.path
import traceback
from threading import Thread, Event, Lock

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
    def __init__(self, stop_event: Event, queue_lock: Lock, waiting_queue):
        super().__init__()
        self.stop_event = stop_event
        self.queue_lock = queue_lock
        self.waiting_queue = waiting_queue

    @devlog.log_on_error(trace_stack=True)
    def run(self) -> None:
        rule_manager = RuleManager.from_json(config.RULES)
        while not self.stop_event.is_set():
            logger.info(f"Checking RSS feeds...")
            try:
                for file_log, link in config.RSS_LIST.items():
                    file_log_path = os.path.join(f"{config.DATA_DIR['log']}/rss/", file_log)
                    log_file = helper.file.read_file(file_log_path)

                    links = parser(link, log_file)

                    with self.queue_lock:
                        self.add_to_queue(rule_manager, links, full_path)

                logger.info(f"All rss downloaded. Sleeping for {helper.duration_humanizer(config.SLEEP['rss_check'])}")
                self.stop_event.wait(config.SLEEP["rss_check"])
            except Exception as e:
                with open(config.LOG_FILE['rss'], "a+") as f:
                    f.write(f"{e}\n{traceback.format_exc()}")
                self.stop_event.wait(10)  # timout before retrying

    def add_to_queue(self, manager: RuleManager, links: dict, file_log: str) -> None:
        for title, link in links.items():
            if title in file_log:
                continue

            anime = helper.parse(title, True)

            with self.queue_lock:
                if manager.check(anime):
                    self.waiting_queue.append(Torrent(anime, link, file_log))

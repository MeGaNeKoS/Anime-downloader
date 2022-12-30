import ctypes
import logging
import os.path
import traceback
from threading import Event, RLock
from typing import List, Tuple, Dict

import devlog

from interfaces.thread import BaseThread
from src import helper
from src.exception.thread import ForceRestartException
from interfaces.interface import Torrent
from src.filter.rule import RuleManager
from src.rss.parser import parser

module_logger = logging.getLogger(__name__)


class RSS(BaseThread):
    """
    This thread will check RSS feed.

    This thread are meant to be run in one instance. But it's possible to run multiple instance of this service.
    """
    module_logger = logging.getLogger(__name__)

    def __init__(self, stop_event: Event, sleep_event: Event, queue_lock: RLock, waiting_queue: list,
                 rules: List[RuleManager], config: dict, *, daemon: bool = True):

        self._rule_manager = rules
        self.clients: List[Tuple[RLock, List[Torrent]]] = []
        self.rss_root_folder = config["watchLog"].get("rootFolder", "rss")
        self._watch_list: Dict[str, str] = config["watchList"]

        # Set up logger
        logger = config["logger"]
        super().__init__(stop_event, sleep_event, queue_lock, waiting_queue,
                         logger=logger, sleep_time=config.get("checkIntervalSeconds", 60), daemon=daemon,
                         traceback_file=config.get("exceptionTraceback", "rss_traceback.log"))

    @property
    def rule_manager(self):
        return self._rule_manager

    @rule_manager.setter
    def rule_manager(self, rules: List[RuleManager]):
        with self._lock:
            self._rule_manager = rules

    @property
    def watch_list(self):
        return self._watch_list

    @watch_list.setter
    def watch_list(self, _watch_list: Dict[str, str]):
        with self._lock:
            self._watch_list = _watch_list

    def add_client(self, lock, downloads):
        self.clients.append((lock, downloads))

    def add_to_queue(self, links: dict, file_log: str) -> None:
        for title, link in links.items():
            if title in file_log:
                continue

            anime = helper.parse(title, True)

            self.validator(anime, link, file_log, title)

    @devlog.log_on_error(trace_stack=True)
    def run(self) -> None:
        while not self.stop_event.is_set():
            self.logger.info(f"Checking RSS feeds...")
            try:
                for file_name, link in self._watch_list.items():
                    full_path = os.path.join(self.rss_root_folder, file_name)
                    log_file = helper.file.read_file(full_path)

                    links = parser(link, log_file)

                    self.add_to_queue(links, full_path)

                self.logger.info(
                    f"All rss downloaded. Sleeping for {helper.duration_humanizer(self._sleep_time)}")
                self.stop_event.wait(self._sleep_time)
            except ForceRestartException:
                self.logger.info("Restarting...")
                continue
            except Exception as e:
                with open(self.exception_traceback, "a+") as f:
                    f.write(f"{e}\n{traceback.format_exc()}")
                self._sleep_event.wait(10)  # timout before retrying

    def validator(self, anime, link, file_log, title) -> None:
        for instance in self.rule_manager:
            if instance.check(anime):
                with self.queue_lock:
                    self.waiting_queue.append(Torrent(anime, link, file_log, title))

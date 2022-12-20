import logging
import time
import traceback
from threading import Thread, Event, Lock, RLock
from typing import List, Dict

import devlog

from src import config, helper
from src.client import QBittorrent as Client
from src.client.interface import TorrentInfo, Torrent

logger = logging.getLogger(__name__)


class Download(Thread):
    """
    This class is meant to be run in one instance. But it's possible to run multiple instance of this service.
    The source of the RSS can be shared between multiple instance of this service.
    """
    def __init__(self, stop_event: Event, queue_lock: Lock, waiting_queue: list,
                 removal_time: int = 0, max_download: int = 5, max_fail: int = 5):
        super().__init__()
        self.client = Client(*config.CLIENT_CONFIG_ARGS, **config.CLIENT_CONFIG_KWARGS)
        self.client.login()
        self.stop_event = stop_event
        self.queue_lock = queue_lock
        self.waiting_queue = waiting_queue
        self.removal_time = removal_time

        self._max_concurrent_downloads = max_download
        self._download_queue: List[Torrent] = []
        self._remove_queue: Dict[float, Torrent] = {}

        self._max_fail = max_fail
        self._number_retries = 10
        self._max_delay_time_seconds = 60
        self._lock = RLock()

    @devlog.log_on_error(trace_stack=True)
    def run(self):
        while not self.stop_event.is_set():
            logger.info(f"Checking download queue...")
            try:
                # test if the client is connected
                self.client.connect()
                with self._lock:
                    self.check_completion()
                    for dtime, download in self._remove_queue.copy().items():
                        if time.time() > dtime and download.remove_torrent():
                            # just in case
                            if download in self._download_queue:
                                self._download_queue.remove(download)
                            self._remove_queue.pop(dtime)

                # Give the other threads a chance to run
                with self.queue_lock:
                    # Avoid soft lock by looping with exact number of items
                    for _ in range(len(self.waiting_queue)):
                        if len(self._download_queue) < self._max_concurrent_downloads:
                            self.add_torrent()
                        else:
                            break

                logger.info(f"All download finished. "
                            f"Sleeping for {helper.duration_humanizer(config.SLEEP['download_check'])}")
                self.stop_event.wait(config.SLEEP["download_check"])
            except ConnectionError as e:
                logger.error(f"Failed to connect to torrent client: {e}")
                for i in range(self._number_retries):
                    # try to reconnect
                    if self.client.login():
                        break

                    # back off exponentially with max 60 seconds
                    time.sleep(min(2 ** i, self._max_delay_time_seconds))
                else:
                    self.stop_event.set()
                    logger.critical("Failed to reconnect to torrent client. Exiting...")

            except Exception as e:
                with open("torrent.log", "a+") as f:
                    f.write(f"{e}\n{traceback.format_exc()}")

    def add_torrent(self, num_retries=10) -> bool:
        """
        This should be called with queue_lock acquired
        """
        try:
            item: Torrent = self.waiting_queue.pop(0)
        except IndexError:
            return False

        if not item:
            return False

        item.set_client(self.client)
        for _ in range(num_retries):
            if item.add_torrent():
                self._download_queue.append(item)
                return True
        else:
            item.fail += 1
            if item.fail >= self._max_fail:
                logger.error(f"Failed to add torrent {item.anime} to client after {self._max_fail} tries. Skipping...")
                return False
            self.waiting_queue.append(item)
            return False

    def check_completion(self):
        for download in self._download_queue:
            torrent: TorrentInfo = download.get_info()

            # remove non-existent torrents
            if not torrent:
                self._remove_queue[time.time()] = download

            if torrent['status'] == 'complete':
                torrent['status'] = 'uploading'
                # make sure it deleted after the torrent_on_finish finish its job
                download.torrent_on_finish(self._lock, self.removal_time, self._download_queue, self._remove_queue)


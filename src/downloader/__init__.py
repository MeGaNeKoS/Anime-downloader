import logging
import time
import traceback
from threading import Event, RLock
from typing import List, Dict

import devlog

from interfaces.thread import BaseThread
from src import helper, client
from interfaces.interface import TorrentInfo, Torrent
from src.exception.thread import ForceRestartException


class Download(BaseThread):
    """
    This class is meant to be run in one instance. But it's possible to run multiple instance of this service.
    The source of the RSS can be shared between multiple instance of this service.
    """
    module_logger = logging.getLogger(__name__)

    def __init__(self, stop_event: Event, sleep_event: Event, queue_lock: RLock, waiting_queue: list,
                 config: dict, *, daemon: bool = True):
        self.removal_time = config["removalTimeSeconds"]
        self._max_concurrent_downloads = config["maxConcurrentDownloads"]
        self._download_queue: List[Torrent] = []
        self._max_fail = config["maxFail"]
        self._max_delay_time_seconds = config["maxDelayTimeSeconds"]
        self._remove_queue: Dict[float, Torrent] = {}

        # Set up logger
        logger = config["logger"]
        super().__init__(stop_event, sleep_event, queue_lock, waiting_queue,
                         logger=logger, sleep_time=config.get("checkIntervalSeconds", 60), daemon=daemon,
                         traceback_file=config.get("exceptionTraceback", "download_traceback.log"))
        client_cfg = config["client"]
        self._number_retries = client_cfg["maxRetries"]
        self.client = client.clients[client_cfg["name"]](**client_cfg["config"])
        if client_cfg["login"]:
            try:
                self.client.login()
            except Exception:
                return

    @devlog.log_on_error(trace_stack=True)
    def run(self):
        while not self.stop_event.is_set():
            self.logger.info(f"Checking download queue...")
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
                with self._lock, self.queue_lock:
                    # Avoid soft lock by looping with exact number of items
                    for _ in range(len(self.waiting_queue)):
                        if len(self._download_queue) < self._max_concurrent_downloads:
                            self.add_torrent()
                        else:
                            break

                self.logger.info(f"All download finished. "
                                 f"Sleeping for {helper.duration_humanizer(self.sleep_time)}")
                self._sleep_event.wait(self.sleep_time)
            except ForceRestartException:
                self.logger.info("Restarting...")
                continue
            except ConnectionError as e:
                try:
                    self.logger.error(f"Failed to connect to torrent client: {e}")
                    for i in range(self._number_retries):
                        # try to reconnect
                        if self.client.login():
                            break

                        # back off exponentially with max 60 seconds
                        time.sleep(min(2 ** i, self._max_delay_time_seconds))
                    else:
                        self.logger.critical("Failed to reconnect to torrent client. Exiting...")
                except ForceRestartException:
                    self.logger.info("Restarting...")
                    continue
            except Exception as e:
                with open(self.exception_traceback, "a+") as f:
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
            if item.add_torrent(self._lock, self.removal_time, self._download_queue, self._remove_queue):
                self._download_queue.append(item)
                return True
        else:
            item.fail += 1
            if item.fail >= self._max_fail:
                self.logger.error(
                    f"Failed to add torrent {item.anime} to client after {self._max_fail} tries. Skipping...")
                return False
            self.waiting_queue.append(item)
            return False

    def check_completion(self):
        for download in self._download_queue:
            torrent: TorrentInfo = download.get_info()

            # remove non-existent torrents
            if not torrent:
                self._remove_queue[time.time()] = download

            if download.status == 'complete':
                download.status = 'finished'
                # make sure it deleted after the torrent_on_finish finish its job
                download.torrent_on_finish(self._lock, self.removal_time, self._download_queue, self._remove_queue)

    """
    New features, not used yet.
    This feature is used in the validation of the RSS item before adding it to the queue.
    Based on the number of client, it will wait until got all client's lock before checking the queue.
    """

    def get_lock(self) -> RLock:
        return self._lock

    def get_downloads(self) -> List[Torrent]:
        return self._download_queue

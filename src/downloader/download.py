import logging
import time
import traceback
from threading import Thread, Event

import devlog

from src import config, helper
from src.client import QBittorrent as Client
from src.client.interface import TorrentInfo, Torrent
from src.share_var import queue_lock, waiting_queue, downloading_queue, uploaded_queue

logger = logging.getLogger(__name__)


class Download(Thread):
    def __init__(self, stop_event: Event):
        super().__init__()
        self.client = Client(*config.CLIENT_CONFIG_ARGS, **config.CLIENT_CONFIG_KWARGS)
        self.client.login()
        self.stop_event = stop_event

        self._max_fail = 3
        self._number_retries = 10
        self._max_delay_time_seconds = 60

    @devlog.log_on_error(trace_stack=True)
    def run(self):
        while not self.stop_event.is_set():
            logger.info(f"Checking download queue...")
            try:
                # test if the client is connected
                self.client.connect()
                with queue_lock:
                    self.check_completion()

                # Give the other threads a chance to run
                with queue_lock:
                    # Avoid soft lock by looping with exact number of items
                    for _ in range(len(waiting_queue)):
                        if len(downloading_queue) < config.MAX_CONCURRENT_DOWNLOADS:
                            self.add_torrent()
                        else:
                            break

                # Give the other threads a chance to run
                with queue_lock:
                    for dtime, download in uploaded_queue.copy().items():
                        if time.time() > dtime and download.remove_torrent():
                            if download in downloading_queue:
                                downloading_queue.remove(download)
                            uploaded_queue.pop(dtime)

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
            item: Torrent = waiting_queue.pop(0)
        except IndexError:
            return False

        if not item:
            return False

        item.set_client(self.client)
        for _ in range(num_retries):
            if item.add_torrent():
                downloading_queue.append(item)
                return True
        else:
            item.fail += 1
            if item.fail >= self._max_fail:
                logger.error(f"Failed to add torrent {item.anime} to client after {self._max_fail} tries. Skipping...")
                return False
            waiting_queue.append(item)
            return False

    @staticmethod
    def check_completion():
        """
        This should be called with queue_lock acquired
        """
        for download in downloading_queue:  # type: Torrent
            torrent: TorrentInfo = download.get_info()

            # remove non-existent torrents
            if not torrent:
                uploaded_queue.append(download)

            print(torrent)
            if torrent['status'] == 'complete':
                torrent['status'] = 'uploading'
                download.torrent_on_finish()
                deletion_time = time.time() + config.UPLOAD_REMOVAl_TIME_SECONDS
                uploaded_queue[deletion_time] = download

import base64
import functools
import logging
import os
import re
import threading
import time
from typing import List, Union

import qbittorrentapi
from qbittorrentapi import TorrentInfoList, TorrentFilesList
from qbittorrentapi.request import Request

from src import helper
from interfaces.interface import Client, TorrentInfo, TorrentFile, Torrent

logger = logging.getLogger(__name__)


def qbittorrent_activated_cooldown(event: threading.Event):
    """
    This following code mean to add a delay time to the client's method before request to the application.
    This is to prevent the client from being overloaded and ignoring the request,
    especially when the client on heavy load.

    This part only add cooldown whenever the Client class tries to make an API call. Since this is a global timer,
    ideally we only sleep when we want to execute the request. Meanwhile, the code should continue the call preparation.
    However, since I don't know where the request will be executed, I have to sleep somewhere before it executed.
    This is not ideal, but it is the best I can do.

    P.S: since the preparation is very fast, the performance impact is negligible.

    Every client can behave differently. Only implement this class when you need it.
    Note: I chose the `_request_manager` method because based on observation this is the entry point for API calls.
    My observation may be wrong, so if you find a better way to do this (the actual method that execute the call),
    please let me know. As it can improve the performance of the client. a little.
    """

    original_request = Request._request_manager

    cooldown_last_call = 0
    cooldown_timer = 0.2

    def _delayed_request_manager(*args, **kwargs):
        # Wait until the COOLDOWN_TIMER time has passed
        nonlocal cooldown_last_call
        current_time = time.time()
        elapsed_time = current_time - cooldown_last_call
        event.wait(max(0., cooldown_timer - elapsed_time))
        cooldown_last_call = time.time()
        return original_request(*args, **kwargs)

    Request._request_manager = functools.singledispatch(_delayed_request_manager)


class QBittorrent(Client):

    def __init__(self, *args, **kwargs):
        """
        Initialize the client. Any parameter is passed to the real client.
        """
        self._default_category = None
        self._default_tag = None
        self._lock = threading.RLock()  # Required on multithreading applications
        self._event = threading.Event()

        # This is necessary because the Qbittorrent takes some time to update the information. Especially on heavy load.
        self._number_retries = 10
        self._wait_time_second = 0.2  # wait time before each operation.
        self._max_wait_time_seconds = 10
        self.client: qbittorrentapi.Client = qbittorrentapi.Client(*args, **kwargs)

    def set_event(self, event: threading.Event):
        self._event = event

    @staticmethod
    def run_in_thread(func):
        def wrapper(*args, **kwargs):
            thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
            thread.start()

        return wrapper

    # Utility methods
    @classmethod
    def _populate_torrent_files(cls, files: TorrentFilesList):
        """
        Convert the torrent files to List[TorrentFile] object.
        """
        normalize = []
        for file in files:
            folder_path, filename = os.path.split(file.name)
            normalize.append(TorrentFile(
                identifier=file.index,
                name=filename,  # individual file name
                size=file.size,  # individual file size
                downloaded=file.priority != 0,  # 0 mean no download
                folder_path=folder_path,  # folder path
            ))
        return normalize

    @classmethod
    def _populate_torrent_info(cls, entries: TorrentInfoList, max_data=-1) -> List[TorrentInfo]:
        """
        Convert the torrent information to List[TorrentInfo] object.
        """
        normalize = []
        for entry in entries.data[:max_data]:
            if entry.state_enum.is_checking:
                state = "checking"
            elif entry.state_enum.is_complete:
                state = "complete"
            elif entry.state_enum.is_downloading:
                state = "downloading"
            elif entry.state_enum.is_errored:
                state = "error"
            elif entry.state_enum.is_paused:
                state = "paused"
            else:
                state = "unknown"

            files = cls._populate_torrent_files(entry.files)
            data = TorrentInfo(
                torrent_hash=entry.hash,
                name=entry.name,
                progress=entry.progress,
                status=state,
                category=entry.category,
                tags=entry.tags,
                files=files,
                save_path=entry.save_path)
            normalize.append(data)

        return normalize

    # Connection methods
    def connect(self):
        # check if the client is connected
        if not self.client.is_logged_in:
            raise ConnectionError("Could not connect to the client")

    def login(self) -> bool:
        try:
            self.client.auth_log_in()
            return True
        except (qbittorrentapi.LoginFailed, qbittorrentapi.Forbidden403Error) as e:
            logger.error(f"Could not login to the client: {e}")
            return False

    # Torrent methods
    def add_torrent(self, torrent: Torrent) -> str:
        torrent_url = torrent.url
        tags = self._default_tag
        category = self._default_category

        if not isinstance(tags, list):
            tags = [tags]

        tags = list(filter(None, tags))

        identifier = f"identifier-{time.time()}"  # this used to identify the torrent since the client only return Ok.
        for url in torrent_url:
            if not url:
                continue

            info_hash = url.startswith("magnet:")
            if info_hash:
                candidate = re.findall("urn:btih:(.*?)(?:&|$)", url, flags=re.IGNORECASE)
                for info_hash in candidate:
                    if len(info_hash) == 40 or len(info_hash) == 64:
                        break
                    if len(info_hash) == 32:
                        info_hash = base64.b32decode(info_hash).hex()
                        break
                else:
                    logger.info(f"Could not find info_hash in magnet link: {url}")
                    continue

            if not info_hash and identifier not in tags:
                tags.append(identifier)

            if not tags:
                tags = None

            for _ in range(self._number_retries):
                with self._lock:
                    # try to add the torrent
                    self.client.torrents_add(url, tags=tags, category=category)

                    # Verify if the torrent was added.
                    # Sometimes the torrent failed because the torrent is already in the client.
                    if info_hash:
                        if self.get_torrent_info(info_hash):
                            # update the torrent information
                            return info_hash
                    else:
                        data = self.get_torrent_info(tags=identifier)
                        if data:
                            self.torrent_remove_tag(data["hash"], [identifier], True)
                            return data["hash"]

                # wait before retry
                self._event.wait(self._wait_time_second)
                if self._event.is_set():
                    break
        return ""

    def get_torrent_info(self, torrent_hash: str = None, tags=None, category=None) -> Union[TorrentInfo, None]:
        for _ in range(self._number_retries):
            with self._lock:
                try:
                    entries = self.client.torrents_info(torrent_hashes=torrent_hash, tag=tags, category=category)
                    if entries:
                        return self._populate_torrent_info(entries, 1)[0]
                except qbittorrentapi.APIError as e:
                    logger.error(f"Could not get torrent information: {e}")
                    self._event.wait(self._wait_time_second)
                    if self._event.is_set():
                        break
                except Exception as e:
                    logger.error(f"Could not get torrent information: {e}")
                    return None
        return None

    def remove_torrent(self, torrent_hash: str, delete_files: bool) -> bool:
        for i in range(self._number_retries):
            with self._lock:
                self.client.torrents_delete(torrent_hashes=torrent_hash, delete_files=delete_files)

                # verify if the torrent was removed
                if not self.get_torrent_info(torrent_hash):
                    return True

            # let it in with statement to give a gap between failed attempts
            self._event.wait(self._wait_time_second)
            if self._event.is_set():
                break
        return False

    # Event behavior methods
    @run_in_thread
    def torrent_on_finish(self, torrent: Torrent, lock: threading.Lock,
                          removal_time: float, download_queue: list, remove_queue: dict) -> None:
        """
        Do whatever you want when the torrent is finished.
        """
        logger.info("Starting post processing")
        logger.info(f"Torrent data: {torrent.title}")
        dtime = time.time() + removal_time
        with lock:
            # remove the torrent from the download queue immediately
            helper.file.add_to_log(torrent.log_file, torrent.title)
            if torrent in download_queue:
                download_queue.remove(torrent)
            remove_queue[dtime] = torrent
        return

    @run_in_thread
    def torrent_on_start(self, torrent: Torrent, lock: Union[threading.Lock, threading.RLock],
                         removal_time: float, download_queue: list, remove_queue: dict) -> None:
        """
        Do whatever you want when the torrent is started.
        """
        logger.info("Starting pre processing")
        logger.info(f"Torrent data: {torrent.title}")
        return

    # client specific methods
    def torrent_remove_tag(self, torrent_hash: str, tags: list, delete=False) -> bool:
        """
        Delete mean delete the tag itself. Otherwise, it will just remove the tag from the torrent.
        """
        for _ in range(self._number_retries):
            with self._lock:
                if delete:
                    self.client.torrents_delete_tags(tags=tags)
                else:
                    self.client.torrents_remove_tags(torrent_hashes=torrent_hash, tags=tags)

                data = self.get_torrent_info(torrent_hash)
                for tag in tags:
                    if tag not in data['tags']:
                        continue
                    break
                else:
                    return True
        return False

from abc import ABC, abstractmethod
from threading import Lock, RLock
from typing import List, Union


class TorrentFile(dict):
    def __init__(self, identifier, name, size, downloaded: bool, folder_path):
        """
        I'm not sure is this data enough, but we can update later.

        :param identifier: unique identifier of the file in the torrent file_list
        :param name: name of the file
        :param size: total size of the file
        :param downloaded: is the file will be downloaded
        :param folder_path: path to the folder where the file will be downloaded
        """
        super().__init__()
        self['identifier'] = identifier
        self["name"] = name
        self['size'] = size
        self['downloaded'] = downloaded
        self['folder_path'] = folder_path


class TorrentInfo(dict):
    def __init__(self, torrent_hash=None, name=None, progress=None,
                 status=None, category=None, tags=None, files: List[TorrentFile] = None,
                 save_path=None):
        """
        I'm not sure is this data enough, but we can update later.

        :param torrent_hash: unique identifier of the torrent
        :param name: name of the torrent
        :param progress: progress of the torrent
        :param status: status of the torrent
        :param category: category of the torrent
        :param tags: tags of the torrent
        :param files: list of files in the torrent
        :param save_path: path to the folder where the torrent will be downloaded
        """
        super().__init__()
        self["hash"] = torrent_hash
        self["name"] = name
        self["progress"] = progress
        self["category"] = category
        self["status"] = status
        self["tags"] = tags
        if files is None:
            files = []
        self["files"] = files
        self["save_path"] = save_path


class Torrent:
    def __init__(self, anime, url: list, file_log: str, title: str, remove_file: bool = False):
        """
        :param anime: Anime dict
        :param url: list of url
        :param file_log: list of path to the file log
        :param remove_file: remove torrent file if this torrent is removed
        """
        self.anime = anime
        self.url = url
        self.log_file: list = [file_log]
        self.title = title

        self.client: Union[Client, None] = None
        self.hash: str = ""
        self.fail = 0
        self.remove_file = remove_file
        self.status = "waiting"
        self.tags = ""
        self.track = True

    def set_client(self, client: 'Client') -> None:
        """
        Set client for this torrent
        """
        self.client = client

    def get_info(self) -> TorrentInfo:
        """
        Get the information of the torrent.
        """
        result = self.client.get_torrent_info(self.hash)
        if self.status != "uploading":
            if result:
                self.status = result["status"]
        return result

    def add_torrent(self, lock: Union[Lock, RLock], removal_time: float, download_queue: list,
                    remove_queue: dict) -> bool:
        """
        Add torrent to client
        """
        if not self.hash:
            self.hash = self.client.add_torrent(self)
        if self.hash:
            # Call when torrent is added successfully
            self.client.torrent_on_start(self, lock, removal_time, download_queue, remove_queue)
            return True
        return False

    def cancel_download(self) -> bool:
        """
        Cancel download. If the torrent is already completed, then it will not be removed.
        Because it possible it's doing the on_finish event.
        """
        anime = self.get_info()
        if anime['status'] == 'complete':
            return False
        return self.remove_torrent()

    def remove_torrent(self) -> bool:
        """
        Remove torrent from client.
        """
        if self.client.remove_torrent(self.hash, self.remove_file):
            return True
        return False

    def torrent_on_finish(self, lock: Union[Lock, RLock], removal_time: float, download_queue: list,
                          remove_queue: dict) -> None:
        """
        Call when torrent is finished
        """
        self.client.torrent_on_finish(self, lock, removal_time, download_queue, remove_queue)


class Client(ABC):
    """
    This is the base class for all clients.
    Any method that called from the service(Download) thread should be implemented here.
    Otherwise, it should be implemented in the client class.
    """

    # Connection methods
    @abstractmethod
    def connect(self):
        """
        This class is used to check connection to the client.
        """
        raise NotImplemented

    @abstractmethod
    def login(self):
        """
        This class is used to log in to the client.
        """
        raise NotImplemented

    # Torrent methods
    @abstractmethod
    def add_torrent(self, torrent: Torrent) -> str:
        """
        This class is used to add a torrent to the client. Torrent url can be a magnet link or a link to a torrent file.
        This function returns Info-hash if the torrent was added successfully, otherwise it returns False.
        """
        raise NotImplemented

    @abstractmethod
    def get_torrent_info(self, torrent_hash: str) -> TorrentInfo:
        """
        Get the information of a torrent.
        This function returns a dictionary with the information of the torrent.
        """
        raise NotImplemented

    @abstractmethod
    def remove_torrent(self, torrent_hash: str, delete_files: bool) -> bool:
        """
        This class is used to remove a torrent from the client. Since the torrent hash is unique,
        it is used to identify the torrent.
        This function returns True if the torrent was removed successfully, otherwise it returns False.
        """
        raise NotImplemented

    # Event behavior methods
    @abstractmethod
    def torrent_on_start(self,  torrent: Torrent, lock: Lock, removal_time: float, download_queue: list,
                         remove_queue: dict) -> None:
        """
        This function is called when the torrent is added to the client.
        """
        raise NotImplemented

    @abstractmethod
    def torrent_on_finish(self, torrent: Torrent, lock: Lock, removal_time: float, download_queue: list,
                          remove_queue: dict) -> None:
        """
        This function is called when the torrent is finished.
        """
        raise NotImplemented

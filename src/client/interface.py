from abc import ABC, abstractmethod
from typing import List, Union


class TorrentFile(dict):
    def __init__(self, identifier, name, size, downloaded: bool, folder_path):
        """
        I'm not sure is this data enough, but we can update later.
        """
        super().__init__()
        self['identifier'] = identifier
        self["name"] = name
        self['size'] = size
        self['folder_path'] = folder_path
        self['downloaded'] = downloaded


class TorrentInfo(dict):
    def __init__(self, torrent_hash=None, name=None, progress=None,
                 status=None, category=None, tags=None, files: List[TorrentFile] = None,
                 save_path=None):
        """
        I'm not sure is this data enough, but we can update later.
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
    def __init__(self, anime, url: list):
        self.anime = anime
        self.url = url

        self.client: Union[Client, None] = None
        self.hash: str = ""
        self.fail = 0
        self.remove_file = False

    def set_client(self, client: 'Client') -> None:
        self.client = client

    def get_info(self) -> TorrentInfo:
        print(f"Getting info {self.hash}")
        return self.client.get_torrent_info(self.hash)

    def add_torrent(self) -> bool:
        self.hash = self.client.add_torrent(self)
        if self.hash:
            self.client.torrent_on_start(self)
            return True
        return False

    def remove_torrent(self) -> bool:
        if self.client.remove_torrent(self.hash, self.remove_file):
            return True
        return False

    def torrent_on_finish(self) -> None:
        self.client.torrent_on_finish(self)


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
    def add_torrent(self, torrent: Torrent) -> bool:
        """
        This class is used to add a torrent to the client. Torrent url can be a magnet link or a link to a torrent file.
        This function returns True if the torrent was added successfully, otherwise it returns False.
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
    def get_torrents(self) -> List[TorrentInfo]:
        """
        Get all torrents from the client. This function returns a list of dictionaries.
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
    def torrent_on_start(self, torrent: Torrent) -> None:
        """
        This function is called when the torrent is added to the client.
        """
        raise NotImplemented

    @abstractmethod
    def torrent_on_finish(self, torrent: Torrent) -> None:
        """
        This function is called when the torrent is finished.
        """
        raise NotImplemented

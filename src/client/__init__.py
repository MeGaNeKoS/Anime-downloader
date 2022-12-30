# set your own client class here
from src.client.qbittorrent import QBittorrent, qbittorrent_activated_cooldown

__all__ = ["clients", "qbittorrent_activated_cooldown"]
clients = {
    "qbittorrent": QBittorrent
}

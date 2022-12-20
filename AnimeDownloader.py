import logging
import threading
import time

from src import config, share_var
from src.client import qbittorrent_activated_cooldown
from src.downloader import Download
from src.rss import RSS

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

stop_event = threading.Event()


def main():
    logger.info(f"Starting Anime Downloader...")

    threads = []
    rss_thread = RSS(stop_event, share_var.queue_lock, share_var.waiting_queue, config.RULES)
    rss_thread.start()
    threads.append(rss_thread)

    qbittorrent_activated_cooldown(stop_event)

    torrent_thread = Download(stop_event, share_var.queue_lock, share_var.waiting_queue)
    torrent_thread.start()
    rss_thread.add_client(torrent_thread.get_lock(), torrent_thread.get_downloads())
    threads.append(torrent_thread)

    thread_status = [thread.is_alive() for thread in threads]
    try:
        while any(thread_status):
            thread_status = [thread.is_alive() for thread in threads]
            time.sleep(config.SLEEP["global"])
    except KeyboardInterrupt:
        stop_event.set()
        logger.info("Stopping Anime Downloader...")
        logger.info("Waiting for all threads to stop...")
        for thread in threads:
            logger.info(f"Waiting for {thread.name} to stop...")
            thread.join()
        logger.info("Anime Downloader stopped.")


if __name__ == '__main__':
    main()

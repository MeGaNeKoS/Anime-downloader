import logging
import threading
import time

from src import config
from src.downloader.download import Download
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
    rss_thread = RSS(stop_event)
    rss_thread.start()
    threads.append(rss_thread)

    torrent_thread = Download(stop_event)
    torrent_thread.start()
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

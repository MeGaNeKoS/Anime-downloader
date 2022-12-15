import logging
import threading
import time

from src import config
from src.rss import RSS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stop_event = threading.Event()


def main():
    logger.info(f"Starting Anime Downloader...")

    threads = []
    rss_thread = RSS(stop_event,
                     config.RSS_LIST,
                     f"{config.DATA_DIR['log']}/rss/")
    rss_thread.start()
    threads.append(rss_thread)

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
            thread.join()
        logger.info("Anime Downloader stopped.")

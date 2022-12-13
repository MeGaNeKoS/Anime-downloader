import logging
import threading
import time
import traceback

import devlog

from src import config
from src import helper, rss
from src.filter.rule import RuleManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stop_event = threading.Event()


@devlog.log_on_error(trace_stack=True)
def start_rss():
    rule_manager = RuleManager.from_json(config.RULES)
    while not stop_event.is_set():
        logger.debug(f"Checking RSS feeds...")
        try:
            for file_log, link in config.RSS_LIST.items():
                file_log_path = f"{config.DATA_DIR['log']}/rss/{file_log}"
                log_file = helper.file.read_file(file_log_path)

                links = rss.parser(link, log_file)

                rss.add_to_queue(rule_manager, links, file_log_path)

            logger.info(f"All rss downloaded. Sleeping for {helper.duration_humanizer(config.SLEEP['rss_check'])}")
            stop_event.wait(config.SLEEP["rss_check"])
        except Exception as e:
            with open("torrent.log", "a+") as f:
                f.write(f"{e}\n{traceback.format_exc()}")


def main():
    logger.info(f"Starting Anime Downloader...")

    threads = []
    thread = threading.Thread(target=start_rss, daemon=True)
    thread.start()
    threads.append(thread)

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


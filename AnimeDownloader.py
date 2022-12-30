import logging
import threading
import time
import json

from src.client import qbittorrent_activated_cooldown
from src.downloader import Download
from src.filter.rule import RuleManager
from src.rss import RSS
from src import helper

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

stop_event = threading.Event()
stop_event_notification = []


def main():
    logger.info(f"Starting Anime Downloader...")

    with open("config.json.example", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    helper.set_legalize_char(config["legalizeCharacter"])
    helper.file.set_max_log(config["maxLogItem"])
    rss_threads = {}
    download_threads = {}
    queue = {}
    rules_manager = {}

    # Initialize the rule_manager
    for name, rule in config["rules"].items():
        rules_manager[name] = RuleManager.from_json(rule)

    # Initialize the queue, and it's Lock
    for waiting_queue_name in config["waitingQueue"]:
        queue[waiting_queue_name] = (threading.RLock(), [])

    # Initialize the RSS thread
    for name, cls_config in config["rssInstance"].items():
        # get the queue and it's lock
        queue_name = cls_config["queue"]
        queue[queue_name] = (lock, waiting_queue) = queue.get(queue_name, (threading.RLock(), []))

        # get all rules
        rules = [rules_manager[rule_name] for rule_name in cls_config["rules"]]
        cls_config["logger"].setdefault("name", name)
        cls_config.setdefault("exceptionTraceback", config["exceptionTraceback"])
        sleep_event = threading.Event()
        stop_event_notification.append(sleep_event)

        rss_threads[name] = thread = RSS(stop_event, sleep_event, lock, waiting_queue, rules, cls_config)
        thread.start()

    qbittorrent_activated_cooldown(stop_event)

    # Initialize the Download thread
    for name, cls_config in config["downloadInstance"].items():
        # get the queue and it's lock
        queue_name = cls_config["queue"]
        queue[queue_name] = (lock, waiting_queue) = queue.get(queue_name, (threading.RLock(), []))

        cls_config["logger"].setdefault("name", name)

        cls_config.setdefault("exceptionTraceback", config["exceptionTraceback"])
        sleep_event = threading.Event()
        stop_event_notification.append(sleep_event)

        download_threads[name] = thread = Download(stop_event, sleep_event, lock, waiting_queue, cls_config)
        thread.start()
        for source in config["rssInstance"]:
            rss_threads.get(source).add_client(thread.get_lock(), thread.get_downloads())

    thread_status = True
    try:
        while thread_status:
            rss_thread_status = [thread.is_alive() for thread in rss_threads.values()]
            download_threads_status = [thread.is_alive() for thread in download_threads.values()]
            thread_status = any(rss_thread_status + download_threads_status)

            time.sleep(config["checkIntervalSeconds"])
    except KeyboardInterrupt:
        stop_event.set()
        for event in stop_event_notification:
            event.set()

        logger.info("Stopping Anime Downloader...")
        logger.info("Waiting for all threads to stop...")
        for name, thread in rss_threads.items():
            logger.info(f"Waiting for {name} to stop...")
            thread.raise_exception(KeyboardInterrupt)
            thread.join(config["maxJoinTimeSeconds"])
        for name, thread in download_threads.items():
            logger.info(f"Waiting for {name} to stop...")
            thread.raise_exception(KeyboardInterrupt)
            thread.join(config["maxJoinTimeSeconds"])

        logger.info("Anime Downloader stopped.")


if __name__ == '__main__':
    main()

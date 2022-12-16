import logging
import os.path
import traceback
from threading import Thread, Event

import devlog

from src import config, helper
from src.filter.rule import RuleManager
from src.rss.parser import parser
from src.rss.validator import add_to_queue
from src.share_var import queue_lock

logger = logging.getLogger(__name__)


class RSS(Thread):
    def __init__(self, stop_event: Event):
        super().__init__()
        self.stop_event = stop_event

    @devlog.log_on_error(trace_stack=True)
    def run(self) -> None:
        rule_manager = RuleManager.from_json(config.RULES)
        while not self.stop_event.is_set():
            logger.info(f"Checking RSS feeds...")
            try:
                for file_log, link in config.RSS_LIST.items():
                    file_log_path = os.path.join(f"{config.DATA_DIR['log']}/rss/", file_log)
                    log_file = helper.file.read_file(file_log_path)

                    links = parser(link, log_file)

                    with queue_lock:
                        add_to_queue(rule_manager, links, file_log_path)

                logger.info(f"All rss downloaded. Sleeping for {helper.duration_humanizer(config.SLEEP['rss_check'])}")
                self.stop_event.wait(config.SLEEP["rss_check"])
            except Exception as e:
                with open(config.LOG_FILE['rss'], "a+") as f:
                    f.write(f"{e}\n{traceback.format_exc()}")

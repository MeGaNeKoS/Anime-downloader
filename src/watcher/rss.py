import logging
import time

import devlog

from src import config, helper
from src import rss
from src.helper import duration_humanizer

logger = logging.getLogger(__name__)


@devlog.log_on_error(trace_stack=True)
def start_rss():
    while True:
        try:
            for file_log, link in config.RSS_LIST.items():
                file_log_path = f"{config.DATA_DIR['log']}/rss/{file_log}"
                log_file = helper.read_file(file_log_path, [])
                with open(f'{config.DATA_DIR["ignored"]}', 'r+') as input_file:
                    ignore = input_file.read().splitlines()

                links = rss.parser(link, log_file)
                rss.add_to_queue(links, ignore, file_log_path)

            logger.info(f"All rss downloaded. Sleeping for {duration_humanizer(config.SLEEP['rss_check'])}")
            time.sleep(config.SLEEP["rss_check"])
        except KeyboardInterrupt:
            break

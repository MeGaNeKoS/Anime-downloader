from src import helper
from src.filter.rule import RuleManager

from src.share_var import waiting_queue


def add_to_queue(manager: RuleManager, links: dict, file_log: str) -> None:
    for title, link in links.items():
        if title in file_log:
            continue

        anime = helper.parse(title, True)

        if manager.check(anime):
            waiting_queue.put(anime)

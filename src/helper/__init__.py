import functools

from deps.recognition import recognition
from src import config
from src.helper import file


def duration_humanizer(second: int):
    """
    Convert seconds to human-readable format
    """
    if not second:
        return "ETA: Unknown"

    msg = []
    if second >= 86400:
        msg.append(f"{second // 86400} day")
        second %= 86400
    if second >= 3600 and second != 0:
        msg.append(f"{second // 3600} hour(s)")
        second %= 3600
    if second >= 60 and second != 0:
        msg.append(f"{second // 60} minute(s)")
        second %= 60
    if second != 0:
        msg.append(f"{second} second(s)")

    if not msg:
        return "ETA: Unknown"

    return ' '.join(msg)


def legalize(filename: str):
    """
    Change forbidden printable character to full width version (utf-8)
    """
    if filename is None:
        return
    for illegal, escaped in config.LEGALIZE_CHARACTER.items():
        filename = filename.replace(illegal, escaped)
    return filename


def parse(file_name, track):
    if track:
        anime = recognition.track(file_name)
    else:
        anime, _ = recognition.parsing(file_name, False)
    if anime.get("anilist", 0) == 0:
        anime["anime_type"] = "unknown"

    return anime


# My own needs
LOWEST_PRIORITY = len(config.RELEASE_GROUP)


@functools.lru_cache(maxsize=128)
def get_priority(release_group: str, priority: int = None):
    try:
        return config.RELEASE_GROUP.index(release_group.lower())
    except ValueError:
        if priority is not None:
            return priority
        return LOWEST_PRIORITY


def fansub_priority(first_fansub, second_fansub) -> int:
    """
    Compare fansub priority

    :param first_fansub:
    :param second_fansub:
    :return:
    """
    if get_priority(first_fansub) < get_priority(second_fansub):
        return 1
    elif get_priority(first_fansub) == get_priority(second_fansub):
        return 0
    return -1


def should_download(anime, existing_file, uncensored) -> bool:
    other_uncensored = "uncensored" in str(existing_file.get("other", "")).lower()
    if uncensored and not other_uncensored:
        return True

    if not uncensored and other_uncensored:
        return False

    if fansub_priority(anime.get("release_group", ""),
                       existing_file.get("release_group", "")) == 1:
        return True

    if is_greater_than(anime.get("release_version", 0),
                       existing_file.get("release_version", 0)):
        return True

    return False


def is_greater_than(equation1, equation2):
    try:
        if isinstance(equation1, str):
            equation1 = int(equation1)
        if isinstance(equation2, str):
            equation2 = int(equation2)
    except ValueError:
        return False
    return equation1 > equation2

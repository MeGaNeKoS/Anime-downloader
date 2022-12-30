from deps.recognition import recognition
from src.helper import file

_legalize_char = {}


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
    for illegal, escaped in _legalize_char.items():
        filename = filename.replace(illegal, escaped)
    return filename


def parse(file_name, track):
    """
    Parse file name and return a dict of parsed result
    """
    if track:
        anime = recognition.track(file_name)
    else:
        anime, _ = recognition.parsing(file_name, False)
    if anime.get("anilist", 0) == 0:
        anime["anime_type"] = "unknown"

    return anime


def set_legalize_char(legalize_char: dict):
    global _legalize_char
    _legalize_char = legalize_char

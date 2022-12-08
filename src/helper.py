import functools
import os

from deps.recognition import recognition
from src import config
from src.share_var import log_file_lock

LOWEST_PRIORITY = len(config.RELEASE_GROUP)


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


@functools.lru_cache(maxsize=128)
def get_priority(release_group: str, priority: int = None):
    try:
        return config.RELEASE_GROUP.index(release_group.lower())
    except ValueError:
        if priority is not None:
            return priority
        return LOWEST_PRIORITY


def legalize(filename: str):
    """
    Change forbidden printable character to full width version (utf-8)
    """
    if filename is None:
        return
    for illegal, escaped in config.LEGALIZE_CHARACTER.items():
        filename = filename.replace(illegal, escaped)
    return filename


def get_destination(anime: dict, path: list):
    if anime.get("anime_title", "").lower() in ["meitantei conan"]:
        path.append(str((int(anime.get("episode_number", 0)) // 50) + 1))

    folders = list(filter(None, [anime.get("anime_year", None),
                                 anime.get("anime_title", None)])) + [folder for folder in path if folder]

    if anime.get("isExtras", False):
        folders.append("Extras")

    if isinstance(anime["anime_type"], list):
        anime_type = anime["anime_type"][0]
    else:
        anime_type = anime["anime_type"]

    anime_type = anime_type or "torrent"

    if not folders:
        return config.FOLDER_PATH["Anime"][anime_type.lower()]  # put it on torrent root file

    base_path = config.FOLDER_PATH["Anime"][anime_type.lower()]
    folders = [str(folder) for folder in folders]
    return os.path.join(base_path, *folders)


def discord_user_notif(msg, mention_owner=False):
    if mention_owner:
        msg = f"{config.OWNER} {msg}"
    with open(config.DISCORD_NOTIF, 'a+', encoding="utf-8") as out:
        out.write(f'{msg}\n')
    return None


def duration_humanizer(second: int):
    """
    Convert seconds to human readable format
    """
    if second is None:
        return "0 second"
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


def read_file(filename: str, default=None):
    """
    Open file with utf-8 encoding
    """
    try:
        with open(filename, 'r+') as input_file:
            log = input_file.read().splitlines()
    except FileNotFoundError:
        log = default
    return log


def add_to_log(filename: str, msg: str):
    """
    Add message to log file
    """
    with log_file_lock:
        log = read_file(filename, [])
        if msg not in log:
            log.insert(0, msg)
        del log[config.MAX_LOG:]
        with open(filename, 'w+') as output_file:
            output_file.write('\n'.join(log))


def is_exist(existing, newer, log_file, title) -> bool:
    if existing is None:
        return False
    # if already exist, check for the fansub priority
    priority = fansub_priority(existing["release_group"], newer["release_group"])
    if priority == 1:
        return True
    elif priority == 0:
        # both fansub has same priority
        # check for the version
        if is_greater_equal(existing.get('release_version', 0), newer.get('release_version', 0)):
            # the queued version is higher or same to the new one
            return True
    # replace the queue with the new one
    # I don't want to make a race condition to another process
    # better to remove then re add it again
    return False


def is_greater_equal(equation1, equation2):
    try:
        if isinstance(equation1, str):
            equation1 = int(equation1)
        if isinstance(equation2, str):
            equation2 = int(equation2)
    except ValueError:
        return False
    return equation1 >= equation2


def is_greater_than(equation1, equation2):
    try:
        if isinstance(equation1, str):
            equation1 = int(equation1)
        if isinstance(equation2, str):
            equation2 = int(equation2)
    except ValueError:
        return False
    return equation1 > equation2


def parse(file_name, track):
    if track:
        anime = recognition.track(file_name)
    else:
        anime, _ = recognition.parsing(file_name, False)
    if anime.get("anilist", 0) == 0:
        anime["anime_type"] = "torrent"

    return anime


def should_download(anime, existing_file, uncensored) -> bool:
    other_uncensored = "uncensored"  in str(existing_file.get("other", "")).lower()
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


def check_file(file_name, torrent_path, existing_root, track):
    anime = parse(file_name, track)

    if anime.get("anime_type", "torrent") == "torrent":
        # if the anime undetected, then we can't guarantee the anime title is correct or not
        anime.pop("anime_title", None)
        # replace os invalid characters
        torrent_path = [legalize(name) for name in torrent_path]
    else:
        # replace os invalid characters
        anime["anime_title"] = legalize(anime["anime_title"])
        torrent_path = []

    save_path = get_destination(anime, torrent_path)

    remove_list = []
    no_download = False
    uncensored = "uncensored" in str(anime.get("other", "")).lower()
    identifier = (f'{anime.get("anime_title")}_'
                  f'{anime.get("episode_number")}')

    file_list = existing_root.get(save_path, {})
    if file_list:
        existing_file = file_list.get(identifier, {})
        if existing_file:
            if existing_file.get("anime_type", "torrent") == "torrent":
                pass
            elif should_download(anime, existing_file, uncensored):
                print(f"Replacing {existing_file['anime_title']} ")
                remove_list.append(existing_file["file_name"])
                file_list[identifier] = anime
            else:
                no_download = True
        else:
            file_list[identifier] = anime

    elif anime.get("anime_type", "torrent") != "torrent":
        try:
            dir_files = os.listdir(save_path)
        except FileNotFoundError:
            dir_files = []

        for old_file in dir_files:
            if not os.path.isfile(os.path.join(save_path, old_file)):
                continue
            existing_file = parse(old_file, track)

            if existing_file.get("anime_type", "torrent") == "torrent":
                # if the anime undetected, then we can't guarantee the anime title is correct or not
                existing_file.pop("anime_title", None)
            else:
                # replace os invalid characters
                existing_file["anime_title"] = legalize(anime["anime_title"])

            existing_identifier = (f'{existing_file.get("anime_title")}_'
                                   f'{existing_file.get("episode_number")}')

            # duplicate_file = file_list.get(existing_identifier, {})
            # if not duplicate_file and existing_file.get("episode_number_alt"):
            #     existing_identifier = (f'{existing_file.get("anime_title")}_'
            #                            f'{existing_file.get("episode_number_alt")}')
            #     duplicate_file = file_list.get(existing_identifier, {})
            #
            # if duplicate_file:
            #     if should_download(existing_file, duplicate_file, uncensored):
            #         remove_list.append(duplicate_file["file_name"])
            #         file_list[identifier] = existing_file
            #     else:
            #         remove_list.append(existing_file["file_name"])
            #         continue

            if (anime.get("anime_title") == existing_file.get("anime_title")
                    and anime.get("episode_number") == existing_file.get("episode_number")):
                if should_download(anime, existing_file, uncensored):
                    print(f"replace {existing_file['file_name']} with {file_name}")
                    remove_list.append(old_file)
                    file_list[existing_identifier] = anime
                else:
                    file_list[existing_identifier] = existing_file
                    no_download = True
    return no_download, remove_list, save_path

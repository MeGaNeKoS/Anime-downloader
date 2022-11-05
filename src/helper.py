import functools

from src import config, gdrive
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
    if anime["anime_title"].lower() == "detective conan":
        path.append((int(anime.get("episode_number", 0))//50) + 1)
    folders = list(filter(None, [anime.get("anime_year", None),
                                 anime.get("anime_title", None)])) + [folder for folder in path if folder]
    if isinstance(anime["anime_type"], list):
        anime_type = anime["anime_type"][0]
    else:
        anime_type = anime["anime_type"]

    anime_type = anime_type or "torrent"
    if not folders:
        return config.FOLDER_LINK["Anime"][anime_type.lower()]  # put it on torrent root file

    key = get_create_folder(config.FOLDER_LINK["Anime"][anime_type.lower()],
                            folders)

    save_path = key[1]
    return save_path


def get_create_folder(root: dict, key: list):
    try:
        folder_id = root[key[0]]
    except (KeyError, TypeError, IndexError):
        if isinstance(root, str):
            folder_id = gdrive.service.create_folder(str(key[0]), root, True)
            root = {'id': root, key[0]: folder_id}
        else:
            folder_id = gdrive.service.create_folder(str(key[0]), root['id'], True)
            root.update({key[0]: folder_id})

    if len(key) > 1:
        new_info = get_create_folder(root[key[0]], key[1:])
        root[key[0]] = new_info[0]
        folder_id = new_info[1]
    if not type(folder_id) == str:
        folder_id = folder_id['id']
    return root, folder_id


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
        # the queued fansub has higher priority
        # so this title will not be downloaded
        # add to log if not exist
        add_to_log(log_file, title)
        return True
    elif priority == 0:
        # both fansub has same priority
        # check for the version
        if existing.get('release_version', 0) >= newer.get('release_version', 0):
            # the queued version is higher or same to the new one
            # so this title will not be downloaded
            # add to log if not exist
            add_to_log(log_file, title)
            return True
    # replace the queue with the new one
    # I don't want to make a race condition to another process
    # better to remove then re add it again
    return False

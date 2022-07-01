import functools
from src import config
from src import gdrive
LOWEST_PRIORITY = len(config.RELEASE_GROUP)


def fansub_priority(first_fansub, second_fansub, equality=True):
    if equality:
        return get_priority(first_fansub) <= get_priority(second_fansub)
    return get_priority(first_fansub) < get_priority(second_fansub)


@functools.lru_cache(maxsize=LOWEST_PRIORITY)
def get_priority(release_group, priority=None):
    try:
        return config.RELEASE_GROUP.index(release_group.lower())
    except ValueError:
        if priority:
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
    key = get_create_folder(config.FOLDER_LINK["Anime"][anime["anime_type"].lower()],
                            list(filter(None, [anime.get("anime_year"), anime.get("anime_title", None)])) +
                            [folder for folder in path if folder])
    config.FOLDER_LINK["Anime"][anime["anime_type"]] = key[0]
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
    with open(config.DISCORD_NOTIF, 'a+') as out:
        out.write(f'{msg}\n')
    return None
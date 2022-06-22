import functools
import config

LOWEST_PRIORITY = len(config.RELEASE_GROUP)


def fansub_priority(first_fansub, second_fansub, equality=True):
    if equality:
        return get_priority(first_fansub) <= get_priority(second_fansub)
    return get_priority(first_fansub) < get_priority(second_fansub)


@functools.lru_cache(maxsize=LOWEST_PRIORITY)
def get_priority(release_group, priority=None):
    try:
        return config.RELEASE_GROUP.index(release_group)
    except ValueError:
        if priority:
            return priority
        return LOWEST_PRIORITY

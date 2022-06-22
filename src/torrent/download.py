downloads = {}


def remove(anime_id):
    # cancel the download, delete the local files,
    # and add the anime to the log file

    downloads.pop(anime_id, None)


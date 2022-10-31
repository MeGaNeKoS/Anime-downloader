from deps.recognition import recognition
from src import config, helper, database
from src.share_var import queue_lock, queue, downloads, download_lock
from src.watcher.download import remove_torrent


def add_to_queue(links, ignore, file_log):
    for title, link in links.items():
        if "." in title[:-6:-1]:
            # we found the file extensions in the title
            anime = recognition.track(title)
        else:
            # force add an extensions since the title from torrent usually doesn't include extensions
            anime = recognition.track(title + ".mkv")
            anime["file_name"] = title

        # skip if in ignore list,
        # skip if the release not from watched release group
        if (anime["anime_title"].lower() in ignore or
                anime.get("release_group", "").lower() not in config.RELEASE_GROUP):
            continue

        # get the download link
        for value in link:
            if value is None:
                continue
            anime['link'] = value
            break

        anime['log_file'] = file_log
        category = str(anime["anilist"]) + str(anime.get("episode_number", 0))
        uncensored = "uncensored" in str(anime.get("other", "")).lower()
        with queue_lock:
            if anime.get("anime_type", "torrent").lower() == "torrent" or anime.get("anilist", 0) == 0:
                # this anime can't be detected :( put to torrent folder instead.
                queue[title] = anime
                continue

            # check if the anime already in queue list
            queue_anime = queue.get(category)
            if helper.is_exist(queue_anime, anime, file_log, title):
                continue

            with download_lock:
                queue_anime = downloads.get(category, None)
                if queue_anime:
                    if helper.is_exist(queue_anime, anime, file_log, title):
                        continue
                    else:
                        if not remove_torrent(queue_anime):
                            # the file already in upload/finished state
                            helper.add_to_log(file_log, title)
                            continue

        # check the fansub preference from the database
        if from_db := database.db.select("preference", {"anime_id": anime["anilist"]}):
            if uncensored and not from_db[0]["uncensored"]:
                from_db[0]["release_group"] = anime["release_group"]
                from_db[0]["uncensored"] = True
                database.db.insert("preference", from_db[0])
            elif not uncensored and from_db[0]["uncensored"]:
                continue
            else:
                priority = helper.fansub_priority(from_db[0]["release_group"], anime["release_group"])
                if priority == 1:
                    # thus we skip this one and wait for that fansub
                    helper.add_to_log(file_log, title)
                    continue
                elif priority == 0:
                    pass
                else:
                    # this anime fansub has higher priority,
                    # so we update the fansub preference with the new one.
                    from_db[0]["release_group"] = anime["release_group"]
                    database.db.insert("preference", from_db[0])
        else:
            # if the preference is empty,
            # then create new preference entry
            to_db = {
                "anime_name": anime["anime_title"],
                "anime_id": anime["anilist"],
                "release_group": anime["release_group"],
                "uncensored": uncensored
            }
            database.db.insert("preference", to_db)

        with queue_lock:
            # add to the queue list
            queue[category] = anime

import feedparser


queue = []

# parse the RSS feed
def rss(feed_link, release_group, data_dir):
    log_file = f'{data_dir}/log/{feed_link.partition("q=")[2]}.txt'
    try:
        with open(log_file, 'r') as f:
            log = f.read().splitlines()
    except FileNotFoundError:
        with open(log_file, 'w+') as f:
            pass
        log = []

    rss_parser = feedparser.parse(feed_link)

    for torrent in rss_parser.entries:
        with open(f'{data_dir}/ignore.txt', 'r') as f:
            ignore = f.read().splitlines()

        # skip the anime if already downloaded or in ignore list
        if torrent['title'] in log or any(name.lower() in torrent['title'].lower() for name in ignore):
            continue
        # get the magnet link
        magnet = "magnet" + str(torrent["summary_detail"].values()).split('href="magnet')[1]
        magnet = magnet.split('">')[0]
        magnet = magnet.replace("&amp;", "&")

        # check if the title contains the release group
        if torrent['title'][0] == "[" and torrent['title'][1:].lower().startswith(tuple(release_group)):
            if torrent.summary.endswith(" file(s)</a>"):
                status = download(magnet, False)
            else:
                status = download(magnet, True)

            if status:
                log.insert(0, torrent['title'])
                del log[100:]  # only save last 100 item
                with open(log_file, 'w+') as f:
                    for magnet_link in log:
                        f.write("%s\n" % magnet_link)

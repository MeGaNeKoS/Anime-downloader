import sys
import traceback
import logging

from src import AnimeDownloader

if __name__ == '__main__':
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    file_handler = logging.FileHandler('app.log', encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO, handlers=[file_handler])

    try:
        AnimeDownloader.main()
    except KeyboardInterrupt:
        print("Exit using ctrl+c")
        sys.exit(0)
    except Exception as e:
        with open("torrent.log", "a+") as f:
            f.write(f"{e}\n{traceback.format_exc()}")

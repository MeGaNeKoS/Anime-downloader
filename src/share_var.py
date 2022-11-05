import threading

from src import config

queue = {}
downloads = {}
main_lock = threading.RLock()
gdrive_lock = threading.RLock()
log_file_lock = threading.RLock()
queue_lock = main_lock
download_lock = main_lock
parser_lock = threading.RLock()

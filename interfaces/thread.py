import ctypes
import logging
import time
from threading import Thread, Event, RLock
from typing import List

from interfaces.interface import Torrent
from src.exception.thread import ForceRestartException


class BaseThread(Thread):
    module_logger = logging.getLogger(__name__)

    def __init__(self, stop_event: Event, sleep_event: Event, queue_lock: RLock, waiting_queue: list, *,
                 logger: dict,
                 sleep_time: int,
                 traceback_file: str,
                 daemon: bool = True):
        super().__init__(daemon=daemon)
        self._lock = RLock()
        self.stop_event = stop_event
        self._sleep_event = sleep_event
        self.queue_lock = queue_lock
        self.waiting_queue: List[Torrent] = waiting_queue
        self.exception_traceback = traceback_file

        self._sleep_time: int = sleep_time

        self.logger = logging.getLogger(f"{self.__module__}[{logger['name']}]")

        if logger.get("level"):
            try:
                self.logger.setLevel(logger["level"])
            except (ValueError, TypeError) as e:
                self.module_logger.warning(f"Fail to set logger level for {logger['name']}: {e}."
                                           f"Using root level instead.")

        # set up the file log handler for this logger
        default_formatter = logger.get("formatter")
        if logger.get("fileHandler"):
            failed = False
            for file_name, msg_format in logger["fileHandler"]:
                try:
                    file_handler = logging.FileHandler(file_name, encoding="utf-8")
                except (FileNotFoundError, PermissionError, UnicodeEncodeError) as e:
                    self.module_logger.error(f"Fail to create file handler for {logger['name']}: {e}")
                    failed = True
                    continue
                except Exception as e:
                    self.module_logger.error(f"Unknown error file handler for {logger['name']}: {e}")
                    failed = True
                    continue

                failed = not self._set_handler(self.logger, file_handler, [msg_format, default_formatter])

            if failed:
                logger.setdefault("streamHandler", "%(asctime)s %(levelname)s %(message)s")

        # set up the stream handler for this logger
        if logger.get("streamHandler"):
            stream_handler = logging.StreamHandler()
            self._set_handler(self.logger, stream_handler, [logger["streamHandler"], default_formatter])

    @property
    def sleep_time(self):
        return self._sleep_time

    @sleep_time.setter
    def sleep_time(self, sleep_time: int):
        with self._lock:
            self._sleep_time = sleep_time
            self._sleep_event.set()
            time.sleep(0.1)
            self._sleep_event.clear()

    @classmethod
    def _set_handler(cls, logger_obj: logging.Logger, handler: logging.Handler, format_list: list) -> bool:
        if not format_list:
            logger_obj.addHandler(handler)
            return True

        success = False
        for msg_formatter in format_list:
            if not msg_formatter:
                continue

            try:
                formatter = logging.Formatter(msg_formatter)
                handler.setFormatter(formatter)
                success = True
                break
            except (ValueError, TypeError) as e:
                cls.module_logger.warning(
                    f"Fail to set formatter for {logger_obj.name}: {e}. Using root formatter instead.")
            except Exception as e:
                cls.module_logger.error(f"Unknown error formatter for {logger_obj.name}: {e}")

        logger_obj.addHandler(handler)
        return success

    def force_restart(self):
        self.raise_exception(ForceRestartException)

    def get_id(self):
        return self.ident

    def raise_exception(self, exception=None):
        if exception is None:
            exception = KeyboardInterrupt

        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(exception))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            self.module_logger.error(f'Exception raise failure for thread {thread_id}')

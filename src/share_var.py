import sys
from threading import RLock


class ThreadDict(dict):
    """
    This class is means to be used on development only to prevent the dictionary from being
    accessed without the lock acquired. As such, it is not meant to be used in production.


    On production, Using the built-in dict class is recommended.
    """

    def __init__(self, thread_lock: RLock):
        super().__init__()
        self.thread_lock: RLock = thread_lock

    def _verify_lock(self):
        # not exists in pyi files but exists in py files
        if not self.thread_lock._is_owned():
            print("Failed to acquire lock")
            raise RuntimeError("ThreadDict must be accessed with the lock acquired")

    def __contains__(self, key):
        self._verify_lock()
        return super().__contains__(key)

    def __delitem__(self, key):
        self._verify_lock()
        super().__delitem__(key)

    def __getitem__(self, key):
        self._verify_lock()
        return super().__getitem__(key)

    def __iter__(self):
        self._verify_lock()
        return super().__iter__()

    def __len__(self):
        self._verify_lock()
        return super().__len__()

    def __repr__(self):
        self._verify_lock()
        return super().__repr__()

    def __setitem__(self, key, value):
        self._verify_lock()
        super().__setitem__(key, value)

    def __str__(self):
        self._verify_lock()
        return super().__str__()

    if sys.version_info >= (3, 8):
        def __reversed__(self):
            self._verify_lock()
            return super().__reversed__()

    if sys.version_info >= (3, 9):
        def __or__(self, *args, **kwargs):
            self._verify_lock()
            return super().__or__(*args, **kwargs)

        def __ror__(self, *args, **kwargs):
            self._verify_lock()
            return super().__ror__(*args, **kwargs)

        def __ior__(self, *args, **kwargs):
            self._verify_lock()
            return super().__ior__(*args, **kwargs)


class ThreadList(list):
    """
    This class is means to be used on development only to prevent the dictionary from being
    accessed without the lock acquired. As such, it is not meant to be used in production.

    On production, Using the built-in list class is recommended.
    """

    def __init__(self, thread_lock: RLock):
        super().__init__()
        self.thread_lock: RLock = thread_lock

    def _verify_lock(self):
        # not exists in pyi files but exists in py files
        if not self.thread_lock._is_owned():
            print("Failed to acquire lock")
            raise RuntimeError("ThreadList must be accessed with the lock acquired")

    def __add__(self, other):
        self._verify_lock()
        return super().__add__(other)

    def __contains__(self, key):
        self._verify_lock()
        return super().__contains__(key)

    def __delitem__(self, key):
        self._verify_lock()
        super().__delitem__(key)

    def __eq__(self, other):
        self._verify_lock()
        return super().__eq__(other)

    def __ge__(self, other):
        self._verify_lock()
        return super().__ge__(other)

    def __getattribute__(self, item):
        if str(item) not in ['_verify_lock', 'thread_lock']:
            self._verify_lock()
        return super().__getattribute__(item)

    def __getitem__(self, key):
        self._verify_lock()
        return super().__getitem__(key)

    def __gt__(self, other):
        self._verify_lock()
        return super().__gt__(other)

    def __iadd__(self, other):
        self._verify_lock()
        return super().__iadd__(other)

    def __imul__(self, other):
        self._verify_lock()
        return super().__imul__(other)

    def __iter__(self):
        self._verify_lock()
        return super().__iter__()

    def __le__(self, other):
        self._verify_lock()
        return super().__le__(other)

    def __len__(self):
        self._verify_lock()
        return super().__len__()

    def __lt__(self, other):
        self._verify_lock()
        return super().__lt__(other)

    def __mul__(self, other):
        self._verify_lock()
        return super().__mul__(other)

    def __ne__(self, other):
        self._verify_lock()
        return super().__ne__(other)

    def __repr__(self):
        self._verify_lock()
        return super().__repr__()

    def __reversed__(self):
        self._verify_lock()
        return super().__reversed__()

    def __rmul__(self, other):
        self._verify_lock()
        return super().__rmul__(other)

    def __setitem__(self, key, value):
        self._verify_lock()
        super().__setitem__(key, value)

    def __sizeof__(self):
        self._verify_lock()
        return super().__sizeof__()

    def __str__(self):
        self._verify_lock()
        return super().__str__()


# Any thread requesting to access the following variables must acquire this lock first
queue_lock = RLock()

waiting_queue = ThreadList(queue_lock)  # Used in RSS, Download Thread

# For general use, use the following lock.
# Avoid using main_lock -> queue_lock -> main_lock as it will cause deadlock
main_lock = RLock()

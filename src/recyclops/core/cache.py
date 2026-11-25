"""A small thread-safe LRU cache with expiry: repeated requests don't repeat AI or data-source calls."""

import time
from collections import OrderedDict
from collections.abc import Callable
from threading import Lock


class TTLCache[T]:
    def __init__(self, max_entries: int = 256, ttl_seconds: float = 3600,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._clock = clock  # seconds; tests pass a fake one to move time on
        self._items: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> T | None:
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            stored_at, value = entry
            if self._clock() - stored_at > self.ttl_seconds:
                del self._items[key]
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._items[key] = (self._clock(), value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_entries:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

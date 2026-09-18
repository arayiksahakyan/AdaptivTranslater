import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)
CacheKey = tuple[str, str, str]


class TranslationCache:
    """Worker-owned bounded LRU; no persistence and no cross-thread sharing."""

    def __init__(self, capacity: int = 256) -> None:
        if capacity <= 0:
            raise ValueError("Cache capacity must be positive.")
        self.capacity = capacity
        self._entries: OrderedDict[CacheKey, str] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: CacheKey) -> str | None:
        if key not in self._entries:
            self.misses += 1
            return None
        self.hits += 1
        self._entries.move_to_end(key)
        logger.debug("Translation cache hit; hits=%d misses=%d", self.hits, self.misses)
        return self._entries[key]

    def put(self, key: CacheKey, translated_text: str) -> None:
        self._entries[key] = translated_text
        self._entries.move_to_end(key)
        while len(self._entries) > self.capacity:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

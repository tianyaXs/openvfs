"""默认内存 Store。"""

from __future__ import annotations

from typing import Any

from openvfs.stores.key_value_adapter import KeyValueStoreAdapter


class MemoryStore(KeyValueStoreAdapter):
    """默认内存 Store，对外隐藏 py-key-value-aio 的 SimpleStore 命名。"""

    def __init__(self, max_entries: int | None = None, prefix: str = "") -> None:
        from key_value.aio.stores.simple import SimpleStore

        super().__init__(SimpleStore(max_entries=max_entries), prefix=prefix)

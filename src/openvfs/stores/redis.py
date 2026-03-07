"""Redis Store。"""

from __future__ import annotations

from typing import Any

from openvfs.stores.key_value_adapter import KeyValueStoreAdapter


class RedisStore(KeyValueStoreAdapter):
    """基于 py-key-value-aio RedisStore 的薄封装。"""

    def __init__(self, prefix: str = "", **kwargs: Any) -> None:
        from key_value.aio.stores.redis import RedisStore as _RedisStore

        super().__init__(_RedisStore(**kwargs), prefix=prefix)

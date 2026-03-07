"""S3 兼容 Store。"""

from __future__ import annotations

from typing import Any

from openvfs.stores.key_value_adapter import KeyValueStoreAdapter


class S3Store(KeyValueStoreAdapter):
    """基于 py-key-value-aio S3Store 的薄封装。"""

    def __init__(self, prefix: str = "", **kwargs: Any) -> None:
        from key_value.aio.stores.s3 import S3Store as _S3Store

        super().__init__(_S3Store(**kwargs), prefix=prefix)

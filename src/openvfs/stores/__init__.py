"""OpenVFS stores。"""

from __future__ import annotations

from typing import Any

from openvfs.stores.base import BaseStore
from openvfs.stores.key_value_adapter import KeyValueStoreAdapter
from openvfs.stores.memory import MemoryStore
from openvfs.stores.redis import RedisStore
from openvfs.stores.s3 import S3Store

__all__ = [
    "BaseStore",
    "KeyValueStoreAdapter",
    "MemoryStore",
    "RedisStore",
    "S3Store",
    "adapt_store",
    "create_default_store",
]


def adapt_store(store: Any) -> BaseStore:
    if isinstance(store, BaseStore):
        return store
    return KeyValueStoreAdapter(store)


def create_default_store() -> BaseStore:
    return MemoryStore()

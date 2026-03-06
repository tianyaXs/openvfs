"""兼容层：请改用 openvfs.stores.base。"""

from openvfs.stores.base import BaseStore

StorageBackend = BaseStore

__all__ = ["BaseStore", "StorageBackend"]

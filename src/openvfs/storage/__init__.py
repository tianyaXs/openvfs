"""兼容层：请改用 openvfs.stores。"""

from openvfs.stores import BaseStore, TOSStore

StorageBackend = BaseStore
TOSStorage = TOSStore

__all__ = ["BaseStore", "StorageBackend", "TOSStore", "TOSStorage"]

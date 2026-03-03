"""存储层"""

from openvfs.storage.base import StorageBackend
from openvfs.storage.tos import TOSStorage

__all__ = ["StorageBackend", "TOSStorage"]

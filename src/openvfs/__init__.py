"""OpenVFS - Agent 专用 Markdown 文件系统"""

from openvfs.chain import DocumentBuilder
from openvfs.client import OpenVFS
from openvfs.exceptions import (
    InvalidURIError,
    MindMarkError,
    NotFoundError,
    StorageError,
)
from openvfs.stores import BaseStore, TOSStore
from openvfs.vfs import VfsDirectory, VfsDocument

__all__ = [
    "OpenVFS",
    "DocumentBuilder",
    "VfsDocument",
    "VfsDirectory",
    "BaseStore",
    "TOSStore",
    "InvalidURIError",
    "MindMarkError",
    "NotFoundError",
    "StorageError",
]
__version__ = "0.1.3"

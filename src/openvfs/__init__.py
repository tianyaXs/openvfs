"""OpenVFS - Agent 专用 Markdown 文件系统中间件。"""

from __future__ import annotations

from typing import Any

from openvfs.exceptions import InvalidURIError, MindMarkError, NotFoundError, StorageError
from openvfs.stores import BaseStore, KeyValueStoreAdapter, MemoryStore, RedisStore, S3Store
from openvfs.vfs import Cell, DocumentBuilder, MarkdownDocument, OpenVFS, OpenVfs, VfsDirectory, VfsFile


__all__ = [
    "OpenVfs",
    "OpenVFS",
    "DocumentBuilder",
    "VfsFile",
    "MarkdownDocument",
    "Cell",
    "VfsDirectory",
    "BaseStore",
    "KeyValueStoreAdapter",
    "MemoryStore",
    "RedisStore",
    "S3Store",
    "InvalidURIError",
    "MindMarkError",
    "NotFoundError",
    "StorageError",
]
__version__ = "0.1.3"

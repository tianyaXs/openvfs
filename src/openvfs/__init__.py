"""OpenVFS - Agent 专用 Markdown 文件系统"""

from openvfs.client import MindMarkClient
from openvfs.chain import DocChain
from openvfs.exceptions import (
    InvalidURIError,
    MindMarkError,
    NotFoundError,
    StorageError,
)

__all__ = [
    "MindMarkClient",
    "DocChain",
    "InvalidURIError",
    "MindMarkError",
    "NotFoundError",
    "StorageError",
]
__version__ = "0.1.0"

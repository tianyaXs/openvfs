"""OpenVFS - 虚拟文件系统

使用方式：import openvfs 后直接基于 openvfs 调用。

示例:
    import openvfs
    vfs = openvfs.Client()
    path = vfs.path("resources/my_project")
    path.create_folder("docs")
    path.create_file("readme.md", "# Hello")
    file = path.find_file("readme.md")
    path.update_file("readme.md", "新内容")
    items = path.list()
    path.delete("readme.md")
"""

from openvfs.client import Client, Path
from openvfs.document import Cell, VFSFile
from openvfs.folder import VFSFolder
from openvfs.exceptions import (
    ConcurrentModifyError,
    InvalidURIError,
    NotFoundError,
    OpenVFSError,
    StorageError,
)

__all__ = [
    "Client",
    "Cell",
    "Path",
    "VFSFile",
    "VFSFolder",
    "ConcurrentModifyError",
    "InvalidURIError",
    "NotFoundError",
    "OpenVFSError",
    "StorageError",
]
__version__ = "0.1.2"

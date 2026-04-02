"""VFS 领域对象。"""

from openvfs.vfs.builder import DocumentBuilder
from openvfs.vfs.directory import VfsDirectory
from openvfs.vfs.document import Cell, MarkdownDocument
from openvfs.vfs.facade import OpenVFS, OpenVfs
from openvfs.vfs.file import VfsFile

__all__ = [
    "OpenVfs",
    "OpenVFS",
    "DocumentBuilder",
    "VfsFile",
    "MarkdownDocument",
    "Cell",
    "VfsDirectory",
]

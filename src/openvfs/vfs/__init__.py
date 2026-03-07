"""VFS 领域对象。"""

from openvfs.vfs.builder import DocumentBuilder
from openvfs.vfs.directory import VfsDirectory
from openvfs.vfs.document import VfsDocument
from openvfs.vfs.facade import OpenVFS, OpenVfs

__all__ = ["OpenVfs", "OpenVFS", "DocumentBuilder", "VfsDocument", "VfsDirectory"]

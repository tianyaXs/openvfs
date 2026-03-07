"""OpenVFS 初始化入口。"""

from __future__ import annotations

from typing import Any

from openvfs.stores import BaseStore
from openvfs.vfs.facade import OpenVfs


def init_vfs(store: BaseStore | Any | None = None, namespaces: list[str] | None = None) -> OpenVfs:
    """初始化 VFS。默认使用 MemoryStore。"""
    return OpenVfs.init_vfs(store=store, namespaces=namespaces)

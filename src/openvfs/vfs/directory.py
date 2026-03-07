"""虚拟文件系统中的目录对象。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openvfs.vfs.facade import OpenVFS


class VfsDirectory:
    """虚拟文件系统中的逻辑目录对象。"""

    def __init__(self, client: OpenVFS, uri: str) -> None:
        self._client = client
        self.uri = uri

    def list(self) -> list[str]:
        path = self._client._uri_path(self.uri)
        if path and not path.endswith("/"):
            path += "/"
        return self._client._store.list_keys(path or "")

    def tree(self, max_depth: int = -1) -> str:
        lines: list[str] = []
        base = self.uri.rstrip("/") or "openvfs://"

        def _walk(uri: str, indent: str, depth: int) -> None:
            if max_depth >= 0 and depth > max_depth:
                return
            items = VfsDirectory(self._client, uri).list()
            dirs = sorted([item for item in items if item.endswith("/")])
            files = sorted([item for item in items if not item.endswith("/")])
            all_items = dirs + files
            for index, name in enumerate(all_items):
                is_last = index == len(all_items) - 1
                branch = "└── " if is_last else "├── "
                lines.append(f"{indent}{branch}{name}")
                if name.endswith("/"):
                    next_indent = indent + ("    " if is_last else "│   ")
                    parent = uri.rstrip("/")
                    child_uri = f"{parent}/{name}"
                    _walk(child_uri, next_indent, depth + 1)

        lines.append(base)
        _walk(base, "", 0)
        return "\n".join(lines)

"""OpenVFS 文件夹对象。"""

from __future__ import annotations

from typing import Any


class VFSFolder:
    """虚拟文件夹对象。"""

    def __init__(self, client: Any, uri: str):
        self._client = client
        self.uri = uri.rstrip("/")

    def _child_uri(self, name: str) -> str:
        name = name.strip().strip("/")
        if not name:
            raise ValueError("name cannot be empty")
        return f"{self.uri}/{name}"

    def create_file(self, name: str, content: str) -> None:
        self._client.create_file(self._child_uri(name), content)

    def create_folder(self, name: str) -> None:
        self._client.create_folder(self._child_uri(name))

    def find_file(self, name: str):
        return self._client.find_file(self._child_uri(name))

    def find_folder(self, name: str):
        return self._client.find_folder(self._child_uri(name))

    def exists_file(self, name: str) -> bool:
        return self._client.exists_file(self._child_uri(name))

    def exists_folder(self, name: str) -> bool:
        return self._client.exists_folder(self._child_uri(name))

    def list(self) -> list[str]:
        return self._client.list(self.uri)

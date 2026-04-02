from __future__ import annotations

from typing import TYPE_CHECKING

from openvfs.vfs.document import MarkdownDocument

if TYPE_CHECKING:
    from openvfs.vfs.facade import OpenVFS


class VfsFile:
    def __init__(self, client: OpenVFS, uri: str) -> None:
        self._client = client
        self.uri = uri

    def create(self, content: str) -> None:
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._store.put(key, content)

    def read(self) -> str:
        return self.as_markdown().read()

    def write(self, content: str) -> None:
        self.as_markdown().write(content)

    def delete(self) -> None:
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._store.delete(key)

    def exists(self) -> bool:
        key = self._client._resolve_key(self.uri, for_file=True)
        return self._client._store.exists(key)

    def as_markdown(self) -> MarkdownDocument:
        return MarkdownDocument(self._client, self.uri)

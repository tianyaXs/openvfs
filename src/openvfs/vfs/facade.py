"""OpenVFS 门面对象。"""

from __future__ import annotations

from typing import Any

from openvfs.stores import BaseStore, MemoryStore, adapt_store, create_default_store
from openvfs.vfs.builder import DocumentBuilder
from openvfs.vfs.config import load_config
from openvfs.vfs.directory import VfsDirectory
from openvfs.vfs.document import VfsDocument
from openvfs.vfs.uri import ensure_md, is_file_uri, parse, to_object_key


class OpenVfs:
    """OpenVFS 门面对象，负责路径解析和 VFS 对象创建。"""

    def __init__(
        self,
        store: BaseStore | Any | None = None,
        namespaces: list[str] | None = None,
    ) -> None:
        cfg = load_config()
        self._store = adapt_store(store) if store is not None else create_default_store()
        self._namespaces = namespaces if namespaces is not None else cfg.get("namespaces")

    @classmethod
    def init_vfs(
        cls,
        store: BaseStore | Any | None = None,
        namespaces: list[str] | None = None,
    ) -> OpenVfs:
        """初始化 VFS。默认使用 MemoryStore。"""
        return cls(store=store, namespaces=namespaces)

    @classmethod
    def default_store(cls) -> MemoryStore:
        """返回默认内存 Store。"""
        return MemoryStore()

    def cd_path(self, *parts: str) -> DocumentBuilder:
        return DocumentBuilder(self, list(parts))

    def create_folder(self, uri: str) -> None:
        normalized = self._uri_path(uri).rstrip("/")
        self._store.create_folder(normalized)

    def mkdir(self, uri: str) -> None:
        self.create_folder(uri)

    def document(self, uri: str) -> VfsDocument:
        return VfsDocument(self, uri)

    def directory(self, uri: str) -> VfsDirectory:
        return VfsDirectory(self, uri)

    def _resolve_key(self, uri: str, for_file: bool = False) -> str:
        _, full_path = parse(uri, self._namespaces)
        if for_file and not is_file_uri(full_path):
            full_path = ensure_md(full_path)
        return to_object_key(full_path, self._store._prefix)

    def _uri_path(self, uri: str) -> str:
        _, full_path = parse(uri, self._namespaces)
        return full_path

    def create(self, uri: str, content: str) -> None:
        self.document(uri).create(content)

    def read(self, uri: str) -> str:
        return self.document(uri).read()

    def update(self, uri: str, content: str) -> None:
        self.document(uri).write(content)

    def delete(self, uri: str) -> None:
        self.document(uri).delete()

    def exists(self, uri: str) -> bool:
        return self.document(uri).exists()

    def list(self, uri: str) -> list[str]:
        return self.directory(uri).list()

    def tree(self, uri: str, max_depth: int = -1) -> str:
        return self.directory(uri).tree(max_depth=max_depth)

    def add_heading(self, uri: str, text: str, level: int = 1, attrs: dict[str, str] | None = None) -> None:
        self.document(uri).add_heading(text, level=level, attrs=attrs)

    def add_heading_with_content(
        self,
        uri: str,
        text: str,
        section_content: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        self.document(uri).add_heading_with_content(text, section_content, level=level, attrs=attrs)

    def append(self, uri: str, content: str) -> None:
        self.document(uri).append(content)

    def insert_under_heading(self, uri: str, heading_text: str, content: str) -> None:
        self.document(uri).insert_under_heading(heading_text, content)

    def replace_heading_content(self, uri: str, heading_text: str, new_content: str) -> None:
        self.document(uri).replace_heading_content(heading_text, new_content)

    def get_headings(self, uri: str) -> list[dict[str, Any]]:
        return self.document(uri).get_headings()

    def get_section(self, uri: str, heading_text: str) -> str:
        return self.document(uri).get_section(heading_text)

    def set_section_by_field(
        self,
        uri: str,
        field: str,
        value: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        self.document(uri).set_section_by_field(field, value, heading_text, section_content, level=level)

    def set_section_by_id(
        self,
        uri: str,
        section_id: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        self.document(uri).set_section_by_id(section_id, heading_text, section_content, level=level)

    def get_section_by_field(self, uri: str, field: str, value: str) -> str:
        return self.document(uri).get_section_by_field(field, value)

    def get_section_by_id(self, uri: str, section_id: str) -> str:
        return self.document(uri).get_section_by_id(section_id)

    def get_section_by_ref(self, uri: str, ref: str | dict[str, str]) -> str:
        return self.document(uri).get_section_by_ref(ref)

    def get_heading_with_context(
        self,
        uri: str,
        heading_ref: str | dict[str, str],
        before: int = 0,
        after: int = 0,
        include_heading: bool = True,
    ) -> str:
        return self.document(uri).get_heading_with_context(heading_ref, before=before, after=after, include_heading=include_heading)

    def list_sections_by_field(self, uri: str, field: str | None = None) -> list[dict[str, Any]]:
        return self.document(uri).list_sections_by_field(field)


OpenVFS = OpenVfs

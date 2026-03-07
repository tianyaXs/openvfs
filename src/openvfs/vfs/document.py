"""虚拟文件系统中的文档对象。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openvfs.exceptions import NotFoundError
from openvfs.filetypes.md.editor import (
    add_heading as _add_heading,
    add_heading_with_content as _add_heading_with_content,
    append_content as _append_content,
    get_heading_with_context as _get_heading_with_context,
    get_section as _get_section,
    get_section_by_field as _get_section_by_field,
    get_section_by_id as _get_section_by_id,
    get_section_by_ref as _get_section_by_ref,
    insert_under_heading as _insert_under_heading,
    list_sections_by_field as _list_sections_by_field,
    replace_heading_content as _replace_heading_content,
    set_section_by_field as _set_section_by_field,
)
from openvfs.filetypes.md.parser import get_headings as _get_headings

if TYPE_CHECKING:
    from openvfs.vfs.facade import OpenVFS


class VfsDocument:
    """虚拟文件系统中的 Markdown 文档对象。"""

    def __init__(self, client: OpenVFS, uri: str) -> None:
        self._client = client
        self.uri = uri

    def create(self, content: str) -> None:
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._store.put(key, content)

    def read(self) -> str:
        key = self._client._resolve_key(self.uri, for_file=True)
        try:
            data = self._client._store.get(key)
            return data.decode("utf-8")
        except NotFoundError:
            raise NotFoundError(self.uri)

    def write(self, content: str) -> None:
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._store.put(key, content)

    def delete(self) -> None:
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._store.delete(key)

    def exists(self) -> bool:
        key = self._client._resolve_key(self.uri, for_file=True)
        return self._client._store.exists(key)

    def add_heading(self, text: str, level: int = 1, attrs: dict[str, str] | None = None) -> None:
        self.write(_add_heading(self.read(), text, level, attrs))

    def add_heading_with_content(
        self,
        text: str,
        section_content: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        self.write(_add_heading_with_content(self.read(), text, section_content, level, attrs))

    def append(self, content: str) -> None:
        self.write(_append_content(self.read(), content))

    def insert_under_heading(self, heading_text: str, content: str) -> None:
        self.write(_insert_under_heading(self.read(), heading_text, content))

    def replace_heading_content(self, heading_text: str, new_content: str) -> None:
        self.write(_replace_heading_content(self.read(), heading_text, new_content))

    def get_headings(self) -> list[dict[str, Any]]:
        headings = _get_headings(self.read())
        return [
            {
                "level": heading.level,
                "text": heading.text,
                "line_start": heading.line_start,
                "attrs": getattr(heading, "attrs", {}),
            }
            for heading in headings
        ]

    def get_section(self, heading_text: str) -> str:
        return _get_section(self.read(), heading_text)

    def set_section_by_field(
        self,
        field: str,
        value: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        self.write(_set_section_by_field(self.read(), field, value, heading_text, section_content, level))

    def set_section_by_id(
        self,
        section_id: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        self.set_section_by_field("id", section_id, heading_text, section_content, level)

    def get_section_by_field(self, field: str, value: str) -> str:
        return _get_section_by_field(self.read(), field, value)

    def get_section_by_id(self, section_id: str) -> str:
        return _get_section_by_id(self.read(), section_id)

    def get_section_by_ref(self, ref: str | dict[str, str]) -> str:
        return _get_section_by_ref(self.read(), ref)

    def get_heading_with_context(
        self,
        heading_ref: str | dict[str, str],
        before: int = 0,
        after: int = 0,
        include_heading: bool = True,
    ) -> str:
        return _get_heading_with_context(self.read(), heading_ref, before, after, include_heading)

    def list_sections_by_field(self, field: str | None = None) -> list[dict[str, Any]]:
        return _list_sections_by_field(self.read(), field)

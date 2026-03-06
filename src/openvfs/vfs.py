"""虚拟文件系统对象。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openvfs.exceptions import NotFoundError
from openvfs.markdown.editor import (
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
from openvfs.markdown.parser import get_headings as _get_headings

if TYPE_CHECKING:
    from openvfs.client import OpenVFS


class VfsDocument:
    """虚拟文件系统中的 Markdown 文档对象。"""

    def __init__(self, client: OpenVFS, uri: str) -> None:
        self._client = client
        self.uri = uri

    def create(self, content: str) -> None:
        """创建文档。"""
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._storage.put(key, content)

    def read(self) -> str:
        """读取文档内容。"""
        key = self._client._resolve_key(self.uri, for_file=True)
        try:
            data = self._client._storage.get(key)
            return data.decode("utf-8")
        except NotFoundError:
            raise NotFoundError(self.uri)

    def write(self, content: str) -> None:
        """覆盖写入文档。"""
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._storage.put(key, content)

    def delete(self) -> None:
        """删除文档。"""
        key = self._client._resolve_key(self.uri, for_file=True)
        self._client._storage.delete(key)

    def exists(self) -> bool:
        """判断文档是否存在。"""
        key = self._client._resolve_key(self.uri, for_file=True)
        return self._client._storage.exists(key)

    def add_heading(
        self,
        text: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        """在文档末尾添加标题。"""
        content = self.read()
        self.write(_add_heading(content, text, level, attrs))

    def add_heading_with_content(
        self,
        text: str,
        section_content: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        """在文档末尾添加标题及其内容。"""
        content = self.read()
        self.write(_add_heading_with_content(content, text, section_content, level, attrs))

    def append(self, content: str) -> None:
        """在文档末尾追加内容。"""
        existing = self.read()
        self.write(_append_content(existing, content))

    def insert_under_heading(self, heading_text: str, content: str) -> None:
        """在指定标题下插入内容。"""
        existing = self.read()
        self.write(_insert_under_heading(existing, heading_text, content))

    def replace_heading_content(self, heading_text: str, new_content: str) -> None:
        """替换指定标题下的内容。"""
        existing = self.read()
        self.write(_replace_heading_content(existing, heading_text, new_content))

    def get_headings(self) -> list[dict[str, Any]]:
        """获取文档中所有标题。"""
        content = self.read()
        headings = _get_headings(content)
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
        """获取指定标题下的内容块。"""
        return _get_section(self.read(), heading_text)

    def set_section_by_field(
        self,
        field: str,
        value: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        """按字段设置段落。"""
        content = self.read()
        self.write(
            _set_section_by_field(content, field, value, heading_text, section_content, level)
        )

    def set_section_by_id(
        self,
        section_id: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        """按 id 设置段落。"""
        self.set_section_by_field("id", section_id, heading_text, section_content, level)

    def get_section_by_field(self, field: str, value: str) -> str:
        """按字段获取段落。"""
        return _get_section_by_field(self.read(), field, value)

    def get_section_by_id(self, section_id: str) -> str:
        """按 id 获取段落。"""
        return _get_section_by_id(self.read(), section_id)

    def get_section_by_ref(self, ref: str | dict[str, str]) -> str:
        """按标题引用获取段落。"""
        return _get_section_by_ref(self.read(), ref)

    def get_heading_with_context(
        self,
        heading_ref: str | dict[str, str],
        before: int = 0,
        after: int = 0,
        include_heading: bool = True,
    ) -> str:
        """获取指定标题及其上下文。"""
        return _get_heading_with_context(self.read(), heading_ref, before, after, include_heading)

    def list_sections_by_field(self, field: str | None = None) -> list[dict[str, Any]]:
        """列举所有带属性的段落。"""
        return _list_sections_by_field(self.read(), field)


class VfsDirectory:
    """虚拟文件系统中的逻辑目录对象。"""

    def __init__(self, client: OpenVFS, uri: str) -> None:
        self._client = client
        self.uri = uri

    def list(self) -> list[str]:
        """列举目录下的子项。"""
        path = self._client._uri_path(self.uri)
        if path and not path.endswith("/"):
            path += "/"
        return self._client._storage.list_keys(path or "")

    def tree(self, max_depth: int = -1) -> str:
        """输出目录树形结构。"""
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

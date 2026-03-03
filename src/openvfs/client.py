"""OpenVFS 主客户端"""

from __future__ import annotations

from typing import Any

from openvfs.config import load_config
from openvfs.exceptions import NotFoundError
from openvfs.markdown.editor import (
    add_heading as _add_heading,
    add_heading_with_content as _add_heading_with_content,
    append_content as _append_content,
    insert_under_heading as _insert_under_heading,
    replace_heading_content as _replace_heading_content,
    get_section as _get_section,
    set_section_by_field as _set_section_by_field,
    set_section_by_id as _set_section_by_id,
    get_section_by_field as _get_section_by_field,
    get_section_by_id as _get_section_by_id,
    get_section_by_ref as _get_section_by_ref,
    get_heading_with_context as _get_heading_with_context,
    list_sections_by_field as _list_sections_by_field,
)
from openvfs.markdown.parser import get_headings as _get_headings
from openvfs.storage.tos import TOSStorage
from openvfs.uri import parse, to_object_key, ensure_md, is_file_uri
from openvfs.chain import DocChain


class MindMarkClient:
    """OpenVFS 客户端，提供 CRUD 及 Markdown 格式操作。"""

    def __init__(
        self,
        bucket: str | None = None,
        prefix: str = "",
        endpoint: str | None = None,
        region: str | None = None,
        ak: str | None = None,
        sk: str | None = None,
        namespaces: list[str] | None = None,
    ):
        cfg = load_config()
        self._storage = TOSStorage(
            bucket=bucket or cfg["bucket"],
            prefix=prefix if prefix else cfg["prefix"],
            endpoint=endpoint or cfg["endpoint"],
            region=region or cfg["region"],
            ak=ak,
            sk=sk,
        )
        self._namespaces = namespaces if namespaces is not None else cfg.get("namespaces")

    def path(self, *parts: str) -> DocChain:
        """链式入口：指定资源路径，返回 DocChain。"""
        return DocChain(self, list(parts))

    def _resolve_key(self, uri: str, for_file: bool = False) -> str:
        """解析 URI 为存储键。"""
        _, full_path = parse(uri, self._namespaces)
        if for_file and not is_file_uri(full_path):
            full_path = ensure_md(full_path)
        return to_object_key(full_path, self._storage._prefix)

    def _uri_path(self, uri: str) -> str:
        """获取 URI 对应的路径（用于 list）。"""
        _, full_path = parse(uri, self._namespaces)
        return full_path

    def create(self, uri: str, content: str) -> None:
        """创建 .md 文件。"""
        key = self._resolve_key(uri, for_file=True)
        self._storage.put(key, content)

    def read(self, uri: str) -> str:
        """读取 .md 文件内容。"""
        key = self._resolve_key(uri, for_file=True)
        try:
            data = self._storage.get(key)
            return data.decode("utf-8")
        except NotFoundError:
            raise NotFoundError(uri)

    def update(self, uri: str, content: str) -> None:
        """全量更新 .md 文件。"""
        key = self._resolve_key(uri, for_file=True)
        self._storage.put(key, content)

    def delete(self, uri: str) -> None:
        """删除 .md 文件。"""
        key = self._resolve_key(uri, for_file=True)
        self._storage.delete(key)

    def exists(self, uri: str) -> bool:
        """检查 URI 是否存在。"""
        key = self._resolve_key(uri, for_file=True)
        return self._storage.exists(key)

    def list(self, uri: str) -> list[str]:
        """列举目录下的子项（文件或子目录）。

        Returns:
            名称列表，目录以 / 结尾，如 ['api.md', 'docs/']
        """
        path = self._uri_path(uri)
        if path and not path.endswith("/"):
            path += "/"
        # list_keys 内部会通过 _key 添加 bucket prefix
        return self._storage.list_keys(path or "")

    def tree(self, uri: str, max_depth: int = -1) -> str:
        """输出目录树形结构。"""
        lines: list[str] = []
        base = uri.rstrip("/") or "openvfs://"

        def _walk(u: str, indent: str, depth: int) -> None:
            if max_depth >= 0 and depth > max_depth:
                return
            items = self.list(u)
            dirs = sorted([x for x in items if x.endswith("/")])
            files = sorted([x for x in items if not x.endswith("/")])
            all_items = dirs + files
            for i, name in enumerate(all_items):
                is_last = i == len(all_items) - 1
                branch = "└── " if is_last else "├── "
                lines.append(f"{indent}{branch}{name}")
                if name.endswith("/"):
                    next_indent = indent + ("    " if is_last else "│   ")
                    parent = u.rstrip("/")
                    child_uri = f"{parent}/{name}"
                    _walk(child_uri, next_indent, depth + 1)

        lines.append(base)
        _walk(base, "", 0)
        return "\n".join(lines)

    # --- Markdown 格式操作 ---

    def add_heading(
        self,
        uri: str,
        text: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        """在文档末尾添加标题。attrs 如 {"id": "install"} 会生成 {#id=install}。"""
        content = self.read(uri)
        self.update(uri, _add_heading(content, text, level, attrs))

    def add_heading_with_content(
        self,
        uri: str,
        text: str,
        section_content: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        """在文档末尾添加标题及其内容。"""
        content = self.read(uri)
        self.update(
            uri,
            _add_heading_with_content(content, text, section_content, level, attrs),
        )

    def append(self, uri: str, content: str) -> None:
        """在文档末尾追加内容。"""
        existing = self.read(uri)
        self.update(uri, _append_content(existing, content))

    def insert_under_heading(self, uri: str, heading_text: str, content: str) -> None:
        """在指定标题下插入内容。"""
        existing = self.read(uri)
        self.update(uri, _insert_under_heading(existing, heading_text, content))

    def replace_heading_content(
        self, uri: str, heading_text: str, new_content: str
    ) -> None:
        """替换指定标题下的内容。"""
        existing = self.read(uri)
        self.update(uri, _replace_heading_content(existing, heading_text, new_content))

    def get_headings(self, uri: str) -> list[dict[str, Any]]:
        """获取文档中所有标题。含 level, text, line_start, attrs。"""
        content = self.read(uri)
        headings = _get_headings(content)
        return [
            {
                "level": h.level,
                "text": h.text,
                "line_start": h.line_start,
                "attrs": getattr(h, "attrs", {}),
            }
            for h in headings
        ]

    def get_section(self, uri: str, heading_text: str) -> str:
        """获取指定标题下的内容块。"""
        content = self.read(uri)
        return _get_section(content, heading_text)

    # --- 按字段/值操作（类数据库按字段定位）---

    def set_section_by_field(
        self,
        uri: str,
        field: str,
        value: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        """按 field=value 设置段落。存在则更新，否则追加。标题带 {#field=value} 属性。"""
        content = self.read(uri)
        self.update(
            uri,
            _set_section_by_field(
                content, field, value, heading_text, section_content, level
            ),
        )

    def set_section_by_id(
        self,
        uri: str,
        section_id: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        """按 id 设置段落。等价于 set_section_by_field(..., "id", section_id, ...)。"""
        self.set_section_by_field(
            uri, "id", section_id, heading_text, section_content, level
        )

    def get_section_by_field(self, uri: str, field: str, value: str) -> str:
        """按 field=value 获取段落内容。"""
        content = self.read(uri)
        return _get_section_by_field(content, field, value)

    def get_section_by_id(self, uri: str, section_id: str) -> str:
        """按 id 获取段落内容。"""
        content = self.read(uri)
        return _get_section_by_id(content, section_id)

    def get_section_by_ref(
        self, uri: str, ref: str | dict[str, str]
    ) -> str:
        """按标题引用获取段落。ref 为标题文本或属性 dict，支持多属性匹配。"""
        content = self.read(uri)
        return _get_section_by_ref(content, ref)

    def get_heading_with_context(
        self,
        uri: str,
        heading_ref: str | dict[str, str],
        before: int = 0,
        after: int = 0,
        include_heading: bool = True,
    ) -> str:
        """获取指定标题及上下文。heading_ref 可为标题文本或 {"id": "install"} 等属性。"""
        content = self.read(uri)
        return _get_heading_with_context(
            content, heading_ref, before, after, include_heading
        )

    def list_sections_by_field(
        self, uri: str, field: str | None = None
    ) -> list[dict[str, Any]]:
        """列举所有带属性的段落，可按 field 筛选。"""
        content = self.read(uri)
        return _list_sections_by_field(content, field)

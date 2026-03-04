"""链式构建器：Path.file(name) -> heading/cell/link -> write；cell 可带属性。"""

from __future__ import annotations

from typing import Any

from openvfs.uri import SCHEME


def _format_attrs(attrs: dict[str, str] | None) -> str:
    if not attrs:
        return ""
    parts = [f"{k}={v}" for k, v in sorted(attrs.items())]
    return f" {{#{','.join(parts)}}}"


def _block_comment_attrs(attrs: dict[str, Any] | None) -> str:
    """块属性用 HTML 注释写在块前。"""
    if not attrs:
        return ""
    parts = [f"{k}={v}" for k, v in sorted(attrs.items()) if v is not None]
    if not parts:
        return ""
    return f"<!-- {{{','.join(parts)}}} -->\n"


def _format_block(
    content: str,
    block_type: str = "text",
    lang: str | None = None,
    link_text: str | None = None,
) -> str:
    """按内容类型格式化为 Markdown 块。"""
    block_type = (block_type or "text").lower()
    if block_type == "code":
        lang = lang or ""
        return f"```{lang}\n{content.strip()}\n```\n"
    if block_type == "json":
        return f"```json\n{content.strip()}\n```\n"
    if block_type == "link":
        url = content.strip()
        text = link_text or url
        return f"[{text}]({url})\n"
    return content.strip() + "\n\n"


class DocBuilder:
    """链式文档构建器：基于 Path，以 cell 为单位添加标题和内容，cell 可带属性。"""

    def __init__(self, path: Any, name: str) -> None:
        self._path = path
        self._name = name.strip()
        if not self._name:
            raise ValueError("文件名不能为空")
        if not self._name.endswith(".md"):
            self._name = f"{self._name}.md"
        self._cells: list[dict[str, Any]] = []

    def heading(self, text: str, level: int = 2, **attrs: str) -> DocBuilder:
        """添加标题。attrs 如 id=install 会生成为 {#id=install}。"""
        attrs_dict = {k: v for k, v in attrs.items() if v is not None}
        self._cells.append({"kind": "heading", "text": text, "level": level, "attrs": attrs_dict})
        return self

    def cell(
        self,
        content: str,
        type: str = "text",
        lang: str = "",
        link_text: str | None = None,
        **attrs: str,
    ) -> DocBuilder:
        """添加内容 cell。type: text | code | json | link。attrs 会写入块前注释便于按属性定位。"""
        t = (type or "text").lower()
        attrs_dict = {k: v for k, v in attrs.items() if v is not None}
        self._cells.append({
            "kind": "cell",
            "content": content,
            "type": t,
            "lang": lang or "",
            "link_text": link_text,
            "attrs": attrs_dict,
        })
        return self

    def text(self, content: str, **attrs: str) -> DocBuilder:
        """添加文本 cell。"""
        return self.cell(content, type="text", **attrs)

    def code(self, content: str, lang: str = "", **attrs: str) -> DocBuilder:
        """添加代码 cell。"""
        return self.cell(content, type="code", lang=lang, **attrs)

    def json_block(self, content: str, **attrs: str) -> DocBuilder:
        """添加 JSON cell。"""
        return self.cell(content, type="json", **attrs)

    def link(self, url: str, text: str | None = None, **attrs: str) -> DocBuilder:
        """添加链接 cell。"""
        return self.cell(url, type="link", link_text=text or url, **attrs)

    def build(self) -> str:
        """将当前 cell 列表渲染为 Markdown 字符串。"""
        out: list[str] = []
        for u in self._cells:
            if u["kind"] == "heading":
                line = f"{'#' * u['level']} {u['text']}{_format_attrs(u.get('attrs'))}\n"
                out.append(line)
            else:
                comment = _block_comment_attrs(u.get("attrs"))
                body = _format_block(
                    u["content"],
                    block_type=u["type"],
                    lang=u.get("lang"),
                    link_text=u.get("link_text"),
                )
                out.append(comment + body)
        return "".join(out).rstrip() + "\n"

    def write(self, overwrite: bool = True) -> DocBuilder:
        """将构建结果写入存储。"""
        body = self.build()
        if overwrite or not self._path.exists_file(self._name):
            self._path.create_file(self._name, body)
        else:
            existing = self._path.find_file(self._name).read()
            self._path.update_file(self._name, existing.rstrip() + "\n\n" + body)
        self._cells = []
        return self

    def get(self) -> str:
        """读取当前文件全文。"""
        return self._path.find_file(self._name).read()

    def get_cell(self, **attrs: str) -> str:
        """按 cell 属性获取内容。如 get_cell(id="install")。"""
        uri = self._path._file_uri(self._name)
        client = self._path._client
        if not attrs:
            raise ValueError("至少指定一个属性，如 id=install")
        if len(attrs) == 1 and "id" in attrs:
            return client.get_section_by_id(uri, attrs["id"])
        if len(attrs) == 1:
            k, v = next(iter(attrs.items()))
            return client.get_section_by_field(uri, k, v)
        return client.get_section_by_ref(uri, attrs)

    def list_cells(self, field: str | None = None) -> list[dict[str, Any]]:
        """列举带属性的 cell（段落），可按 field 筛选。"""
        uri = self._path._file_uri(self._name)
        return self._path._client.list_sections_by_field(uri, field)

"""链式构建器：资源路径 -> 文档 -> 标题/内容块 -> 写入或按属性获取

设计参考 DrissionPage：简洁而强大，链式调用。
"""

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


class DocChain:
    """链式文档构建与读取。"""

    def __init__(self, client: Any, path_parts: list[str], doc_name: str = "") -> None:
        self._client = client
        self._path_parts = list(path_parts)
        self._doc_name = doc_name
        self._buffer: list[str] = []

    def _uri_path(self) -> str:
        path = "/".join(self._path_parts).strip("/")
        if self._doc_name:
            name = self._doc_name if self._doc_name.endswith(".md") else f"{self._doc_name}.md"
            path = f"{path}/{name}" if path else name
        return path

    def _uri(self) -> str:
        p = self._uri_path()
        return f"{SCHEME}://{p}" if p else f"{SCHEME}://"

    def path(self, *parts: str) -> DocChain:
        """追加资源路径（可多次调用）。"""
        self._path_parts.extend(str(p).strip("/") for p in parts if str(p).strip())
        return self

    def doc(self, name: str) -> DocChain:
        """指定文档名（自动补 .md）。"""
        self._doc_name = name.strip()
        return self

    def heading(
        self,
        text: str,
        level: int = 2,
        **attrs: str,
    ) -> DocChain:
        """添加标题，可带属性 {#k=v}。"""
        attrs_dict = {k: v for k, v in attrs.items() if v is not None}
        line = f"{'#' * level} {text}{_format_attrs(attrs_dict)}\n"
        self._buffer.append(line)
        return self

    def block(
        self,
        content: str,
        type: str = "text",
        lang: str | None = None,
        link_text: str | None = None,
        **block_attrs: Any,
    ) -> DocChain:
        """添加内容块。type: text | code | json | link。block_attrs 写入块前注释。"""
        comment = _block_comment_attrs(block_attrs)
        body = _format_block(content, block_type=type, lang=lang, link_text=link_text)
        self._buffer.append(comment + body)
        return self

    def text(self, content: str, **block_attrs: Any) -> DocChain:
        """添加文本块。"""
        return self.block(content, type="text", **block_attrs)

    def code(self, content: str, lang: str = "", **block_attrs: Any) -> DocChain:
        """添加代码块。"""
        return self.block(content, type="code", lang=lang, **block_attrs)

    def json_block(self, content: str, **block_attrs: Any) -> DocChain:
        """添加 JSON 块。"""
        return self.block(content, type="json", **block_attrs)

    def link(self, url: str, text: str | None = None, **block_attrs: Any) -> DocChain:
        """添加链接块。"""
        return self.block(url, type="link", link_text=text, **block_attrs)

    def build(self) -> str:
        """返回当前 buffer 拼接内容。"""
        return "".join(self._buffer).rstrip() + "\n"

    def write(self, overwrite: bool = False) -> DocChain:
        """写入 TOS。若 overwrite 则覆盖，否则与已有内容拼接。"""
        uri = self._uri()
        body = self.build()
        if overwrite or not self._client.exists(uri):
            self._client.create(uri, body)
        else:
            existing = self._client.read(uri)
            self._client.update(uri, existing.rstrip() + "\n\n" + body)
        self._buffer = []
        return self

    def read(self) -> str:
        """读取当前文档全文。"""
        return self._client.read(self._uri())

    def get_block(self, **attrs: str) -> str:
        """按标题属性获取内容。支持多属性匹配，便于精确定位。"""
        uri = self._uri()
        if not attrs:
            raise ValueError("至少指定一个属性，如 id=xxx 或 type=work_report,from=task_executor_agent")
        if len(attrs) == 1 and "id" in attrs:
            return self._client.get_section_by_id(uri, attrs["id"])
        if len(attrs) == 1:
            k, v = next(iter(attrs.items()))
            return self._client.get_section_by_field(uri, k, v)
        return self._client.get_section_by_ref(uri, attrs)

    def list_blocks(self, field: str | None = None) -> list[dict[str, Any]]:
        """列举带属性的段落，可按 field 筛选。用于 TASK 时可按 msg_id/type/from 等筛出再 get_block。"""
        return self._client.list_sections_by_field(self._uri(), field)

    def get_by_hierarchy(self, *level_attrs: str) -> str:
        """按属性层级获取。如 get_by_hierarchy('id=install', 'id=step1') 逐级下钻。"""
        uri = self._uri()
        content = self._client.read(uri)
        from openvfs.markdown.parser import get_headings, find_heading_by_field

        lines = content.split("\n")
        scope_lines = lines
        for level_spec in level_attrs:
            if "=" not in level_spec:
                continue
            k, _, v = level_spec.strip().partition("=")
            k, v = k.strip(), v.strip()
            scope_content = "\n".join(scope_lines)
            headings = get_headings(scope_content)
            h = find_heading_by_field(headings, k, v)
            if not h:
                raise ValueError(f"未找到 {k}={v}")
            start_idx = h.line_start
            end_idx = (h.line_end - 1) if h.line_end else (len(scope_lines) - 1)
            scope_lines = scope_lines[start_idx : end_idx + 1]
        return "\n".join(scope_lines).rstrip()

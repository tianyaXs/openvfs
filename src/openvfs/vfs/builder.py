"""链式文档构建器。"""

from __future__ import annotations

from typing import Any, Literal

from openvfs.vfs.uri import SCHEME


def _format_attrs(attrs: dict[str, str] | None) -> str:
    if not attrs:
        return ""
    parts = [f"{k}={v}" for k, v in sorted(attrs.items())]
    return f" {{#{','.join(parts)}}}"


def _block_comment_attrs(attrs: dict[str, Any] | None) -> str:
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
    block_type = (block_type or "text").lower()
    if block_type == "code":
        return f"```{lang or ''}\n{content.strip()}\n```\n"
    if block_type == "json":
        return f"```json\n{content.strip()}\n```\n"
    if block_type == "link":
        url = content.strip()
        text = link_text or url
        return f"[{text}]({url})\n"
    return content.strip() + "\n\n"


class DocumentBuilder:
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
        path = self._uri_path()
        return f"{SCHEME}://{path}" if path else f"{SCHEME}://"

    def cd_path(self, *parts: str) -> DocumentBuilder:
        self._path_parts.extend(str(part).strip("/") for part in parts if str(part).strip())
        return self

    def create_folder(self, name: str) -> DocumentBuilder:
        folder = str(name).strip("/")
        if not folder:
            raise ValueError("目录名不能为空")
        self._path_parts.append(folder)
        self._client.mkdir(f"{SCHEME}://{'/'.join(self._path_parts)}")
        return self

    def create_file(self, name: str) -> DocumentBuilder:
        file_name = name.strip()
        if not file_name:
            raise ValueError("文件名不能为空")
        self._doc_name = file_name
        return self

    def heading(self, text: str, level: int = 2, **attrs: str) -> DocumentBuilder:
        attrs_dict = {key: value for key, value in attrs.items() if value is not None}
        self._buffer.append(f"{'#' * level} {text}{_format_attrs(attrs_dict)}\n")
        return self

    def block(
        self,
        content: str,
        type: str = "text",
        lang: str | None = None,
        link_text: str | None = None,
        **block_attrs: Any,
    ) -> DocumentBuilder:
        comment = _block_comment_attrs(block_attrs)
        body = _format_block(content, block_type=type, lang=lang, link_text=link_text)
        self._buffer.append(comment + body)
        return self

    def text(self, content: str, **block_attrs: Any) -> DocumentBuilder:
        return self.block(content, type="text", **block_attrs)

    def code(self, content: str, lang: str = "", **block_attrs: Any) -> DocumentBuilder:
        return self.block(content, type="code", lang=lang, **block_attrs)

    def json_block(self, content: str, **block_attrs: Any) -> DocumentBuilder:
        return self.block(content, type="json", **block_attrs)

    def link(self, url: str, text: str | None = None, **block_attrs: Any) -> DocumentBuilder:
        return self.block(url, type="link", link_text=text, **block_attrs)

    def build(self) -> str:
        return "".join(self._buffer).rstrip() + "\n"

    def write(self, overwrite: bool = False) -> DocumentBuilder:
        uri = self._uri()
        body = self.build()
        if overwrite:
            self._client.create(uri, body)
        else:
            self._client._mutate_file(
                uri,
                lambda existing: body if not existing else existing.rstrip() + "\n\n" + body,
                create_if_missing=True,
            )
        self._buffer = []
        return self

    def read(self) -> str:
        return self._client.read(self._uri())

    def find_cell(
        self,
        selector: str,
        expect: Literal["one", "zero_or_one", "many"] = "one",
    ) -> Any:
        return self._client.find_cell(self._uri(), selector, expect=expect)

    def list_cell(self) -> list[Any]:
        return self._client.list_cell(self._uri())

    def update_cell(
        self,
        selector: str,
        content: str,
        expect: Literal["one", "zero_or_one", "many"] = "one",
    ) -> Any:
        return self._client.update_cell(self._uri(), selector, content, expect=expect)

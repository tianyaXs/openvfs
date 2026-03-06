"""OpenVFS 主客户端。"""

from __future__ import annotations

from typing import Any

from openvfs.chain import DocumentBuilder
from openvfs.config import load_config
from openvfs.stores.base import BaseStore
from openvfs.uri import ensure_md, is_file_uri, parse, to_object_key
from openvfs.vfs import VfsDirectory, VfsDocument


class OpenVFS:
    """OpenVFS 门面对象，负责配置、路径解析和 VFS 对象创建。"""

    def __init__(
        self,
        bucket: str | None = None,
        prefix: str = "",
        endpoint: str | None = None,
        region: str | None = None,
        ak: str | None = None,
        sk: str | None = None,
        namespaces: list[str] | None = None,
        store: BaseStore | None = None,
    ):
        cfg = load_config()
        self._store = store or self._build_default_store(
            bucket=bucket or cfg["bucket"],
            prefix=prefix if prefix else cfg["prefix"],
            endpoint=endpoint or cfg["endpoint"],
            region=region or cfg["region"],
            ak=ak,
            sk=sk,
            store_name=cfg.get("store", "tos"),
        )
        self._namespaces = namespaces if namespaces is not None else cfg.get("namespaces")

    def _build_default_store(
        self,
        *,
        bucket: str,
        prefix: str,
        endpoint: str,
        region: str,
        ak: str | None,
        sk: str | None,
        store_name: str,
    ) -> BaseStore:
        normalized = (store_name or "tos").strip().lower()
        if normalized != "tos":
            raise ValueError(
                f"Unsupported default store: {store_name}. 请显式传入 store=..."
            )
        from openvfs.stores.tos import TOSStore

        return TOSStore(
            bucket=bucket,
            prefix=prefix,
            endpoint=endpoint,
            region=region,
            ak=ak,
            sk=sk,
        )

    def path(self, *parts: str) -> DocumentBuilder:
        """链式入口：指定资源路径，返回文档构建器。"""
        return DocumentBuilder(self, list(parts))

    def document(self, uri: str) -> VfsDocument:
        """创建文档对象。"""
        return VfsDocument(self, uri)

    def directory(self, uri: str) -> VfsDirectory:
        """创建目录对象。"""
        return VfsDirectory(self, uri)

    def _resolve_key(self, uri: str, for_file: bool = False) -> str:
        """解析 URI 为存储键。"""
        _, full_path = parse(uri, self._namespaces)
        if for_file and not is_file_uri(full_path):
            full_path = ensure_md(full_path)
        return to_object_key(full_path, self._store._prefix)

    def _uri_path(self, uri: str) -> str:
        """获取 URI 对应的路径。"""
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

    def add_heading(
        self,
        uri: str,
        text: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        self.document(uri).add_heading(text, level=level, attrs=attrs)

    def add_heading_with_content(
        self,
        uri: str,
        text: str,
        section_content: str,
        level: int = 1,
        attrs: dict[str, str] | None = None,
    ) -> None:
        self.document(uri).add_heading_with_content(
            text,
            section_content,
            level=level,
            attrs=attrs,
        )

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
        self.document(uri).set_section_by_field(
            field,
            value,
            heading_text,
            section_content,
            level=level,
        )

    def set_section_by_id(
        self,
        uri: str,
        section_id: str,
        heading_text: str,
        section_content: str,
        level: int = 2,
    ) -> None:
        self.document(uri).set_section_by_id(
            section_id,
            heading_text,
            section_content,
            level=level,
        )

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
        return self.document(uri).get_heading_with_context(
            heading_ref,
            before=before,
            after=after,
            include_heading=include_heading,
        )

    def list_sections_by_field(self, uri: str, field: str | None = None) -> list[dict[str, Any]]:
        return self.document(uri).list_sections_by_field(field)

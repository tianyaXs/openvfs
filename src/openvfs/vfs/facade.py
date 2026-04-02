"""OpenVFS 门面对象。"""

from __future__ import annotations

import threading
from typing import Any, Literal

from openvfs.exceptions import NotFoundError
from openvfs.stores import BaseStore, MemoryStore, adapt_store, create_default_store
from openvfs.vfs.builder import DocumentBuilder
from openvfs.vfs.config import load_config
from openvfs.vfs.directory import VfsDirectory
from openvfs.vfs.document import Cell
from openvfs.vfs.file import VfsFile
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
        self._key_locks: dict[str, threading.RLock] = {}
        self._key_locks_guard = threading.Lock()

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

    def find_file(self, path: str, must_exist: bool = True) -> VfsFile | None:
        uri = self._as_file_uri(path)
        file = VfsFile(self, uri)
        if must_exist and not file.exists():
            return None
        return file

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

    def _get_key_lock(self, key: str) -> threading.RLock:
        with self._key_locks_guard:
            lock = self._key_locks.get(key)
            if lock is None:
                lock = threading.RLock()
                self._key_locks[key] = lock
            return lock

    def _decode_data(self, data: bytes) -> str:
        return data.decode("utf-8")

    def _read_file_unlocked(self, key: str, uri: str) -> str:
        try:
            return self._decode_data(self._store.get(key))
        except NotFoundError as exc:
            raise ValueError(f"文件不存在: {uri}") from exc

    def _write_file_unlocked(self, key: str, content: str) -> None:
        self._store.put(key, content)

    def _mutate_file(
        self,
        uri: str,
        mutator: Any,
        *,
        create_if_missing: bool = False,
    ) -> str:
        file_uri = self._as_file_uri(uri)
        key = self._resolve_key(file_uri, for_file=True)
        with self._get_key_lock(key):
            exists = self._store.exists(key)
            if not exists and not create_if_missing:
                raise ValueError(f"文件不存在: {uri}")
            current = self._decode_data(self._store.get(key)) if exists else ""
            updated = mutator(current)
            if not isinstance(updated, str):
                raise TypeError("文件变更函数必须返回 str")
            self._write_file_unlocked(key, updated)
            return updated

    def _as_file_uri(self, path: str) -> str:
        raw = path.strip()
        if not raw:
            raise ValueError("文件路径不能为空")
        if raw.startswith("openvfs://"):
            return raw
        normalized = raw.strip("/")
        return f"openvfs://{normalized}"

    def create(self, uri: str, content: str) -> None:
        file_uri = self._as_file_uri(uri)
        key = self._resolve_key(file_uri, for_file=True)
        with self._get_key_lock(key):
            self._write_file_unlocked(key, content)

    def read(self, uri: str) -> str:
        file_uri = self._as_file_uri(uri)
        key = self._resolve_key(file_uri, for_file=True)
        with self._get_key_lock(key):
            return self._read_file_unlocked(key, uri)

    def update(self, uri: str, content: str) -> None:
        file_uri = self._as_file_uri(uri)
        key = self._resolve_key(file_uri, for_file=True)
        with self._get_key_lock(key):
            if not self._store.exists(key):
                raise ValueError(f"文件不存在: {uri}")
            self._write_file_unlocked(key, content)

    def delete(self, uri: str) -> None:
        file_uri = self._as_file_uri(uri)
        key = self._resolve_key(file_uri, for_file=True)
        with self._get_key_lock(key):
            if not self._store.exists(key):
                raise ValueError(f"文件不存在: {uri}")
            self._store.delete(key)

    def exists(self, uri: str) -> bool:
        file_uri = self._as_file_uri(uri)
        key = self._resolve_key(file_uri, for_file=True)
        with self._get_key_lock(key):
            return self._store.exists(key)

    def list(self, uri: str) -> list[str]:
        return self.directory(uri).list()

    def tree(self, uri: str, max_depth: int = -1) -> str:
        return self.directory(uri).tree(max_depth=max_depth)

    def add_cell(
        self,
        path: str,
        title: str,
        content: str,
        level: int = 2,
        attrs: dict[str, str] | None = None,
    ) -> Cell:
        file = self.find_file(path, must_exist=False)
        if file is None:
            raise RuntimeError(f"无法创建文件对象: {path}")
        md = file.as_markdown()
        return md.add_cell(title=title, content=content, level=level, attrs=attrs, create_if_missing=True)

    def list_cell(self, path: str) -> list[Cell]:
        file = self.find_file(path)
        if file is None:
            raise ValueError(f"文件不存在: {path}")
        return file.as_markdown().list_cell()

    def find_cell(
        self,
        path: str,
        selector: str,
        expect: Literal["one", "zero_or_one", "many"] = "one",
    ) -> Cell | list[Cell] | None:
        file = self.find_file(path)
        if file is None:
            raise ValueError(f"文件不存在: {path}")
        return file.as_markdown().find_cell(selector, expect=expect)

    def update_cell(
        self,
        path: str,
        selector: str,
        content: str,
        expect: Literal["one", "zero_or_one", "many"] = "one",
    ) -> Cell | list[Cell] | None:
        file = self.find_file(path)
        if file is None:
            raise ValueError(f"文件不存在: {path}")
        return file.as_markdown().update_cell(selector=selector, content=content, expect=expect)


OpenVFS = OpenVfs

"""py-key-value-aio 到 OpenVFS 的薄适配层。"""

from __future__ import annotations

import asyncio
import atexit
import base64
from typing import Any

from openvfs.exceptions import NotFoundError, StorageError
from openvfs.stores.base import BaseStore

INDEX_COLLECTION = "openvfs:index"
DATA_COLLECTION = "openvfs:data"
DIRECTORY_KEY_PREFIX = "dir:"


class KeyValueStoreAdapter(BaseStore):
    """将 py-key-value-aio 的异步 store 适配为 OpenVFS 可用的同步 BaseStore。"""

    def __init__(self, store: Any, prefix: str = "") -> None:
        self._kv_store = store
        self.prefix = prefix.strip("/")
        self._prefix = f"{self.prefix}/" if self.prefix else ""
        self._loop = asyncio.new_event_loop()
        self._closed = False
        atexit.register(self.close)

    def _run(self, coroutine: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            if self._closed:
                raise RuntimeError("KeyValueStoreAdapter 已关闭")
            return self._loop.run_until_complete(coroutine)
        raise RuntimeError("同步 OpenVFS 不能在已有事件循环中直接驱动异步 store，请后续改为异步入口")

    def close(self) -> None:
        if self._closed:
            return
        close = getattr(self._kv_store, "close", None)
        if close is not None:
            self._loop.run_until_complete(close())
        self._loop.close()
        self._closed = True

    def _directory_record_key(self, path: str) -> str:
        normalized = path.rstrip("/")
        return f"{DIRECTORY_KEY_PREFIX}{normalized}"

    def _get_index(self, path: str) -> list[str]:
        record = self._run(self._kv_store.get(self._directory_record_key(path), collection=INDEX_COLLECTION))
        if not record:
            return []
        children = record.get("children", [])
        if not isinstance(children, list):
            raise StorageError(f"非法目录索引记录: {path}")
        return [str(item) for item in children]

    def _put_index(self, path: str, children: list[str]) -> None:
        self._run(
            self._kv_store.put(
                self._directory_record_key(path),
                {"children": sorted(set(children))},
                collection=INDEX_COLLECTION,
            )
        )

    def create_folder(self, path: str) -> None:
        normalized = path.strip("/")
        if not normalized:
            return
        parts = [part for part in normalized.split("/") if part]
        parent = ""
        for part in parts:
            children = self._get_index(parent)
            child = f"{part}/"
            if child not in children:
                children.append(child)
                self._put_index(parent, children)
            parent = f"{parent}/{part}".strip("/")
            if not self._get_index(parent):
                self._put_index(parent, [])

    def _update_indexes_for_put(self, key: str) -> None:
        parts = [part for part in key.strip("/").split("/") if part]
        parent = ""
        for index, part in enumerate(parts):
            child = f"{part}/" if index < len(parts) - 1 else part
            children = self._get_index(parent)
            if child not in children:
                children.append(child)
                self._put_index(parent, children)
            parent = f"{parent}/{part}".strip("/")
            if index < len(parts) - 1 and not self._get_index(parent):
                self._put_index(parent, [])

    def _update_indexes_for_delete(self, key: str) -> None:
        parts = [part for part in key.strip("/").split("/") if part]
        if not parts:
            return
        parent = "/".join(parts[:-1])
        child = parts[-1]
        children = self._get_index(parent)
        if child in children:
            children.remove(child)
            self._put_index(parent, children)

    def put(self, key: str, content: str | bytes) -> None:
        encoded = base64.b64encode(content.encode("utf-8") if isinstance(content, str) else content).decode("ascii")
        self._run(
            self._kv_store.put(
                key,
                {"content_base64": encoded},
                collection=DATA_COLLECTION,
            )
        )
        self._update_indexes_for_put(key)

    def get(self, key: str) -> bytes:
        record = self._run(self._kv_store.get(key, collection=DATA_COLLECTION))
        if not record:
            raise NotFoundError(key)
        encoded = record.get("content_base64")
        if not isinstance(encoded, str):
            raise StorageError(f"非法内容记录: {key}")
        return base64.b64decode(encoded.encode("ascii"))

    def delete(self, key: str) -> None:
        self._run(self._kv_store.delete(key, collection=DATA_COLLECTION))
        self._update_indexes_for_delete(key)

    def exists(self, key: str) -> bool:
        record = self._run(self._kv_store.get(key, collection=DATA_COLLECTION))
        return record is not None

    def list_keys(self, prefix: str, delimiter: str = "/") -> list[str]:
        if delimiter != "/":
            raise StorageError("当前仅支持 '/' 作为目录分隔符")
        return self._get_index(prefix.rstrip("/"))

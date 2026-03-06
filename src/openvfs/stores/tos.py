"""火山云 TOS Store 实现。"""

from __future__ import annotations

import os
import warnings
from typing import Any

from openvfs.exceptions import NotFoundError, StorageError
from openvfs.stores.base import BaseStore

warnings.filterwarnings("ignore", category=SyntaxWarning, module="tos")


class TOSStore(BaseStore):
    """基于火山云 TOS 的 Store 实现。"""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        endpoint: str = "tos-cn-beijing.volces.com",
        region: str = "cn-beijing",
        ak: str | None = None,
        sk: str | None = None,
    ) -> None:
        try:
            import tos  # type: ignore
        except ImportError as exc:
            raise ImportError("TOSStore requires optional dependency: pip install openvfs[tos]") from exc

        self._tos = tos
        self.bucket = bucket
        self.prefix = (prefix or "").strip("/")
        self._prefix = f"{self.prefix}/" if self.prefix else ""

        access_key = ak or os.getenv("TOS_ACCESS_KEY")
        secret_key = sk or os.getenv("TOS_SECRET_KEY")
        if not access_key or not secret_key:
            raise StorageError("TOS credentials required: set TOS_ACCESS_KEY and TOS_SECRET_KEY")

        self._client = tos.TosClientV2(access_key, secret_key, endpoint, region)

    def _key(self, path: str) -> str:
        normalized = path.lstrip("/")
        return f"{self._prefix}{normalized}" if self._prefix else normalized

    def put(self, key: str, content: str | bytes) -> None:
        data = content.encode("utf-8") if isinstance(content, str) else content
        try:
            self._client.put_object(self.bucket, key, content=data)
        except self._tos.exceptions.TosClientError as exc:
            raise StorageError(f"TOS put failed: {exc.message}", getattr(exc, "request_id", None)) from exc
        except self._tos.exceptions.TosServerError as exc:
            raise StorageError(f"TOS put failed: {exc.message}", getattr(exc, "request_id", None)) from exc

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(self.bucket, key)
            return response.read()
        except self._tos.exceptions.TosServerError as exc:
            if getattr(exc, "status_code", 0) == 404 or "NoSuchKey" in str(exc.code or ""):
                raise NotFoundError(f"tos://{self.bucket}/{key}") from exc
            raise StorageError(f"TOS get failed: {exc.message}", getattr(exc, "request_id", None)) from exc
        except self._tos.exceptions.TosClientError as exc:
            raise StorageError(f"TOS get failed: {exc.message}") from exc

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(self.bucket, key)
        except self._tos.exceptions.TosClientError as exc:
            raise StorageError(f"TOS delete failed: {exc.message}") from exc
        except self._tos.exceptions.TosServerError as exc:
            raise StorageError(f"TOS delete failed: {exc.message}", getattr(exc, "request_id", None)) from exc

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(self.bucket, key)
            return True
        except self._tos.exceptions.TosServerError as exc:
            if getattr(exc, "status_code", 0) == 404:
                return False
            raise StorageError(f"TOS head failed: {exc.message}", getattr(exc, "request_id", None)) from exc
        except self._tos.exceptions.TosClientError as exc:
            raise StorageError(f"TOS head failed: {exc.message}") from exc

    def list_keys(self, prefix: str, delimiter: str = "/") -> list[str]:
        full_prefix = self._key(prefix)
        if not full_prefix.endswith("/"):
            full_prefix += "/"
        result: list[str] = []
        try:
            response = self._client.list_objects_type2(
                self.bucket,
                prefix=full_prefix,
                delimiter=delimiter,
                max_keys=1000,
            )
            for item in getattr(response, "common_prefixes", []) or []:
                prefix_value = getattr(item, "prefix", None) or ""
                name = prefix_value.rstrip("/").split("/")[-1]
                if name:
                    result.append(name + "/")
            for obj in getattr(response, "contents", []) or []:
                key = getattr(obj, "key", None) or ""
                if key and key != full_prefix:
                    relative = key[len(full_prefix) :] if key.startswith(full_prefix) else key
                    if relative:
                        result.append(relative)
        except self._tos.exceptions.TosClientError as exc:
            raise StorageError(f"TOS list failed: {exc.message}") from exc
        except self._tos.exceptions.TosServerError as exc:
            raise StorageError(f"TOS list failed: {exc.message}", getattr(exc, "request_id", None)) from exc
        return result

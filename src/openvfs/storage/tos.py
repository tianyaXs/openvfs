"""火山云 TOS 存储实现"""

import os
import warnings

from openvfs.exceptions import NotFoundError, StorageError
from openvfs.storage.base import StorageBackend

# 过滤 tos SDK 的 SyntaxWarning（无效转义序列）
warnings.filterwarnings("ignore", category=SyntaxWarning, module="tos")

try:
    import tos
except ImportError as e:
    raise ImportError("Please install tos: pip install tos") from e


class TOSStorage(StorageBackend):
    """火山云 TOS 存储后端"""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        endpoint: str = "tos-cn-beijing.volces.com",
        region: str = "cn-beijing",
        ak: str | None = None,
        sk: str | None = None,
    ):
        self.bucket = bucket
        self.prefix = (prefix or "").strip("/")
        self._prefix = f"{self.prefix}/" if self.prefix else ""

        ak = ak or os.getenv("TOS_ACCESS_KEY")
        sk = sk or os.getenv("TOS_SECRET_KEY")
        if not ak or not sk:
            raise StorageError("TOS credentials required: set TOS_ACCESS_KEY and TOS_SECRET_KEY")

        self._client = tos.TosClientV2(ak, sk, endpoint, region)

    def _key(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self._prefix}{path}" if self._prefix else path

    def put(self, key: str, content: str | bytes) -> None:
        data = content.encode("utf-8") if isinstance(content, str) else content
        try:
            self._client.put_object(self.bucket, key, content=data)
        except tos.exceptions.TosClientError as e:
            raise StorageError(f"TOS put failed: {e.message}", getattr(e, "request_id", None)) from e
        except tos.exceptions.TosServerError as e:
            raise StorageError(
                f"TOS put failed: {e.message}",
                getattr(e, "request_id", None),
            ) from e

    def get(self, key: str) -> bytes:
        try:
            resp = self._client.get_object(self.bucket, key)
            return resp.read()
        except tos.exceptions.TosServerError as e:
            if getattr(e, "status_code", 0) == 404 or "NoSuchKey" in str(e.code or ""):
                raise NotFoundError(f"tos://{self.bucket}/{key}") from e
            raise StorageError(
                f"TOS get failed: {e.message}",
                getattr(e, "request_id", None),
            ) from e
        except tos.exceptions.TosClientError as e:
            raise StorageError(f"TOS get failed: {e.message}") from e

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(self.bucket, key)
        except tos.exceptions.TosClientError as e:
            raise StorageError(f"TOS delete failed: {e.message}") from e
        except tos.exceptions.TosServerError as e:
            raise StorageError(
                f"TOS delete failed: {e.message}",
                getattr(e, "request_id", None),
            ) from e

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(self.bucket, key)
            return True
        except tos.exceptions.TosServerError as e:
            if getattr(e, "status_code", 0) == 404:
                return False
            raise StorageError(
                f"TOS head failed: {e.message}",
                getattr(e, "request_id", None),
            ) from e
        except tos.exceptions.TosClientError as e:
            raise StorageError(f"TOS head failed: {e.message}") from e

    def list_keys(self, prefix: str, delimiter: str = "/") -> list[str]:
        full_prefix = self._key(prefix)
        if not full_prefix.endswith("/"):
            full_prefix += "/"
        result: list[str] = []
        try:
            # TosClientV2 使用 list_objects_type2
            resp = self._client.list_objects_type2(
                self.bucket,
                prefix=full_prefix,
                delimiter=delimiter,
                max_keys=1000,
            )
            # 共同前缀（模拟子目录）- CommonPrefixInfo 有 prefix 属性
            for p in getattr(resp, "common_prefixes", []) or []:
                prefix_val = getattr(p, "prefix", None) or ""
                name = prefix_val.rstrip("/").split("/")[-1]
                if name:
                    result.append(name + "/")
            # 直接对象 - ListedObject 有 key 属性
            for obj in getattr(resp, "contents", []) or []:
                key = getattr(obj, "key", None) or ""
                if key and key != full_prefix:
                    rel = key[len(full_prefix) :] if key.startswith(full_prefix) else key
                    if rel:
                        result.append(rel)
        except tos.exceptions.TosClientError as e:
            raise StorageError(f"TOS list failed: {e.message}") from e
        except tos.exceptions.TosServerError as e:
            raise StorageError(
                f"TOS list failed: {e.message}",
                getattr(e, "request_id", None),
            ) from e
        return result

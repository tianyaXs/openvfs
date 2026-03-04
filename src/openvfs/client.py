"""OpenVFS 主客户端（纯虚拟文件系统能力）。"""

from __future__ import annotations

from openvfs.config import load_config
from openvfs.document import VFSFile
from openvfs.folder import VFSFolder
from openvfs.exceptions import NotFoundError
from openvfs.storage.tos import TOSStorage
from openvfs.uri import SCHEME, parse, to_object_key


class Path:
    """路径句柄：在指定路径下执行文件管理操作。"""

    def __init__(self, client: "Client", path_parts: list[str]) -> None:
        self._client = client
        self._path_parts = [p for p in path_parts if p]

    def _file_uri(self, name: str) -> str:
        path = "/".join(self._path_parts)
        name = name.strip().lstrip("/")
        if not name:
            raise ValueError("文件名不能为空")
        full = f"{path}/{name}" if path else name
        return f"{SCHEME}://{full}"

    def _dir_uri(self) -> str:
        path = "/".join(self._path_parts)
        return f"{SCHEME}://{path}/" if path else f"{SCHEME}://"

    def _folder_uri(self, name: str) -> str:
        name = name.strip().strip("/")
        if not name:
            raise ValueError("文件夹名不能为空")
        path = "/".join(self._path_parts)
        full = f"{path}/{name}" if path else name
        return f"{SCHEME}://{full}"

    def create_file(self, name: str, content: str) -> None:
        """创建文件。"""
        self._client.create_file(self._file_uri(name), content)

    def create_folder(self, name: str) -> None:
        """创建文件夹。"""
        self._client.create_folder(self._folder_uri(name))

    def find_file(self, name: str) -> VFSFile:
        """查找文件并返回文件对象。"""
        return self._client.find_file(self._file_uri(name))

    def find_folder(self, name: str) -> VFSFolder:
        """查找文件夹并返回文件夹对象。"""
        return self._client.find_folder(self._folder_uri(name))

    def update_file(self, name: str, content: str) -> None:
        """全量更新文件内容。"""
        self._client.update_file(self._file_uri(name), content)

    def delete(self, name: str) -> None:
        """删除文件。"""
        self._client.delete(self._file_uri(name))

    def exists_file(self, name: str) -> bool:
        """检查文件是否存在。"""
        return self._client.exists_file(self._file_uri(name))

    def exists_folder(self, name: str) -> bool:
        """检查文件夹是否存在。"""
        return self._client.exists_folder(self._folder_uri(name))

    def list(self) -> list[str]:
        """列举当前路径下子项（文件或子目录），目录以 / 结尾。"""
        return self._client.list(self._dir_uri())


class Client:
    """OpenVFS 客户端，提供通用文件管理接口。"""

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

    def path(self, path_spec: str) -> Path:
        """指定路径，返回 Path，用于 create/find/update/delete/list。"""
        parts = [p for p in path_spec.strip("/").split("/") if p]
        return Path(self, parts)

    def _resolve_key(self, uri: str) -> str:
        """解析 URI 为存储键。"""
        _, full_path = parse(uri, self._namespaces)
        return to_object_key(full_path, self._storage._prefix)

    def _uri_path(self, uri: str) -> str:
        """获取 URI 对应路径（用于 list）。"""
        _, full_path = parse(uri, self._namespaces)
        return full_path

    def create_file(self, uri: str, content: str) -> None:
        """创建文件。"""
        key = self._resolve_key(uri)
        self._storage.put(key, content)

    def find(self, uri: str) -> VFSFile:
        """查找文件并返回文件对象。"""
        return self.find_file(uri)

    def find_file(self, uri: str) -> VFSFile:
        """查找文件并返回文件对象。"""
        # 先验证目标存在，确保语义是 find 文件对象
        self._read_text(uri)
        return VFSFile(self, uri)

    def create_folder(self, uri: str) -> None:
        """创建文件夹（创建以 / 结尾的目录对象）。"""
        _, full_path = parse(uri, self._namespaces)
        folder = full_path.rstrip("/")
        if not folder:
            raise ValueError("cannot create root folder")
        folder_key = to_object_key(f"{folder}/", self._storage._prefix)
        self._storage.put(folder_key, "")

    def find_folder(self, uri: str) -> VFSFolder:
        """查找文件夹并返回文件夹对象。"""
        if not self.exists_folder(uri):
            raise NotFoundError(uri)
        return VFSFolder(self, uri)

    def _read_text(self, uri: str) -> str:
        """读取原始文本内容。"""
        key = self._resolve_key(uri)
        try:
            data = self._storage.get(key)
            return data.decode("utf-8")
        except NotFoundError:
            raise NotFoundError(uri)

    def _write_text(self, uri: str, content: str) -> None:
        """写入原始文本内容。"""
        key = self._resolve_key(uri)
        self._storage.put(key, content)

    def update_file(self, uri: str, content: str) -> None:
        """全量更新文件内容。"""
        self._write_text(uri, content)

    def delete(self, uri: str) -> None:
        """删除文件。"""
        key = self._resolve_key(uri)
        self._storage.delete(key)

    def exists_file(self, uri: str) -> bool:
        """检查文件是否存在。"""
        key = self._resolve_key(uri)
        return self._storage.exists(key)

    def exists_folder(self, uri: str) -> bool:
        """检查文件夹是否存在。"""
        _, full_path = parse(uri, self._namespaces)
        folder = full_path.rstrip("/")
        if not folder:
            return False

        folder_key = to_object_key(f"{folder}/", self._storage._prefix)
        if self._storage.exists(folder_key):
            return True

        items = self.list(uri)
        return len(items) > 0

    def list(self, uri: str) -> list[str]:
        """列举目录下子项（文件或子目录）。"""
        path = self._uri_path(uri)
        if path and not path.endswith("/"):
            path += "/"
        items = self._storage.list_keys(path or "")
        # 去重，避免目录对象和 common_prefix 同时返回导致重复。
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

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

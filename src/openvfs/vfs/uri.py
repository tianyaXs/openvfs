"""URI 解析与校验。"""

import re
from typing import Sequence

from openvfs.exceptions import InvalidURIError

SCHEME = "openvfs"
DEFAULT_NAMESPACES = frozenset({"resources", "user", "agent"})
VALID_PATH = re.compile(r"^[a-zA-Z0-9_\-\./]+$")


def parse(
    uri: str,
    allowed_namespaces: Sequence[str] | None = DEFAULT_NAMESPACES,
) -> tuple[str, str]:
    """解析 openvfs URI，返回 (首段, 完整路径)。"""
    if not uri or not isinstance(uri, str):
        raise InvalidURIError(uri or "", "URI must be non-empty string")

    uri = uri.strip()
    prefix = f"{SCHEME}://"
    if not uri.startswith(prefix):
        raise InvalidURIError(uri, f"URI must start with {prefix}")

    full_path = uri[len(prefix) :].strip("/")
    if not full_path:
        raise InvalidURIError(uri, "URI path cannot be empty")

    if not VALID_PATH.match(full_path.replace(".md", "")):
        raise InvalidURIError(uri, "Path contains invalid characters")

    if allowed_namespaces is not None and len(allowed_namespaces) > 0:
        first = full_path.split("/", 1)[0]
        nameset = frozenset(allowed_namespaces)
        if first not in nameset:
            raise InvalidURIError(
                uri,
                f"Path first segment must be one of {sorted(nameset)}",
            )

    first_segment = full_path.split("/", 1)[0]
    return first_segment, full_path


def to_object_key(uri_path: str, prefix: str = "") -> str:
    """将 URI 路径转为对象键。"""
    normalized_prefix = prefix.rstrip("/")
    normalized_key = uri_path.lstrip("/")
    if normalized_prefix:
        return f"{normalized_prefix}/{normalized_key}"
    return normalized_key


def ensure_md(uri_path: str) -> str:
    """确保路径以 .md 结尾。"""
    if uri_path.endswith(".md"):
        return uri_path
    return f"{uri_path.rstrip('/')}.md"


def is_file_uri(uri_path: str) -> bool:
    """判断是否为文件 URI。"""
    return uri_path.rstrip("/").endswith(".md")

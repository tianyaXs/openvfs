"""OpenVFS 异常定义"""


class MindMarkError(Exception):
    """OpenVFS 基础异常（保留类名以兼容）"""

    pass


class NotFoundError(MindMarkError):
    """资源不存在"""

    def __init__(self, uri: str, message: str | None = None):
        self.uri = uri
        super().__init__(message or f"Resource not found: {uri}")


class StorageError(MindMarkError):
    """存储层异常"""

    def __init__(self, message: str, request_id: str | None = None):
        self.request_id = request_id
        super().__init__(message)


class InvalidURIError(MindMarkError):
    """无效 URI"""

    def __init__(self, uri: str, message: str | None = None):
        self.uri = uri
        super().__init__(message or f"Invalid URI: {uri}")

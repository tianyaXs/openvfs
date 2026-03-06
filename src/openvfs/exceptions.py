"""OpenVFS 异常定义"""


class OpenVFSError(Exception):
    """OpenVFS 基础异常"""

    pass


class NotFoundError(OpenVFSError):
    """资源不存在"""

    def __init__(self, uri: str, message: str | None = None):
        self.uri = uri
        super().__init__(message or f"Resource not found: {uri}")


class StorageError(OpenVFSError):
    """存储层异常"""

    def __init__(self, message: str, request_id: str | None = None):
        self.request_id = request_id
        super().__init__(message)


class InvalidURIError(OpenVFSError):
    """无效 URI"""

    def __init__(self, uri: str, message: str | None = None):
        self.uri = uri
        super().__init__(message or f"Invalid URI: {uri}")


class ConcurrentModifyError(OpenVFSError):
    """并发修改冲突"""

    def __init__(self, message: str = "Concurrent modification detected"):
        super().__init__(message)


class LockError(OpenVFSError):
    """分布式锁异常"""

    pass

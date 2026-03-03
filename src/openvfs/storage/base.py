"""存储后端抽象"""

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    def put(self, key: str, content: str | bytes) -> None:
        """上传/覆盖对象。"""
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        """获取对象内容。"""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除对象。"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查对象是否存在。"""
        pass

    @abstractmethod
    def list_keys(self, prefix: str, delimiter: str = "/") -> list[str]:
        """列举指定前缀下的对象键或「目录」。

        Args:
            prefix: 前缀，如 resources/project/
            delimiter: 分隔符，用于模拟目录（返回共同前缀）

        Returns:
            对象键或目录名的列表
        """
        pass

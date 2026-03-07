"""存储后端抽象。"""

from abc import ABC, abstractmethod


class BaseStore(ABC):
    """OpenVFS 存储后端抽象基类。"""

    prefix: str
    _prefix: str

    @abstractmethod
    def put(self, key: str, content: str | bytes) -> None:
        """上传或覆盖对象内容。"""

    @abstractmethod
    def get(self, key: str) -> bytes:
        """获取对象内容。"""

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除对象。"""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查对象是否存在。"""

    @abstractmethod
    def list_keys(self, prefix: str, delimiter: str = "/") -> list[str]:
        """列举指定前缀下的对象键或逻辑目录。"""

    def create_folder(self, path: str) -> None:
        """创建逻辑目录，默认由具体实现按需覆盖。"""
        return None

"""兼容层：请改用 openvfs.stores.tos。"""

from openvfs.stores.tos import TOSStore

TOSStorage = TOSStore

__all__ = ["TOSStore", "TOSStorage"]

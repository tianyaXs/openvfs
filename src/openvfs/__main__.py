"""python -m openvfs"""

import os

from openvfs import OpenVFS


def main() -> int:
    if not os.getenv("TOS_ACCESS_KEY") or not os.getenv("TOS_SECRET_KEY"):
        print("请设置 TOS_ACCESS_KEY 和 TOS_SECRET_KEY 环境变量")
        return 1
    OpenVFS()
    print("OpenVFS 客户端已初始化")
    print("示例: client.create('openvfs://resources/demo/readme.md', '# Demo')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

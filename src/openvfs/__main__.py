"""python -m openvfs"""

import os

import openvfs


def main() -> int:
    if not os.getenv("TOS_ACCESS_KEY") or not os.getenv("TOS_SECRET_KEY"):
        print("请设置 TOS_ACCESS_KEY 和 TOS_SECRET_KEY 环境变量")
        return 1
    openvfs.Client()
    print("OpenVFS 已就绪，使用: client = openvfs.Client()")
    print("示例: client.create_file('openvfs://resources/demo/readme.md', '# Demo')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

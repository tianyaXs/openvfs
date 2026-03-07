"""python -m openvfs"""

from openvfs import OpenVfs


def main() -> int:
    vfs = OpenVfs.init_vfs()
    vfs.create("openvfs://resources/demo/readme.md", "# Demo")
    print("OpenVFS 已初始化")
    print("示例: myvfs = OpenVfs.init_vfs()")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""测试基础目录行为：子目录列举与深度树输出。"""

import os

import pytest

import openvfs


def _client() -> openvfs.Client:
    if os.getenv("OPENVFS_RUN_INTEGRATION") != "1":
        pytest.skip("set OPENVFS_RUN_INTEGRATION=1 to run TOS integration tests")
    if not os.getenv("TOS_ACCESS_KEY") or not os.getenv("TOS_SECRET_KEY"):
        pytest.skip("TOS credentials not set")
    return openvfs.Client(
        bucket="openvfs",
        endpoint="tos-cn-beijing.volces.com",
        region="cn-beijing",
    )


def test_nested_list():
    client = _client()
    base = client.path("resources/pytest/nested_list")
    try:
        base.create_file("root.txt", "root")
        base.create_file("a/b/c.txt", "leaf")

        items = base.list()
        assert "root.txt" in items
        assert "a/" in items
    finally:
        if base.exists_file("root.txt"):
            base.delete("root.txt")
        if base.exists_file("a/b/c.txt"):
            base.delete("a/b/c.txt")


def test_tree_max_depth():
    client = _client()
    root = "openvfs://resources/pytest/tree_depth"
    f1 = f"{root}/a.txt"
    f2 = f"{root}/d1/d2/b.txt"
    try:
        client.create_file(f1, "A")
        client.create_file(f2, "B")

        tree = client.tree(root, max_depth=1)
        assert "a.txt" in tree
        assert "d1/" in tree
    finally:
        if client.exists_file(f1):
            client.delete(f1)
        if client.exists_file(f2):
            client.delete(f2)

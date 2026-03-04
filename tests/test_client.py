"""OpenVFS 客户端测试（基础文件管理）。"""

import os

import pytest

import openvfs
from openvfs.uri import parse


def _client() -> openvfs.Client:
    """需要设置 TOS_ACCESS_KEY 和 TOS_SECRET_KEY 环境变量。"""
    if os.getenv("OPENVFS_RUN_INTEGRATION") != "1":
        pytest.skip("set OPENVFS_RUN_INTEGRATION=1 to run TOS integration tests")
    if not os.getenv("TOS_ACCESS_KEY") or not os.getenv("TOS_SECRET_KEY"):
        pytest.skip("TOS credentials not set")
    return openvfs.Client(
        bucket="openvfs",
        endpoint="tos-cn-beijing.volces.com",
        region="cn-beijing",
    )


def test_uri_validation():
    """测试 URI 校验。"""
    parse("openvfs://resources/project/readme.md")
    parse("openvfs://agent/skills/search.json")
    with pytest.raises(openvfs.InvalidURIError):
        parse("http://example.com")
    with pytest.raises(openvfs.InvalidURIError):
        parse("openvfs://")


def test_crud():
    """测试基础 CRUD 操作。"""
    client = _client()
    uri = "openvfs://resources/pytest/test_crud.txt"
    try:
        client.create_file(uri, "hello")
        assert client.exists_file(uri)
        assert client.find(uri).read() == "hello"

        client.update_file(uri, "world")
        assert client.find(uri).read() == "world"
    finally:
        if client.exists_file(uri):
            client.delete(uri)
    assert not client.exists_file(uri)


def test_list_and_tree():
    """测试目录列举与树形输出。"""
    client = _client()
    base = "openvfs://resources/pytest/vfs_tree"
    file1 = f"{base}/a.txt"
    file2 = f"{base}/nested/b.txt"
    try:
        client.create_file(file1, "A")
        client.create_file(file2, "B")

        items = client.list(base)
        assert "a.txt" in items
        assert "nested/" in items

        tree = client.tree(base)
        assert "a.txt" in tree
        assert "nested/" in tree
    finally:
        if client.exists_file(file1):
            client.delete(file1)
        if client.exists_file(file2):
            client.delete(file2)

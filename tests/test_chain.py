"""测试 Path 句柄的基础文件管理能力。"""

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


def test_path_create_find_delete():
    """path(path_spec) 单字符串路径，create/find/delete。"""
    client = _client()
    path = client.path("resources/pytest/vfs_path")
    doc_name = "chain.json"
    content = '{"name": "openvfs", "ok": true}'
    try:
        path.create_file(doc_name, content)
        assert path.exists_file(doc_name)
        got = path.find_file(doc_name).read()
        assert "openvfs" in got
    finally:
        if path.exists_file(doc_name):
            path.delete(doc_name)
    assert not path.exists_file(doc_name)


def test_path_update_and_list():
    """path.update_file 与 path.list。"""
    client = _client()
    p = client.path("resources/pytest/vfs_path")
    try:
        p.create_file("list_test.txt", "A")
        p.update_file("list_test.txt", "B")
        assert p.find_file("list_test.txt").read() == "B"
        items = p.list()
        assert "list_test.txt" in items
    finally:
        if p.exists_file("list_test.txt"):
            p.delete("list_test.txt")


def test_custom_namespaces():
    """可配置 namespaces：空列表表示不限制首段。"""
    from openvfs.uri import parse

    parse("openvfs://custom/app/readme.md", allowed_namespaces=[])
    parse("openvfs://resources/app/readme.md", allowed_namespaces=["resources", "custom"])
    with pytest.raises(openvfs.InvalidURIError):
        parse("openvfs://other/app/readme.md", allowed_namespaces=["resources"])

"""测试完整文件生命周期：创建、读取、更新、删除。"""

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


def test_file_lifecycle():
    client = _client()
    uri = "openvfs://resources/test/lifecycle_doc.json"

    try:
        initial = '{"version": 1, "name": "mindmark"}'
        client.create_file(uri, initial)
        assert client.exists_file(uri)
        assert '"version": 1' in client.find(uri).read()

        updated = '{"version": 2, "name": "mindmark", "status": "active"}'
        client.update_file(uri, updated)
        content = client.find(uri).read()
        assert '"version": 2' in content
        assert '"status": "active"' in content
    finally:
        if client.exists_file(uri):
            client.delete(uri)

    assert not client.exists_file(uri)

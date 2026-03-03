"""测试链式 API、可配置路径、内容类型、属性层级"""

import os

import pytest

from openvfs import MindMarkClient


def _client() -> MindMarkClient:
    if not os.getenv("TOS_ACCESS_KEY") or not os.getenv("TOS_SECRET_KEY"):
        pytest.skip("TOS credentials not set")
    return MindMarkClient(
        bucket="openvfs",
        endpoint="tos-cn-beijing.volces.com",
        region="cn-beijing",
    )


def test_chain_write_and_read():
    """链式：path -> doc -> heading -> block -> write / read"""
    client = _client()
    uri_path = ("resources", "pytest", "chain_test")
    doc_name = "chain.md"
    try:
        (
            client.path(*uri_path)
            .doc(doc_name)
            .heading("安装", level=2, id="install")
            .block("pip install openvfs", type="code", lang="bash")
            .heading("数据", level=2, id="data")
            .json_block('{"key": "value"}')
            .link("https://example.com", "示例链接")
            .write()
        )
        content = client.path(*uri_path).doc(doc_name).read()
        assert "## 安装 {#id=install}" in content
        assert "```bash" in content
        assert "```json" in content
        assert "[示例链接](https://example.com)" in content
        block = client.path(*uri_path).doc(doc_name).get_block(id="install")
        assert "pip install openvfs" in block
    finally:
        from openvfs.uri import SCHEME
        full_uri = f"{SCHEME}://{'/'.join(uri_path)}/{doc_name}"
        if client.exists(full_uri):
            client.delete(full_uri)


def test_custom_namespaces():
    """可配置 namespaces：空列表表示不限制首段"""
    from openvfs.uri import parse
    parse("openvfs://custom/app/readme.md", allowed_namespaces=[])
    parse("openvfs://resources/app/readme.md", allowed_namespaces=["resources", "custom"])
    with pytest.raises(Exception):
        parse("openvfs://other/app/readme.md", allowed_namespaces=["resources"])

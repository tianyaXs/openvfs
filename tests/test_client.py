"""OpenVFS 客户端测试"""

import os

import pytest

from openvfs import MindMarkClient
from openvfs.exceptions import InvalidURIError, NotFoundError


def _client() -> MindMarkClient:
    """需要设置 TOS_ACCESS_KEY 和 TOS_SECRET_KEY 环境变量。"""
    if not os.getenv("TOS_ACCESS_KEY") or not os.getenv("TOS_SECRET_KEY"):
        pytest.skip("TOS credentials not set")
    return MindMarkClient(
        bucket="openvfs",
        endpoint="tos-cn-beijing.volces.com",
        region="cn-beijing",
    )


def test_uri_validation():
    """测试 URI 校验。"""
    from openvfs.uri import parse

    parse("openvfs://resources/project/readme.md")
    parse("openvfs://agent/skills/search.md")
    with pytest.raises(InvalidURIError):
        parse("http://example.com")
    with pytest.raises(InvalidURIError):
        parse("openvfs://")


def test_crud():
    """测试 CRUD 操作。"""
    client = _client()
    uri = "openvfs://resources/pytest/test_crud.md"
    try:
        client.create(uri, "# Test\n\nContent")
        assert client.exists(uri)
        content = client.read(uri)
        assert "Test" in content and "Content" in content
        client.update(uri, "# Updated\n\nNew content")
        assert "Updated" in client.read(uri)
    finally:
        if client.exists(uri):
            client.delete(uri)
    assert not client.exists(uri)


def test_markdown_ops():
    """测试 Markdown 格式操作。"""
    client = _client()
    uri = "openvfs://resources/pytest/test_md.md"
    try:
        client.create(uri, "# Title\n\nIntro")
        client.add_heading(uri, "Section", level=2)
        client.insert_under_heading(uri, "Section", "Some text")
        content = client.read(uri)
        assert "## Section" in content and "Some text" in content
        headings = client.get_headings(uri)
        assert len(headings) >= 2
        section = client.get_section(uri, "Section")
        assert "Some text" in section
    finally:
        if client.exists(uri):
            client.delete(uri)

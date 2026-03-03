"""测试完整文档生命周期：创建、修改、更新、追加"""

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


def test_document_lifecycle():
    """完整流程：创建 -> 追加 -> 修改 -> 更新 -> 读取验证"""
    client = _client()
    uri = "openvfs://resources/test/lifecycle_doc.md"

    try:
        # 1. 创建文档
        initial = "# 项目说明\n\n这是初始内容。"
        client.create(uri, initial)
        assert client.exists(uri)
        assert "项目说明" in client.read(uri)

        # 2. 追加内容（add_heading + insert_under_heading）
        client.add_heading(uri, "功能特性", level=2)
        client.insert_under_heading(uri, "功能特性", "- 存储\n- 更新\n- 查询")
        content = client.read(uri)
        assert "## 功能特性" in content
        assert "- 存储" in content

        # 3. 修改（replace_heading_content）
        client.replace_heading_content(uri, "功能特性", "- 创建\n- 读取\n- 更新\n- 删除")
        content = client.read(uri)
        assert "- 创建" in content
        assert "- 存储" not in content

        # 4. 更新（全量覆盖）
        new_full = "# 项目说明 v2\n\n完全重写的内容。\n\n## 安装\n\npip install openvfs"
        client.update(uri, new_full)
        content = client.read(uri)
        assert "v2" in content
        assert "完全重写" in content
        assert "功能特性" not in content
        assert "## 安装" in content

        # 5. 追加段落（append）
        client.append(uri, "## 使用\n\n```python\nfrom openvfs import MindMarkClient\n```")
        content = client.read(uri)
        assert "## 使用" in content
        assert "MindMarkClient" in content

        # 6. 验证 get_section / get_headings
        install_section = client.get_section(uri, "安装")
        assert "pip install openvfs" in install_section
        headings = client.get_headings(uri)
        assert len(headings) == 3  # 项目说明、安装、使用
        assert headings[0]["text"] == "项目说明 v2"
        assert headings[1]["text"] == "安装"
        assert headings[2]["text"] == "使用"

    finally:
        if client.exists(uri):
            client.delete(uri)
    assert not client.exists(uri)

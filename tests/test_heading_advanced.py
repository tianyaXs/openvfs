"""测试标题高级功能：按字段/值、带上下文"""

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


def test_add_headings_with_content():
    """添加一二三级标题及内容。"""
    client = _client()
    uri = "openvfs://resources/pytest/advanced_headings.md"
    try:
        client.create(uri, "")
        # 一级
        client.add_heading_with_content(
            uri, "项目概述", "这是一个 OpenVFS 项目。", level=1
        )
        # 二级
        client.add_heading_with_content(
            uri, "安装说明", "pip install openvfs", level=2
        )
        # 三级
        client.add_heading_with_content(
            uri, "依赖项", "tos, python>=3.10", level=3
        )
        content = client.read(uri)
        assert "# 项目概述" in content
        assert "## 安装说明" in content
        assert "### 依赖项" in content
        assert "pip install openvfs" in content
    finally:
        if client.exists(uri):
            client.delete(uri)


def test_set_get_by_field():
    """按字段和值设置、获取段落。"""
    client = _client()
    uri = "openvfs://resources/pytest/field_sections.md"
    try:
        client.create(uri, "# 文档\n\n")
        # 按 id 设置
        client.set_section_by_id(
            uri, "install", "安装步骤", "pip install openvfs", level=2
        )
        client.set_section_by_id(uri, "api", "API 说明", "from openvfs import MindMarkClient", level=2)
        # 按 field=value 设置
        client.set_section_by_field(
            uri, "category", "guide", "使用指南", "见 README", level=2
        )
        # 按 id 获取
        install_content = client.get_section_by_id(uri, "install")
        assert "pip install openvfs" in install_content
        api_content = client.get_section_by_id(uri, "api")
        assert "MindMarkClient" in api_content
        # 按 field=value 获取
        guide_content = client.get_section_by_field(uri, "category", "guide")
        assert "见 README" in guide_content
    finally:
        if client.exists(uri):
            client.delete(uri)


def test_set_section_update_existing():
    """按 id 更新已存在段落。"""
    client = _client()
    uri = "openvfs://resources/pytest/update_section.md"
    try:
        client.create(uri, "")
        client.set_section_by_id(uri, "changelog", "更新日志", "v0.1.0 初始版本", level=2)
        content1 = client.get_section_by_id(uri, "changelog")
        assert "v0.1.0" in content1
        # 更新
        client.set_section_by_id(
            uri, "changelog", "更新日志", "v0.1.0 初始\nv0.2.0 新增字段", level=2
        )
        content2 = client.get_section_by_id(uri, "changelog")
        assert "v0.2.0" in content2
    finally:
        if client.exists(uri):
            client.delete(uri)


def test_get_heading_with_context():
    """带上下文获取标题。"""
    client = _client()
    uri = "openvfs://resources/pytest/context_section.md"
    try:
        doc = """# 总览

前言段落。

## 安装 {#id=install}

pip install openvfs

## 使用 {#id=usage}

from openvfs import MindMarkClient
"""
        client.create(uri, doc)
        # 按 id 获取，带前后 1 行
        ctx = client.get_heading_with_context(
            uri, {"id": "install"}, before=1, after=1
        )
        assert "## 安装" in ctx
        assert "pip install openvfs" in ctx
        # 按标题文本
        ctx2 = client.get_heading_with_context(
            uri, "安装", before=0, after=2, include_heading=True
        )
        assert "## 安装" in ctx2
    finally:
        if client.exists(uri):
            client.delete(uri)


def test_list_sections_by_field():
    """列举带属性的段落。"""
    client = _client()
    uri = "openvfs://resources/pytest/list_sections.md"
    try:
        doc = """# 文档

## 安装 {#id=install}
pip install

## API {#id=api,category=reference}
usage
"""
        client.create(uri, doc)
        sections = client.list_sections_by_field(uri)
        assert len(sections) >= 2  # id=install, id=api, category=reference
        ids = [s for s in sections if s["field"] == "id"]
        assert len(ids) == 2
        install_sections = [s for s in sections if s["value"] == "install"]
        assert any(s["heading"] == "安装" for s in install_sections)
    finally:
        if client.exists(uri):
            client.delete(uri)

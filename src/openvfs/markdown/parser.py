"""Markdown 标题解析

支持标题属性语法：## 标题 {#id=xxx} 或 ## 标题 {#field=value}
用于按字段/值快速定位段落，类似数据库按字段查询。
"""

import re
from dataclasses import dataclass, field


# 匹配 # ## ### 等标题行
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

# 匹配标题末尾属性 {#key=value} 或 {#k1=v1,k2=v2}
ATTRS_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")


def _parse_attrs(attrs_str: str) -> dict[str, str]:
    """解析属性字符串，如 'id=install' 或 'id=install,category=guide'。"""
    result: dict[str, str] = {}
    for part in attrs_str.split(","):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip()
    return result


def _extract_attrs(text: str) -> tuple[str, dict[str, str]]:
    """从标题文本中提取属性，返回 (纯净标题, 属性字典)。"""
    m = ATTRS_RE.search(text)
    if m:
        attrs = _parse_attrs(m.group(1))
        clean_text = ATTRS_RE.sub("", text).strip()
        return clean_text, attrs
    return text.strip(), {}


@dataclass
class Heading:
    """标题信息"""

    level: int  # 1-6
    text: str  # 不含属性的标题文本
    line_start: int  # 1-based
    line_end: int | None  # 下一同级或更高级标题的行，None 表示到文末
    attrs: dict[str, str] = field(default_factory=dict)  # 如 {"id": "install"}


def get_headings(content: str) -> list[Heading]:
    """解析 Markdown 内容，返回所有标题及位置。"""
    headings: list[Heading] = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            raw_text = m.group(2)
            text, attrs = _extract_attrs(raw_text)
            headings.append(
                Heading(
                    level=level,
                    text=text,
                    line_start=i,
                    line_end=None,
                    attrs=attrs,
                )
            )

    # 填充 line_end
    for idx, h in enumerate(headings):
        for next_h in headings[idx + 1 :]:
            if next_h.level <= h.level:
                h.line_end = next_h.line_start - 1
                break
        else:
            h.line_end = len(lines)

    return headings


def find_heading(headings: list[Heading], text: str) -> Heading | None:
    """按标题文本查找（精确匹配，不含属性部分）。"""
    text = text.strip()
    for h in headings:
        if h.text == text or h.text.strip() == text:
            return h
    return None


def find_heading_by_id(headings: list[Heading], section_id: str) -> Heading | None:
    """按 id 属性查找。"""
    return find_heading_by_field(headings, "id", section_id)


def find_heading_by_field(
    headings: list[Heading], field: str, value: str
) -> Heading | None:
    """按 field=value 查找。"""
    for h in headings:
        if h.attrs.get(field) == value:
            return h
    return None


def find_heading_by_ref(
    headings: list[Heading],
    ref: str | dict[str, str],
) -> Heading | None:
    """按多种方式查找标题。

    ref 可以是:
    - str: 按标题文本匹配
    - dict: 按字段匹配，如 {"id": "install"} 或 {"field": "value"}
    """
    if isinstance(ref, str):
        return find_heading(headings, ref)
    if isinstance(ref, dict):
        for h in headings:
            if all(h.attrs.get(k) == v for k, v in ref.items()):
                return h
    return None

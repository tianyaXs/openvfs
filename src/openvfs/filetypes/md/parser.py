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


@dataclass
class CellSelectorCondition:
    field: str
    value: str
    is_text: bool = False


def _split_selector_clauses(body: str) -> list[str]:
    clauses: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    escaped = False
    i = 0

    while i < len(body):
        ch = body[i]
        if escaped:
            buf.append(ch)
            escaped = False
            i += 1
            continue
        if ch == "\\":
            escaped = True
            buf.append(ch)
            i += 1
            continue
        if quote is not None:
            if ch == quote:
                quote = None
            buf.append(ch)
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if body[i : i + 2] == "@@":
            clause = "".join(buf).strip()
            if clause:
                clauses.append(clause)
            buf = []
            i += 2
            continue
        buf.append(ch)
        i += 1

    last_clause = "".join(buf).strip()
    if last_clause:
        clauses.append(last_clause)
    return clauses


def _split_unescaped_equal(clause: str) -> tuple[str, str]:
    quote: str | None = None
    escaped = False
    for i, ch in enumerate(clause):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if quote is not None:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch == "=":
            return clause[:i].strip(), clause[i + 1 :].strip()
    raise ValueError(f"无效 cell 选择器子句，缺少 '=': {clause}")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        inner = value[1:-1]
        return bytes(inner, "utf-8").decode("unicode_escape")
    if "@@" in value:
        raise ValueError("未加引号的值不能包含 '@@'，请使用引号包裹")
    return value.replace("\\@", "@").replace("\\=", "=").replace("\\\\", "\\")


def parse_cell_selector(selector: str) -> list[CellSelectorCondition]:
    source = selector.strip()
    if not source:
        raise ValueError("cell 选择器不能为空")

    if source.startswith("@@"):
        body = source[2:]
    elif source.startswith("@"):
        body = source[1:]
    else:
        raise ValueError("cell 选择器必须以 '@' 或 '@@' 开头")

    clauses = _split_selector_clauses(body)
    if not clauses:
        raise ValueError("cell 选择器没有有效子句")

    conditions: list[CellSelectorCondition] = []
    for clause in clauses:
        field_raw, value_raw = _split_unescaped_equal(clause)
        field_raw = field_raw.strip()
        is_text = field_raw.endswith("()")
        field = field_raw[:-2].strip() if is_text else field_raw
        if not field:
            raise ValueError(f"无效 cell 选择器字段: {field_raw}")
        conditions.append(
            CellSelectorCondition(
                field=field,
                value=_unquote(value_raw),
                is_text=is_text,
            )
        )
    return conditions

"""Markdown 格式编辑"""

from typing import Any, Literal

from openvfs.filetypes.md.parser import (
    CellSelectorCondition,
    find_heading,
    find_heading_by_field,
    find_heading_by_id,
    find_heading_by_ref,
    get_headings,
    parse_cell_selector,
)


def _format_attrs(attrs: dict[str, str] | None) -> str:
    """格式化为 {#k1=v1,k2=v2}。"""
    if not attrs:
        return ""
    parts = [f"{k}={v}" for k, v in sorted(attrs.items())]
    return f" {{#{','.join(parts)}}}"


def _make_heading(
    level: int,
    text: str,
    attrs: dict[str, str] | None = None,
) -> str:
    return f"{'#' * level} {text}{_format_attrs(attrs)}\n"


def add_heading(
    content: str,
    text: str,
    level: int = 1,
    attrs: dict[str, str] | None = None,
) -> str:
    """在文档末尾添加标题。"""
    return content.rstrip() + "\n\n" + _make_heading(level, text, attrs)


def add_heading_with_content(
    content: str,
    text: str,
    section_content: str,
    level: int = 1,
    attrs: dict[str, str] | None = None,
) -> str:
    """在文档末尾添加标题及其内容。"""
    block = _make_heading(level, text, attrs) + "\n" + section_content.rstrip() + "\n"
    return content.rstrip() + "\n\n" + block


def append_content(content: str, block: str) -> str:
    """在文档末尾追加内容块。"""
    return content.rstrip() + "\n\n" + block.rstrip() + "\n"


def insert_under_heading(content: str, heading_text: str, block: str) -> str:
    """在指定标题下插入内容（紧跟标题行后）。"""
    headings = get_headings(content)
    h = find_heading(headings, heading_text)
    if not h:
        raise ValueError(f"Heading not found: {heading_text}")

    lines = content.split("\n")
    insert_line = h.line_start
    block_lines = block.rstrip().split("\n")
    new_block = "\n".join(block_lines) + "\n"

    before = "\n".join(lines[: insert_line]) + "\n" if insert_line > 0 else ""
    after = "\n" + "\n".join(lines[insert_line:]) if insert_line < len(lines) else ""
    return before + new_block + after


def replace_heading_content(content: str, heading_text: str, new_content: str) -> str:
    """替换指定标题下的内容。"""
    headings = get_headings(content)
    h = find_heading(headings, heading_text)
    if not h:
        raise ValueError(f"Heading not found: {heading_text}")

    lines = content.split("\n")
    title_idx = h.line_start - 1
    content_start = title_idx + 1
    content_end = h.line_end if h.line_end else len(lines)

    before = "\n".join(lines[:content_start])
    after = "\n".join(lines[content_end:]) if content_end < len(lines) else ""
    new_block = new_content.rstrip()
    return (before + "\n\n" + new_block + "\n\n" + after).strip() + "\n"


def get_section(content: str, heading_text: str) -> str:
    """获取指定标题下的内容块（不含标题行）。"""
    headings = get_headings(content)
    h = find_heading(headings, heading_text)
    if not h:
        raise ValueError(f"Heading not found: {heading_text}")

    lines = content.split("\n")
    content_start = h.line_start
    content_end = h.line_end if h.line_end else len(lines)
    return "\n".join(lines[content_start:content_end]).rstrip()


# --- 按字段/值 操作（类似数据库按字段查询）---

def set_section_by_field(
    content: str,
    field: str,
    value: str,
    heading_text: str,
    section_content: str,
    level: int = 2,
) -> str:
    """按 field=value 设置段落。若已存在则更新内容，否则在末尾添加。

    标题将带有 {#field=value} 属性，便于后续按字段快速定位。
    """
    headings = get_headings(content)
    h = find_heading_by_field(headings, field, value)
    attrs = {field: value}
    new_block = _make_heading(level, heading_text, attrs) + "\n" + section_content.rstrip() + "\n"

    if h:
        # 更新：替换该标题及其内容
        lines = content.split("\n")
        start_idx = h.line_start - 1
        end_idx = (h.line_end if h.line_end else len(lines)) - 1
        before = "\n".join(lines[:start_idx])
        after = "\n".join(lines[end_idx + 1 :]) if end_idx + 1 < len(lines) else ""
        middle = new_block.rstrip()
        return (before + "\n\n" + middle + "\n\n" + after).strip() + "\n"
    else:
        return content.rstrip() + "\n\n" + new_block


def set_section_by_id(
    content: str,
    section_id: str,
    heading_text: str,
    section_content: str,
    level: int = 2,
) -> str:
    """按 id 设置段落。等价于 set_section_by_field(content, "id", section_id, ...)。"""
    return set_section_by_field(
        content, "id", section_id, heading_text, section_content, level
    )


def get_section_by_field(content: str, field: str, value: str) -> str:
    """按 field=value 获取段落内容。"""
    headings = get_headings(content)
    h = find_heading_by_field(headings, field, value)
    if not h:
        raise ValueError(f"No section with {field}={value!r}")

    lines = content.split("\n")
    content_start = h.line_start
    content_end = h.line_end if h.line_end else len(lines)
    return "\n".join(lines[content_start:content_end]).rstrip()


def get_section_by_id(content: str, section_id: str) -> str:
    """按 id 获取段落内容。"""
    return get_section_by_field(content, "id", section_id)


def get_section_by_ref(content: str, ref: str | dict[str, str]) -> str:
    """按标题引用获取段落内容。ref 可为标题文本或属性 dict（支持多属性匹配）。"""
    headings = get_headings(content)
    h = find_heading_by_ref(headings, ref)
    if not h:
        raise ValueError(f"Heading not found: {ref}")

    lines = content.split("\n")
    content_start = h.line_start
    content_end = h.line_end if h.line_end else len(lines)
    return "\n".join(lines[content_start:content_end]).rstrip()


# --- 带上下文的获取 ---

def get_heading_with_context(
    content: str,
    heading_ref: str | dict[str, str],
    before: int = 0,
    after: int = 0,
    include_heading: bool = True,
) -> str:
    """获取指定标题及其上下文指定行数。

    Args:
        content: 文档内容
        heading_ref: 标题引用，可为标题文本 str 或 属性 dict 如 {"id": "install"}
        before: 标题前额外行数
        after: 标题后（含标题下内容）额外行数
        include_heading: 是否包含标题行本身

    Returns:
        上下文片段
    """
    headings = get_headings(content)
    h = find_heading_by_ref(headings, heading_ref)
    if not h:
        ref_str = heading_ref if isinstance(heading_ref, str) else str(heading_ref)
        raise ValueError(f"Heading not found: {ref_str}")

    lines = content.split("\n")
    # 1-based 行号 -> 0-based 索引
    line_idx = h.line_start - 1
    content_end = (h.line_end if h.line_end else len(lines)) - 1

    start = max(0, line_idx - before)
    # after 表示标题「之后」额外多少行（含标题下的内容）
    end = min(len(lines), content_end + 1 + after)

    if not include_heading:
        start = line_idx + 1  # 从标题下一行开始

    return "\n".join(lines[start:end]).rstrip()


def list_sections_by_field(content: str, field: str | None = None) -> list[dict]:
    """列举所有带属性的段落，可按 field 筛选。

    Returns:
        [{"field": "id", "value": "install", "heading": "安装", "level": 2}, ...]
    """
    headings = get_headings(content)
    result = []
    for h in headings:
        if not h.attrs:
            continue
        if field and field not in h.attrs:
            continue
        for k, v in h.attrs.items():
            if field and k != field:
                continue
            result.append(
                {
                    "field": k,
                    "value": v,
                    "heading": h.text,
                    "level": h.level,
                }
            )
    return result


def _cell_from_heading(content_lines: list[str], heading: Any) -> dict:
    content_start = heading.line_start
    content_end = heading.line_end if heading.line_end else len(content_lines)
    body = "\n".join(content_lines[content_start:content_end]).rstrip()
    return {
        "title": heading.text,
        "level": heading.level,
        "attrs": dict(heading.attrs),
        "content": body,
        "line_start": heading.line_start,
        "line_end": heading.line_end,
    }


def _match_cell_condition(heading: Any, condition: CellSelectorCondition) -> bool:
    if condition.is_text:
        return heading.text == condition.value
    return heading.attrs.get(condition.field) == condition.value


def list_cells(content: str) -> list[dict]:
    headings = get_headings(content)
    lines = content.split("\n")
    return [_cell_from_heading(lines, heading) for heading in headings]


def find_cells(content: str, selector: str) -> list[dict]:
    conditions = parse_cell_selector(selector)
    headings = get_headings(content)
    lines = content.split("\n")

    matched = [
        heading
        for heading in headings
        if all(_match_cell_condition(heading, condition) for condition in conditions)
    ]
    return [_cell_from_heading(lines, heading) for heading in matched]


def add_cell(
    content: str,
    title: str,
    section_content: str,
    level: int = 2,
    attrs: dict[str, str] | None = None,
) -> str:
    return add_heading_with_content(content, title, section_content, level=level, attrs=attrs)


def update_cells(
    content: str,
    selector: str,
    section_content: str,
    expect: Literal["one", "zero_or_one", "many"] = "one",
) -> str:
    conditions = parse_cell_selector(selector)
    headings = get_headings(content)
    matched = [
        heading
        for heading in headings
        if all(_match_cell_condition(heading, condition) for condition in conditions)
    ]

    if expect == "one":
        if not matched:
            raise ValueError(f"update_cell 未命中: {selector}")
        if len(matched) > 1:
            raise ValueError(f"update_cell 预期 1 个结果，实际 {len(matched)} 个: {selector}")
        targets = [matched[0]]
    elif expect == "zero_or_one":
        if len(matched) > 1:
            raise ValueError(f"update_cell 预期最多 1 个结果，实际 {len(matched)} 个: {selector}")
        targets = matched
    else:
        targets = matched

    if not targets:
        return content.rstrip("\n") + "\n"

    lines = content.split("\n")
    replacement = section_content.rstrip()
    replacement_lines = [""] if not replacement else [""] + replacement.split("\n") + [""]

    for heading in sorted(targets, key=lambda item: item.line_start, reverse=True):
        title_idx = heading.line_start - 1
        content_start = title_idx + 1
        content_end = heading.line_end if heading.line_end else len(lines)
        lines = lines[:content_start] + replacement_lines + lines[content_end:]

    return "\n".join(lines).rstrip("\n") + "\n"

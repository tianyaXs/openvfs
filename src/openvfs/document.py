"""OpenVFS 文件对象与 Cell 模型（以 Markdown 为持久化格式）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


SUPPORTED_CELL_TYPES = {"text", "json", "code", "link", "heading"}
MARKER_PREFIX = "<!-- openvfs-cell "
MARKER_SUFFIX = " -->"


@dataclass
class Cell:
    """内容单元块。"""

    type: str
    content: str
    attrs: dict[str, str] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "attrs": dict(self.attrs),
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Cell":
        t = str(data.get("type", "text")).strip().lower()
        if t not in SUPPORTED_CELL_TYPES:
            raise ValueError(f"unsupported cell type: {t}")
        content = str(data.get("content", ""))
        attrs_raw = data.get("attrs") or {}
        meta_raw = data.get("meta") or {}
        attrs = {str(k): str(v) for k, v in attrs_raw.items()}
        meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}
        return cls(type=t, content=content, attrs=attrs, meta=meta)


class VFSFile:
    """虚拟文件对象，支持按 Cell 进行增删改查。"""

    def __init__(self, client: Any, uri: str):
        self._client = client
        self.uri = uri

    @staticmethod
    def _normalize_attrs(attrs: dict[str, str] | None) -> dict[str, str]:
        if not attrs:
            return {}
        return {str(k): str(v) for k, v in attrs.items()}

    @staticmethod
    def _is_json_document(raw: str) -> bool:
        raw = raw.strip()
        if not raw:
            return False
        if not (raw.startswith("{") and raw.endswith("}")):
            return False
        try:
            obj = json.loads(raw)
            return isinstance(obj, dict) and isinstance(obj.get("cells"), list)
        except json.JSONDecodeError:
            return False

    @staticmethod
    def _cell_to_markdown(cell: Cell) -> str:
        marker = (
            MARKER_PREFIX
            + json.dumps(
                {
                    "type": cell.type,
                    "attrs": cell.attrs,
                    "meta": cell.meta,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + MARKER_SUFFIX
        )

        t = cell.type
        body = ""
        if t == "heading":
            level = int(cell.meta.get("level", 2) or 2)
            level = max(1, min(6, level))
            body = f"{'#' * level} {cell.content.strip()}\n"
        elif t == "code":
            lang = str(cell.meta.get("lang", "") or "")
            body = f"```{lang}\n{cell.content.rstrip()}\n```\n"
        elif t == "json":
            body = f"```json\n{cell.content.rstrip()}\n```\n"
        elif t == "link":
            text = str(cell.meta.get("text") or cell.content.strip())
            url = cell.content.strip()
            body = f"[{text}]({url})\n"
        else:
            body = cell.content.rstrip() + "\n"

        return marker + "\n" + body + "\n"

    @staticmethod
    def _parse_code_fence(body: str) -> tuple[str, str] | None:
        m = re.match(r"^```([^\n]*)\n([\s\S]*?)\n```\s*$", body.strip())
        if not m:
            return None
        lang = m.group(1).strip()
        content = m.group(2)
        return lang, content

    @staticmethod
    def _parse_heading(body: str) -> tuple[int, str] | None:
        line = body.strip().splitlines()[0] if body.strip() else ""
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not m:
            return None
        return len(m.group(1)), m.group(2).strip()

    @staticmethod
    def _parse_link(body: str) -> tuple[str, str] | None:
        line = body.strip()
        m = re.match(r"^\[(.+)\]\((.+)\)$", line)
        if not m:
            return None
        return m.group(1), m.group(2)

    def _parse_markdown_cells(self, raw: str) -> list[Cell]:
        lines = raw.splitlines()
        starts: list[int] = []
        metas: list[dict[str, Any]] = []

        for i, line in enumerate(lines):
            if line.startswith(MARKER_PREFIX) and line.endswith(MARKER_SUFFIX):
                payload = line[len(MARKER_PREFIX) : -len(MARKER_SUFFIX)]
                try:
                    meta = json.loads(payload)
                    if not isinstance(meta, dict):
                        continue
                    starts.append(i)
                    metas.append(meta)
                except json.JSONDecodeError:
                    continue

        if not starts:
            return [Cell(type="text", content=raw)] if raw else []

        cells: list[Cell] = []
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
            meta = metas[idx]
            cell_type = str(meta.get("type", "text")).strip().lower()
            if cell_type not in SUPPORTED_CELL_TYPES:
                cell_type = "text"
            attrs = self._normalize_attrs(meta.get("attrs") or {})
            cell_meta = dict(meta.get("meta") or {})

            body_lines = lines[start + 1 : end]
            while body_lines and body_lines[0].strip() == "":
                body_lines = body_lines[1:]
            while body_lines and body_lines[-1].strip() == "":
                body_lines = body_lines[:-1]
            body = "\n".join(body_lines)

            content = body
            if cell_type in {"code", "json"}:
                parsed = self._parse_code_fence(body)
                if parsed:
                    lang, content = parsed
                    if cell_type == "code" and lang:
                        cell_meta["lang"] = lang
            elif cell_type == "heading":
                parsed = self._parse_heading(body)
                if parsed:
                    level, text = parsed
                    cell_meta["level"] = level
                    content = text
            elif cell_type == "link":
                parsed = self._parse_link(body)
                if parsed:
                    text, url = parsed
                    cell_meta["text"] = text
                    content = url

            cells.append(Cell(type=cell_type, content=content, attrs=attrs, meta=cell_meta))

        return cells

    def _parse_cells(self) -> list[Cell]:
        raw = self._client._read_text(self.uri)
        if not raw.strip():
            return []

        # 兼容旧 JSON 文档格式
        if self._is_json_document(raw):
            payload = json.loads(raw)
            return [Cell.from_dict(item) for item in payload.get("cells", [])]

        return self._parse_markdown_cells(raw)

    def _write_cells(self, cells: list[Cell]) -> None:
        blocks = [self._cell_to_markdown(c) for c in cells]
        content = "".join(blocks).rstrip() + "\n"
        self._client._write_text(self.uri, content)

    def read(self) -> str:
        """读取原始文件内容。"""
        return self._client._read_text(self.uri)

    def list_cells(self) -> list[Cell]:
        """列举全部 cell。"""
        return self._parse_cells()

    def add_cell(
        self,
        *,
        cell_type: str,
        content: str,
        attrs: dict[str, str] | None = None,
        **meta: Any,
    ) -> Cell:
        """追加一个 cell。"""
        cell = Cell.from_dict(
            {
                "type": cell_type,
                "content": content,
                "attrs": self._normalize_attrs(attrs),
                "meta": meta,
            }
        )
        cells = self._parse_cells()
        cells.append(cell)
        self._write_cells(cells)
        return cell

    def add_cells(self, cells: list[dict[str, Any] | Cell]) -> list[Cell]:
        """批量追加 cell（一次写入，适合高频构建）。"""
        if not cells:
            return []

        parsed: list[Cell] = []
        for item in cells:
            if isinstance(item, Cell):
                parsed.append(item)
            else:
                parsed.append(Cell.from_dict(item))

        existing = self._parse_cells()
        existing.extend(parsed)
        self._write_cells(existing)
        return parsed

    def find_cells(self, **attrs: str) -> list[Cell]:
        """按多个属性标签查询 cell（AND 匹配）。"""
        cells = self._parse_cells()
        if not attrs:
            return cells
        return [
            c
            for c in cells
            if all(c.attrs.get(str(k)) == str(v) for k, v in attrs.items())
        ]

    def find_cell(self, **attrs: str) -> Cell:
        """按多个属性标签查询单个 cell（返回首个匹配）。"""
        if not attrs:
            raise ValueError("find_cell requires at least one attr")
        matched = self.find_cells(**attrs)
        if not matched:
            raise ValueError(f"cell not found by attrs: {attrs}")
        return matched[0]

    def update_cell(
        self,
        match_attrs: dict[str, str],
        *,
        content: str | None = None,
        cell_type: str | None = None,
        attrs: dict[str, str] | None = None,
        **meta: Any,
    ) -> Cell:
        """按属性定位并更新首个 cell。"""
        if not match_attrs:
            raise ValueError("update_cell requires match_attrs")
        cells = self._parse_cells()
        for i, c in enumerate(cells):
            if not all(c.attrs.get(str(k)) == str(v) for k, v in match_attrs.items()):
                continue
            new_type = c.type if cell_type is None else cell_type
            updated = Cell.from_dict(
                {
                    "type": new_type,
                    "content": c.content if content is None else content,
                    "attrs": c.attrs if attrs is None else self._normalize_attrs(attrs),
                    "meta": {**c.meta, **meta} if meta else c.meta,
                }
            )
            cells[i] = updated
            self._write_cells(cells)
            return updated
        raise ValueError(f"cell not found by attrs: {match_attrs}")

    def delete_cell(self, **attrs: str) -> int:
        """按属性删除 cell，返回删除数量。"""
        if not attrs:
            raise ValueError("delete_cell requires at least one attr")

        cells = self._parse_cells()
        kept: list[Cell] = []
        deleted = 0
        for c in cells:
            if all(c.attrs.get(str(k)) == str(v) for k, v in attrs.items()):
                deleted += 1
            else:
                kept.append(c)

        if deleted > 0:
            self._write_cells(kept)
        return deleted

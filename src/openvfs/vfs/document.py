from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from openvfs.filetypes.md.editor import add_cell as _add_cell
from openvfs.filetypes.md.editor import find_cells as _find_cells
from openvfs.filetypes.md.editor import list_cells as _list_cells
from openvfs.filetypes.md.editor import update_cells as _update_cells

if TYPE_CHECKING:
    from openvfs.vfs.facade import OpenVFS


@dataclass(frozen=True)
class Cell:
    title: str
    level: int
    attrs: dict[str, str]
    content: str
    line_start: int
    line_end: int | None

    def read(self) -> str:
        return self.content


class MarkdownDocument:
    def __init__(self, client: OpenVFS, uri: str) -> None:
        self._client = client
        self.uri = uri

    def read(self) -> str:
        return self._client.read(self.uri)

    def write(self, content: str) -> None:
        self._client.create(self.uri, content)

    def list_cell(self) -> list[Cell]:
        return self._to_cells(_list_cells(self.read()))

    def find_cell(
        self,
        selector: str,
        expect: Literal["one", "zero_or_one", "many"] = "one",
    ) -> Cell | list[Cell] | None:
        return self._resolve_cells(_find_cells(self.read(), selector), selector, expect, action="find_cell")

    def add_cell(
        self,
        title: str,
        content: str,
        level: int = 2,
        attrs: dict[str, str] | None = None,
        create_if_missing: bool = False,
    ) -> Cell:
        updated = self._client._mutate_file(
            self.uri,
            lambda current: _add_cell(current, title, content, level=level, attrs=attrs),
            create_if_missing=create_if_missing,
        )
        selector: str
        if attrs and "id" in attrs:
            selector = f"@id={self._selector_value(attrs['id'])}"
        else:
            selector = f"@text()={self._selector_value(title)}"
        result = self._resolve_cells(_find_cells(updated, selector), selector, "one", action="add_cell")
        if isinstance(result, Cell):
            return result
        raise RuntimeError("add_cell 返回类型异常")

    def update_cell(
        self,
        selector: str,
        content: str,
        expect: Literal["one", "zero_or_one", "many"] = "one",
    ) -> Cell | list[Cell] | None:
        updated = self._client._mutate_file(
            self.uri,
            lambda current: _update_cells(current, selector, content, expect=expect),
            create_if_missing=False,
        )
        return self._resolve_cells(_find_cells(updated, selector), selector, expect, action="update_cell")

    def _to_cells(self, raw_cells: list[dict]) -> list[Cell]:
        return [
            Cell(
                title=item["title"],
                level=item["level"],
                attrs=item["attrs"],
                content=item["content"],
                line_start=item["line_start"],
                line_end=item["line_end"],
            )
            for item in raw_cells
        ]

    def _resolve_cells(
        self,
        raw_cells: list[dict],
        selector: str,
        expect: Literal["one", "zero_or_one", "many"],
        action: str,
    ) -> Cell | list[Cell] | None:
        cells = self._to_cells(raw_cells)
        if expect == "many":
            return cells
        if expect == "zero_or_one":
            if len(cells) > 1:
                raise ValueError(f"{action} 预期最多 1 个结果，实际 {len(cells)} 个: {selector}")
            return cells[0] if cells else None
        if not cells:
            raise ValueError(f"{action} 未命中: {selector}")
        if len(cells) > 1:
            raise ValueError(f"{action} 预期 1 个结果，实际 {len(cells)} 个: {selector}")
        return cells[0]

    @staticmethod
    def _selector_value(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

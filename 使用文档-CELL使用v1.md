# OpenVFS CELL 使用文档 V1

## 1. 结论（先看这个）

- 当前版本的 Cell 核心操作 `add_cell` / `find_cell` / `list_cell` / `update_cell` 已可用。
- 同一进程、同一 `OpenVfs` 实例下的并发写入已做串行化保护（按文件 key 加锁）。
- `update_cell` 仅更新正文，不修改标题和属性。
- 目前没有 `delete_cell`、`rename_cell`、`update_cell_attrs` 等 API。

## 2. Cell 操作可行性总表

| 操作目标 | OpenVfs 门面 | MarkdownDocument | DocumentBuilder | 当前可行性 | 并发行为（同进程同实例） | 说明 |
|---|---|---|---|---|---|---|
| 新增 Cell | `add_cell(path, title, content, level=2, attrs=None)` | `add_cell(title, content, level=2, attrs=None)` | 无直接 `add_cell`（可走 `vfs.add_cell`） | [可行] | [已保护]（原子读改写） | 文件不存在时会自动创建空文档后新增 |
| 查询单个/多个 Cell | `find_cell(path, selector, expect=...)` | `find_cell(selector, expect=...)` | `find_cell(selector, expect=...)` | [可行] | 读操作加同 key 锁 | 支持 `one/zero_or_one/many` |
| 列出全部 Cell | `list_cell(path)` | `list_cell()` | `list_cell()` | [可行] | 读操作加同 key 锁 | 返回 `list[Cell]` |
| 更新 Cell 正文 | `update_cell(path, selector, content, expect=...)` | `update_cell(selector, content, expect=...)` | `update_cell(selector, content, expect=...)` | [可行] | [已保护]（原子读改写） | 仅替换正文，标题/attrs 不变 |
| 删除 Cell | 无 | 无 | 无 | [不可行] | - | 当前版本未提供 |
| 修改 Cell 标题 | 无 | 无 | 无 | [不可行] | - | 当前版本未提供 |
| 修改 Cell attrs | 无 | 无 | 无 | [不可行] | - | 当前版本未提供 |

## 3. 选择器语法（当前实现）

| 类型 | 语法 | 示例 | 是否可行 | 说明 |
|---|---|---|---|---|
| 单条件属性匹配 | `@field=value` | `@id=install` | [可行] | 精确匹配 |
| 文本匹配 | `@text()=value` | `@text()=安装` | [可行] | 匹配标题文本 |
| 多条件 AND | `@@a=b@@c=d` | `@@class=guide@@id=install` | [可行] | 所有条件必须同时满足 |
| 带引号值 | `@id="a@@b"` | `@id="one@@two"` | [可行] | 值含 `@@` 时必须加引号 |
| 非法前缀 | `id=install` | - | [不可行] | 必须以 `@` 或 `@@` 开头 |
| OR / 正则查询 | 无 | - | [不可行] | 仅支持精确 AND 匹配 |

## 4. `expect` 语义（find/update 通用）

| expect | 命中 0 条 | 命中 1 条 | 命中 >1 条 | 返回类型 |
|---|---|---|---|---|
| `one` | 抛异常 | 返回 `Cell` | 抛异常 | `Cell` |
| `zero_or_one` | 返回 `None` | 返回 `Cell` | 抛异常 | `Cell \| None` |
| `many` | 返回空列表 | 返回单元素列表 | 返回列表 | `list[Cell]` |

## 5. 并发与一致性可行性

| 场景 | 当前状态 | 说明 |
|---|---|---|
| 同一进程、同一 `OpenVfs` 实例并发写同一文件 | [可行] | 已按文件 key 加 `RLock`，`_mutate_file` 内原子读改写 |
| 同一进程并发读写同一文件 | [可行] | 读写都走同 key 锁，避免交叉覆盖 |
| 不同 `OpenVfs` 实例并发写（同进程） | [部分可行] | 锁在实例内，不是全局锁 |
| 多进程/分布式并发写同一对象 | [不可保证] | 当前无跨进程 CAS/版本号机制 |

## 6. 快速示例

```python
from openvfs import OpenVfs

vfs = OpenVfs.init_vfs()

# 新增
vfs.add_cell("resources/project/readme", "安装", "uv add openvfs", attrs={"id": "install", "class": "guide"})

# 查询
cell = vfs.find_cell("resources/project/readme", "@id=install")
cells = vfs.find_cell("resources/project/readme", "@@class=guide", expect="many")

# 更新正文
updated = vfs.update_cell(
    "resources/project/readme",
    "@id=install",
    "uv add openvfs\nuv add py-key-value-aio",
)

# 列举
all_cells = vfs.list_cell("resources/project/readme")
```

## 7. 当前版本建议

- 强烈建议每个 Cell 设置稳定 `id`，优先使用 `@id=...` 查询和更新。
- 对不确定唯一性的查询，先用 `expect="many"` 评估命中集合，再做更新。
- 在多实例或分布式写入场景，建议后续补充版本号/CAS 机制后再作为强一致写路径。

## 8. 与主流命名约定对照（调研结论）

| 语义 | 主流约定（Python 生态） | OpenVFS 当前状态 | 是否对齐 |
|---|---|---|---|
| 查找一个可空对象 | `find_* -> Optional[T]` | `find_cell(..., expect="zero_or_one") -> Cell \| None` | [对齐] |
| 获取唯一对象 | `get_* -> T`（不存在抛异常） | `find_cell(..., expect="one")`（未命中/多命中抛异常） | [语义对齐，命名不同] |
| 列举 | `list_* -> list[T]` | `list_cell() -> list[Cell]` | [对齐] |
| 更新 | `update_*` | `update_cell(...)` | [对齐] |
| 删除（严格） | `remove_*` | 无 | [未实现] |
| 删除（静默） | `discard_*` | 无 | [未实现] |

说明：外部调研显示 `find/get/list/update` 这组语义在 Python 社区可读性最好；你当前 Cell API 主体已符合该方向，后续若补删除类能力，建议成对提供严格与静默两种语义。

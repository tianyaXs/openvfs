# OpenVFS 使用说明

OpenVFS 聚焦通用虚拟文件系统（VFS），并在文件对象层提供 Cell 单元块管理。

## Client API

```python
import openvfs

vfs = openvfs.Client()
```

- `create_file(uri, content)`
- `create_folder(uri)`
- `find(uri) -> VFSFile`
- `find_file(uri) -> VFSFile`
- `find_folder(uri) -> VFSFolder`
- `update_file(uri, content)`
- `delete(uri)`
- `exists_file(uri)`
- `exists_folder(uri)`
- `list(uri)`
- `tree(uri, max_depth=-1)`

## Path API

```python
path = vfs.path("resources/my_project")

path.create_file("doc.md", "")
file = path.find_file("doc.md")
```

- `path.create_file(name, content)`
- `path.create_folder(name)`
- `path.find_file(name) -> VFSFile`
- `path.find_folder(name) -> VFSFolder`
- `path.update_file(name, content)`
- `path.delete(name)`
- `path.exists_file(name)`
- `path.exists_folder(name)`
- `path.list()`

## VFSFile 与 Cell

`find` 返回 `VFSFile`，在文件对象上按 cell 操作：
文件持久化为 Markdown 原文，每个 cell 会被序列化为一个 Markdown 内容块。

- `read()`：原始内容
- `list_cells()`：列举所有 cell
- `add_cell(cell_type, content, attrs={...}, **meta)`
- `add_cells([...])`：批量追加 cell
- `find_cell(**attrs)`：按多个属性标签查询首个 cell
- `find_cells(**attrs)`：按多个属性标签查询全部 cell
- `update_cell(match_attrs, content=..., cell_type=..., attrs=..., **meta)`
- `delete_cell(**attrs)`

### cell 类型

- `text`
- `json`
- `code`
- `link`
- `heading`

### 示例：多标签定位

```python
uri = "openvfs://resources/demo/cells.md"
vfs.create_file(uri, "")
file = vfs.find(uri)

file.add_cell(
    cell_type="code",
    content="pip install openvfs",
    attrs={"id": "install", "scope": "guide"},
    lang="bash",
)

cell = file.find_cell(id="install", scope="guide")
print(cell.content)
```

## URI 规范

- 格式：`openvfs://{namespace}/{path}`
- 默认命名空间：`resources`、`user`、`agent`
- `Client(namespaces=[...])` 自定义
- `Client(namespaces=[])` 关闭首段限制

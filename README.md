# OpenVFS

面向 Agent 的虚拟文件系统，基于火山云 TOS 存储。

## 安装

```bash
pip install openvfs
```

## 核心模型

- `Client`：文件系统入口
- `VFSFolder`：文件夹对象（由 `find_folder` 返回）
- `VFSFile`：文件对象（由 `find` 返回）
- `Cell`：单元内容块（`text/json/code/link/heading`）

## 核心 API

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

## 文件对象 API（VFSFile）

文件内容以 Markdown 原文存储，每个 cell 对应一个 Markdown 块。

- `read()`：读取原始内容
- `list_cells()`：获取所有 cell
- `add_cell(cell_type, content, attrs={...}, **meta)`
- `add_cells([...])`：批量追加 cell（一次写入）
- `find_cell(**attrs)`：按多个属性标签定位单个 cell
- `find_cells(**attrs)`：按多个属性标签查询多个 cell
- `update_cell(match_attrs, content=..., cell_type=..., attrs=..., **meta)`
- `delete_cell(**attrs)`

## 快速示例

```python
import openvfs

vfs = openvfs.Client()
uri = "openvfs://resources/my_project/readme.md"

vfs.create_folder("openvfs://resources/my_project")
vfs.create_file(uri, "")

folder = vfs.find_folder("openvfs://resources/my_project")
file = vfs.find(uri)

file.add_cell(
    cell_type="heading",
    content="安装",
    attrs={"id": "install", "scope": "guide"},
    level=2,
)
file.add_cell(
    cell_type="code",
    content="pip install openvfs",
    attrs={"id": "install_cmd", "scope": "guide"},
    lang="bash",
)

cell = file.find_cell(id="install_cmd", scope="guide")
print(cell.type, cell.content)
```

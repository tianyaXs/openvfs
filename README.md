# OpenVFS

Agent 专用 Markdown 虚拟文件系统中间件，底层基于可热插拔的 Store 后端。

## 安装

```bash
uv add py-key-value-aio
uv add openvfs
```

## 快速示例

```python
from openvfs import OpenVfs

myvfs = OpenVfs.init_vfs()
file = myvfs.find_file("resources/project/readme", must_exist=False)
if file is None:
    raise RuntimeError("无法创建文件对象")

file.create("# 项目说明\n")
doc = file.as_markdown()
doc.add_cell("安装", "uv add openvfs", attrs={"id": "install", "class": "guide"})
doc.update_cell("@id=install", "uv add openvfs\nuv add py-key-value-aio")

cell = doc.find_cell("@id=install")
content = file.read()
```

## 直接导入 Store

```python
from openvfs import MemoryStore, OpenVfs

store = MemoryStore()
myvfs = OpenVfs.init_vfs(store=store)
```

可选后端示例：

```python
from openvfs import OpenVfs, S3Store

store = S3Store(
    bucket_name="my-bucket",
    endpoint_url="https://tos-s3-cn-beijing.volces.com",
    aws_access_key_id="your-ak",
    aws_secret_access_key="your-sk",
)
myvfs = OpenVfs.init_vfs(store=store)
```

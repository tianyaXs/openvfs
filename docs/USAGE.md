# OpenVFS 使用说明（V2）

本文档包含两部分：

- 最新推荐用法（V2）
- 旧版到新版的迁移对照

## 一、V2 核心模型

V2 统一为三层对象路径：

1. `OpenVfs`：系统入口
2. `VfsFile`：文件对象（通过 `find_file` 获取）
3. `MarkdownDocument`：Markdown 视图（通过 `file.as_markdown()` 获取）

Cell 操作统一在 `MarkdownDocument` 上进行：

- `add_cell(...)`
- `find_cell(...)`
- `list_cell()`
- `update_cell(...)`

## 二、Store 配置与导入（S3/Redis/Memory）

OpenVFS 支持注入自定义 store：

```python
from openvfs import OpenVfs

vfs = OpenVfs.init_vfs(store=store)
```

如果不传 `store`，默认使用 `MemoryStore`。

### 1) MemoryStore（默认，适合本地开发）

```python
from openvfs import MemoryStore, OpenVfs

store = MemoryStore(max_entries=1000, prefix="")
vfs = OpenVfs.init_vfs(store=store)
```

参数说明：

- `max_entries`：最大缓存条目数，`None` 表示不限制
- `prefix`：对象 key 前缀（用于隔离不同业务空间）

### 2) RedisStore（适合共享状态）

```python
from openvfs import OpenVfs, RedisStore

store = RedisStore(
    redis_url="redis://127.0.0.1:6379/0",
    prefix="openvfs",
)
vfs = OpenVfs.init_vfs(store=store)
```

常用参数（透传到底层 Redis store）：

- `redis_url`：Redis 连接串
- `prefix`：key 前缀

### 3) S3Store（AWS S3 / TOS / MinIO）

`S3Store` 构造参数会透传到底层 S3 实现，最常用的是：

- `bucket_name`
- `region_name`
- `endpoint_url`
- `aws_access_key_id`
- `aws_secret_access_key`
- `prefix`

#### 3.1 AWS S3 示例

```python
from openvfs import OpenVfs, S3Store

store = S3Store(
    bucket_name="my-bucket",
    region_name="ap-southeast-1",
    endpoint_url="https://s3.ap-southeast-1.amazonaws.com",
    aws_access_key_id="your-ak",
    aws_secret_access_key="your-sk",
    prefix="openvfs",
)
vfs = OpenVfs.init_vfs(store=store)
```

#### 3.2 火山引擎 TOS（S3 兼容）示例

```python
from openvfs import OpenVfs, S3Store

store = S3Store(
    bucket_name="my-bucket",
    region_name="cn-beijing",
    endpoint_url="https://tos-s3-cn-beijing.volces.com",
    aws_access_key_id="your-ak",
    aws_secret_access_key="your-sk",
    prefix="openvfs",
)
vfs = OpenVfs.init_vfs(store=store)
```

#### 3.3 MinIO 示例

```python
from openvfs import OpenVfs, S3Store

store = S3Store(
    bucket_name="openvfs",
    region_name="us-east-1",
    endpoint_url="http://127.0.0.1:9000",
    aws_access_key_id="root",
    aws_secret_access_key="password",
    prefix="openvfs",
)
vfs = OpenVfs.init_vfs(store=store)
```

当你使用 MinIO 时：

- `endpoint_url` 用 `http://` 或 `https://` 明确协议
- `bucket_name` 需要提前存在（或由你的运维流程创建）
- 推荐显式设置 `region_name`

### 4) 使用环境变量组织配置（推荐）

```python
import os

from openvfs import OpenVfs, S3Store

store = S3Store(
    bucket_name=os.environ["S3_BUCKET_NAME"],
    region_name=os.environ.get("S3_REGION_NAME", "us-east-1"),
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    prefix=os.environ.get("OPENVFS_PREFIX", "openvfs"),
)
vfs = OpenVfs.init_vfs(store=store)
```

### 5) 如何确认 store 生效

```python
file = vfs.find_file("resources/store-check/readme", must_exist=False)
if file is None:
    raise RuntimeError("无法创建文件对象")

file.create("# Store Check\n")
doc = file.as_markdown()
doc.add_cell("验证", "store 已生效", attrs={"id": "verify"})
cell = doc.find_cell("@id=verify")
print(cell.read())
```

## 三、最新常用用法

### 1) 初始化

```python
from openvfs import OpenVfs

vfs = OpenVfs.init_vfs()
```

### 2) 定位文件对象（find_file）

```python
file = vfs.find_file("resources/project/readme", must_exist=False)
if file is None:
    raise RuntimeError("无法创建文件对象")

# 首次创建文件内容
file.create("# 文档标题\n")

# 读取原始 markdown 文本
raw = file.read()
```

说明：

- `must_exist=True`：文件不存在时返回 `None`
- `must_exist=False`：总是返回文件对象（可后续创建）

### 3) 转为 Markdown 视图（as_markdown）

```python
doc = file.as_markdown()
```

### 4) 新增 Cell（add_cell）

```python
doc.add_cell("安装", "uv add openvfs", attrs={"id": "install", "class": "guide"})
doc.add_cell("FAQ", "默认后端是 MemoryStore", attrs={"id": "faq", "class": "guide"})
```

### 5) 查询 Cell（find_cell）

`find_cell` 是唯一查询入口。

选择器语法：

- 单条件：`@id=one`
- 多条件（AND）：`@@class=p_cls@@text()=第三行`

```python
# 单条件，默认 expect="one"
cell = doc.find_cell("@id=install")

# 多条件 AND 查询
cell2 = doc.find_cell("@@class=guide@@text()=FAQ")

# 获取多个结果
cells = doc.find_cell("@@class=guide", expect="many")

# 最多一个结果
maybe_cell = doc.find_cell("@id=missing", expect="zero_or_one")
```

`expect` 语义：

- `one`：必须命中 1 个，否则抛异常
- `zero_or_one`：0 个返回 `None`，超过 1 个抛异常
- `many`：返回 `list[Cell]`

### 6) 列举 Cell（list_cell）

```python
all_cells = doc.list_cell()
for cell in all_cells:
    print(cell.title, cell.attrs)
```

### 7) 更新 Cell（update_cell）

`update_cell` 会替换命中 cell 的正文内容（不改标题和 attrs），并复用 `expect` 语义。

```python
# 精确更新一个 cell（推荐按 id）
updated = doc.update_cell("@id=install", "uv add openvfs\nuv add py-key-value-aio")

# 最多一个：未命中返回 None
maybe_cell = doc.update_cell("@id=missing", "noop", expect="zero_or_one")

# 批量更新：命中多个时全部更新
updated_cells = doc.update_cell("@@class=guide", "统一说明", expect="many")
```

`expect` 语义：

- `one`：必须命中 1 个，否则抛异常
- `zero_or_one`：0 个返回 `None`，超过 1 个抛异常
- `many`：允许 0..N 个，返回 `list[Cell]`

### 8) 门面层快捷调用（可选）

```python
vfs.add_cell("resources/project/readme", "安装", "uv add openvfs", attrs={"id": "install"})
cell = vfs.find_cell("resources/project/readme", "@id=install")
updated = vfs.update_cell("resources/project/readme", "@id=install", "uv add openvfs\nuv add py-key-value-aio")
cells = vfs.list_cell("resources/project/readme")
```

### 9) 目录能力

```python
vfs.create_folder("openvfs://resources/project")
items = vfs.list("openvfs://resources")
tree = vfs.tree("openvfs://resources", max_depth=3)
```

## 四、迁移指南（旧版 -> V2）

### [重要] 兼容策略

当前版本按 V2 定义收敛，建议直接迁移到新接口，不再继续扩展旧命名方式。

### 1) 典型迁移对照

| 旧写法 | 新写法（V2） |
|---|---|
| `vfs.document(uri)` | `vfs.find_file(path).as_markdown()` |
| `get_section_by_id(uri, id)` | `find_cell("@id=...")` |
| `get_section_by_field(uri, field, value)` | `find_cell("@@field=value", expect="many")` 或更具体条件 |
| `get_section_by_ref(uri, ref)` | `find_cell(selector)` |
| `list_sections_by_field(uri, field)` | `list_cell()` + 调用侧筛选，或 `find_cell(..., expect="many")` |
| `set_section_by_id(...)` | `add_cell(..., attrs={"id": ...})` |
| `set_section_by_field(...)` | `add_cell(..., attrs={field: value})` |

### 2) 代码迁移示例

旧代码：

```python
uri = "openvfs://resources/project/readme.md"
vfs.set_section_by_id(uri, "install", "安装", "uv add openvfs", level=2)
text = vfs.get_section_by_id(uri, "install")
```

新代码：

```python
file = vfs.find_file("resources/project/readme", must_exist=False)
if file is None:
    raise RuntimeError("无法创建文件对象")

if not file.exists():
    file.create("# 项目文档\n")

doc = file.as_markdown()
doc.add_cell("安装", "uv add openvfs", level=2, attrs={"id": "install"})
cell = doc.find_cell("@id=install")
text = cell.read()
```

### 3) 选择器建议

- 推荐优先给 cell 设置稳定 `id`
- 精确命中优先使用 `@id=...`
- 组合查询使用 `@@...@@...`
- 值中包含 `@@` 时请使用引号，如：`@id="one@@two"`

## 五、建议的落地顺序

1. 先把“文档对象入口”统一为 `find_file(...).as_markdown()`
2. 把查询逻辑统一替换为 `find_cell(...)`
3. 再迁移新增逻辑到 `add_cell(...)`
4. 最后清理旧版调用与旧文档示例

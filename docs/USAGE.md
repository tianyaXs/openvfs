# OpenVFS 使用说明

面向 AI Agent 的 Markdown 虚拟文件系统，基于火山云 TOS 存储。支持链式 API、URI 规范访问、按标题属性定位段落。

---

## 目录

- [概述](#概述)
- [安装](#安装)
- [配置](#配置)
  - [凭证](#凭证)
  - [客户端初始化](#客户端初始化)
  - [命名空间与路径](#命名空间与路径)
- [URI 规范](#uri-规范)
- [链式 API（推荐）](#链式-api推荐)
  - [创建文档与块](#创建文档与块)
  - [内容类型与块属性](#内容类型与块属性)
  - [链式读取与按属性获取](#链式读取与按属性获取)
  - [通用方法组合任意格式](#通用方法组合任意格式)
- [文件操作（CRUD）](#文件操作crud)
- [标题与内容操作](#标题与内容操作)
  - [添加标题](#添加标题)
  - [添加标题及内容](#添加标题及内容)
  - [在指定标题下插入](#在指定标题下插入)
  - [替换与追加](#替换与追加)
- [按字段/值操作](#按字段值操作)
  - [设置段落](#设置段落)
  - [获取段落](#获取段落)
  - [列举带属性段落](#列举带属性段落)
- [按标题获取内容](#按标题获取内容)
- [文档结构](#文档结构)
- [完整示例](#完整示例)
- [异常处理](#异常处理)

---

## 概述

OpenVFS 将 Markdown 文件组织为虚拟文件系统，通过 `openvfs://` URI 访问。提供：

- **CRUD**：创建、读取、更新、删除 `.md` 文件
- **链式 API**：`path → doc → heading → block → write`，支持 text/code/json/link 等块类型
- **按属性定位**：标题属性 `{#id=install}`，可 `get_block(id="install")`、`get_section_by_id` 等
- **可配置命名空间**：默认 `resources` / `user` / `agent`，可自定义或关闭限制

存储后端为火山云 TOS，凭证通过环境变量或 `~/.openvfs/config.json` 配置。

---

## 安装

```bash
pip install openvfs
```

或使用 [uv](https://github.com/astral-sh/uv)：

```bash
uv add openvfs
```

---

## 配置

### 凭证

**方式一：环境变量**

```bash
export TOS_ACCESS_KEY=your-access-key-id
export TOS_SECRET_KEY=your-secret-access-key
```

**方式二：项目根目录 `.env`**

```env
TOS_ACCESS_KEY=your-access-key-id
TOS_SECRET_KEY=your-secret-access-key
```

**方式三：配置文件 `~/.openvfs/config.json`**

```json
{
  "storage": {
    "bucket": "openvfs",
    "prefix": "",
    "endpoint": "tos-cn-beijing.volces.com",
    "region": "cn-beijing"
  }
}
```

凭证仍通过环境变量 `TOS_ACCESS_KEY`、`TOS_SECRET_KEY` 注入；配置文件用于 bucket、endpoint、region、prefix 等。

可选环境变量覆盖：`OPENVFS_BUCKET`、`OPENVFS_PREFIX`、`OPENVFS_ENDPOINT`、`OPENVFS_REGION`。

### 客户端初始化

```python
from openvfs import MindMarkClient

# 使用默认配置（环境变量 / ~/.openvfs/config.json）
client = MindMarkClient()

# 显式指定存储参数
client = MindMarkClient(
    bucket="openvfs",
    endpoint="tos-cn-beijing.volces.com",
    region="cn-beijing",
)
```

### 命名空间与路径

路径首段（命名空间）可配置：

- **默认**：`namespaces=["resources", "user", "agent"]`，仅允许这三种首段
- **自定义**：如 `["docs", "app"]`，仅允许这些首段
- **不限制**：`namespaces=[]`，任意路径合法，如 `openvfs://any/folder/doc.md`

```python
client = MindMarkClient(namespaces=["resources", "user", "agent"])  # 默认
client = MindMarkClient(namespaces=[])  # 不限制
```

配置文件示例（`~/.openvfs/config.json`）：

```json
{
  "storage": { "bucket": "openvfs", "endpoint": "...", "region": "..." },
  "structure": {
    "namespaces": []
  }
}
```

---

## URI 规范

- **格式**：`openvfs://{path}`，`path` 是否限制首段由 `namespaces` 决定
- **默认**：首段须为 `resources`、`user`、`agent` 之一
- **示例**：
  - `openvfs://resources/project/readme.md`
  - `openvfs://agent/skills/search_code.md`
  - `namespaces=[]` 时：`openvfs://any/folder/doc.md`

---

## 链式 API（推荐）

设计参考 [DrissionPage](https://drissionpage.cn/)：链式调用，从路径到文档到标题到块，最后写入。

### 创建文档与块

```python
(client
  .path("resources", "my_project")
  .doc("readme.md")
  .heading("安装", level=2, id="install")
  .block("pip install openvfs", type="code", lang="bash")
  .heading("API", level=2, id="api")
  .block('{"get": true}', type="json")
  .link("https://example.com", text="示例")
  .write())
```

### 内容类型与块属性

| 方法 | 说明 | 存储形式 |
|------|------|----------|
| `.block(content, type="text", **attrs)` | 通用块 | 段落 |
| `.text(content, **attrs)` | 文本块 | 段落 |
| `.block(content, type="code", lang="bash", **attrs)` | 代码块 | \`\`\`bash ... \`\`\` |
| `.code(content, lang="", **attrs)` | 代码块 | 同上 |
| `.block(content, type="json", **attrs)` | JSON 块 | \`\`\`json ... \`\`\` |
| `.json_block(content, **attrs)` | JSON 块 | 同上 |
| `.block(url, type="link", link_text="x", **attrs)` | 链接 | [text](url) |
| `.link(url, text=None, **attrs)` | 链接 | 同上 |

块属性 `**attrs` 会写入块前 HTML 注释 `<!-- {k=v} -->`，便于按属性定位。

### 链式读取与按属性获取

```python
# 读取全文
content = client.path("resources", "my_project").doc("readme.md").read()

# 按单属性获取（如 id=install）
block = client.path("resources", "my_project").doc("readme.md").get_block(id="install")

# 多属性匹配
block = client.path("resources", "my_project").doc("readme.md").get_block(
    type="work_report", from_agent="task_executor"
)

# 按属性层级下钻
content = client.path("resources", "my_project").doc("readme.md").get_by_hierarchy(
    "id=install", "id=step1"
)

# 列举带某属性的段落后再 get_block
items = client.path("resources", "my_project").doc("readme.md").list_blocks(field="msg_id")
```

属性名为 Python 关键字时用字典传入，例如：`.get_block(type="work_report", **{"from": "task_executor"})`。

### 通用方法组合任意格式

不提供针对某种文档结构的专用方法，只提供通用能力：**标题（含层级属性）+ 内容块（text/code/json/link）**。目标格式由调用方组合。

例如构建「文档头元数据 + 多条消息块」的 TASK 式结构：

```python
ch = client.path("agent", "tasks").doc("TASK.md")

ch.heading("TASK", level=1)
ch.text("- task_id: 1772165762941\n- mode: append-only\n- description: 多Agent协作群聊记录")

ch.heading("MSG 2026-02-27T12:16:04+08:00 | d16bcdea87", level=2,
           msg_id="d16bcdea87", task_id="1772165762941", type="work_report",
           **{"from": "task_executor_agent", "to": "task_dispatcher_agent"})
ch.text("- task_id: 1772165762941\n- from: task_executor_agent\n- to: task_dispatcher_agent")
ch.heading("TEXT", level=3)
ch.text("@task_dispatcher_agent 任务编号: T-FINAL，播报完成。")

ch.write()
```

检索时属性名与构建时一致即可：

```python
body = client.path("agent", "tasks").doc("TASK.md").get_block(msg_id="d16bcdea87")
body = client.path("agent", "tasks").doc("TASK.md").get_block(
    type="work_report", **{"from": "task_executor_agent"}
)
```

---

## 文件操作（CRUD）

| 方法 | 说明 |
|------|------|
| `create(uri, content)` | 创建 .md 文件 |
| `read(uri)` | 读取完整内容 |
| `update(uri, content)` | 全量覆盖更新 |
| `delete(uri)` | 删除文件 |
| `exists(uri)` | 检查是否存在 |

```python
client.create("openvfs://resources/project/readme.md", "# 标题\n\n内容")
content = client.read("openvfs://resources/project/readme.md")
client.update("openvfs://resources/project/readme.md", "新内容")
client.delete("openvfs://resources/project/readme.md")
```

---

## 标题与内容操作

### 添加标题

```python
client.add_heading(uri, "安装步骤", level=2)
client.add_heading(uri, "安装", level=2, attrs={"id": "install"})  # ## 安装 {#id=install}
```

### 添加标题及内容

```python
client.add_heading_with_content(
    uri,
    "项目简介",
    "OpenVFS 是 Agent 专用文件系统。",
    level=1,
)
```

### 在指定标题下插入

```python
client.insert_under_heading(uri, "安装步骤", "pip install openvfs")
```

### 替换与追加

```python
client.replace_heading_content(uri, "安装步骤", "新内容...")
client.append(uri, "## 附录\n\n更多说明...")
```

---

## 按字段/值操作

通过标题属性 `{#field=value}` 定位段落，类似按字段查询。

### 设置段落

```python
# 按 id 设置（存在则更新，不存在则追加）
client.set_section_by_id(
    uri,
    section_id="install",
    heading_text="安装步骤",
    section_content="pip install openvfs",
    level=2,
)

# 按 field=value 设置
client.set_section_by_field(
    uri,
    field="category",
    value="guide",
    heading_text="使用指南",
    section_content="见 README",
    level=2,
)
```

生成示例：

```markdown
## 安装步骤 {#id=install}
pip install openvfs

## 使用指南 {#category=guide}
见 README
```

### 获取段落

```python
content = client.get_section_by_id(uri, "install")
content = client.get_section_by_field(uri, "category", "guide")
```

多属性匹配（如 `get_section_by_ref`）见客户端方法文档。

### 列举带属性段落

```python
sections = client.list_sections_by_field(uri)
# [{"field": "id", "value": "install", "heading": "安装步骤", "level": 2}, ...]

sections = client.list_sections_by_field(uri, field="id")
```

---

## 按标题获取内容

```python
content = client.get_section(uri, "安装步骤")

# 带上下文（标题及前后若干行）
ctx = client.get_heading_with_context(
    uri,
    heading_ref={"id": "install"},  # 或标题文本 "安装步骤"
    before=2,
    after=3,
    include_heading=True,
)
```

---

## 文档结构

```python
headings = client.get_headings(uri)
# [{"level": 1, "text": "项目", "line_start": 1, "attrs": {}}, ...]

items = client.list("openvfs://resources/project/")   # ['readme.md', 'docs/']

tree = client.tree("openvfs://resources/")
# openvfs://resources
# ├── project/
# │   ├── readme.md
# │   └── docs/
# └── ...
```

---

## 完整示例

```python
from openvfs import MindMarkClient

client = MindMarkClient()
uri = "openvfs://resources/project/readme.md"

client.create(uri, "# 项目说明\n\n简介内容。")
client.set_section_by_id(uri, "install", "安装", "pip install openvfs", level=2)
client.set_section_by_id(uri, "usage", "使用", "from openvfs import MindMarkClient", level=2)
client.append(uri, "## 附录\n更多内容。")

install_content = client.get_section_by_id(uri, "install")
ctx = client.get_heading_with_context(uri, {"id": "install"}, before=1, after=2)
```

---

## 异常处理

```python
from openvfs import MindMarkClient, NotFoundError, InvalidURIError

try:
    content = client.read("openvfs://resources/notfound.md")
except NotFoundError as e:
    print(f"未找到: {e.uri}")
except InvalidURIError as e:
    print(f"无效 URI: {e.uri}")
```

---

**相关文档**：[设计方案](DESIGN.md) | [README](../README.md)

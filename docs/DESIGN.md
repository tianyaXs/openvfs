# OpenVFS 设计方案

## Agent 专用 Markdown 文件系统

---

## 一、项目概述

### 1.1 目标与定位

**OpenVFS** 是一个面向 AI Agent 的专用 Markdown 文件系统，以 `.md` 文件为核心载体，提供存储、更新、查询、删除等完整 CRUD 能力。项目将发布至 PyPI，供其他系统以 Python 包形式直接引用。

**核心差异化**：
- 纯 Markdown 原生，无向量化、无模型配置、无语义检索，轻量可嵌入
- 围绕 Agent 工作流设计：结构化目录、可编程格式操作、确定性路径访问
- 云端持久化：基于火山云对象存储 (TOS) 落地，支持分布式与高可用

### 1.2 设计参考

设计理念参考 [OpenViking](https://github.com/volcengine/OpenViking) 的以下部分（不包含向量化、模型、检索）：

| OpenViking 概念 | OpenVFS 采用 | 说明 |
|----------------|---------------|------|
| 文件系统范式 | ✓ | 虚拟目录 + URI 统一访问 |
| 分层结构 | ✓（简化） | 目录/文件两级，无 L0/L1/L2 语义层 |
| 可观测性 | ✓ | 操作轨迹、路径可追溯 |
| 向量/Embedding | ✗ | 不涉及 |
| 语义检索 | ✗ | 不涉及 |
| VLM/模型配置 | ✗ | 不涉及 |

---

## 二、核心概念

### 2.1 虚拟文件系统范式

将 Agent 的知识与文档统一抽象为虚拟文件系统，通过 `openvfs://` 协议访问。每个对象对应唯一 URI。

```
openvfs://
├── resources/              # 资源：项目文档、参考资料等
│   ├── my_project/
│   │   ├── docs/
│   │   │   ├── api.md
│   │   │   └── tutorial.md
│   │   └── notes/
│   │       └── meeting_001.md
│   └── ...
├── user/                   # 用户：偏好、习惯等
│   └── preferences/
│       └── writing_style.md
└── agent/                  # Agent：技能、指令、任务记忆等
    ├── skills/
    │   ├── search_code.md
    │   └── analyze_data.md
    ├── memories/
    └── instructions/
```

### 2.2 URI 规范

- **格式**：`openvfs://{namespace}/{path}`
- **示例**：
  - `openvfs://resources/my_project/docs/api.md`
  - `openvfs://agent/skills/search_code.md`
- **命名空间**：`resources`、`user`、`agent`（可扩展）

### 2.3 对象键映射

TOS 中对象键与 URI 的映射规则：

- URI: `openvfs://resources/project/docs/api.md`
- TOS Key: `{bucket_prefix}/resources/project/docs/api.md`

通过固定前缀区分不同项目/租户，支持多租户隔离。

---

## 三、存储层设计（火山云 TOS）

### 3.1 依赖

- 火山云对象存储 Python SDK：`tos`
- 文档：[安装](https://www.volcengine.com/docs/6349/93479) · [初始化](https://www.volcengine.com/docs/6349/93483) · [快速入门](https://www.volcengine.com/docs/6349/92786) · [普通上传](https://www.volcengine.com/docs/6349/92800)

### 3.2 存储模型

| 概念 | TOS 对应 | 说明 |
|------|----------|------|
| 桶 (Bucket) | 1 个专用桶 | 存储所有 OpenVFS 文件 |
| 对象 (Object) | `.md` 文件 | Key = `{prefix}/{uri_path}` |
| 目录 | 无真实目录 | 通过 Key 前缀模拟，如 `resources/project/docs/` |
| 列举 | `list_objects` | 通过 `prefix` 实现目录列举 |

### 3.3 客户端初始化

```python
import tos

client = tos.TosClientV2(
    ak=os.getenv("TOS_ACCESS_KEY"),
    sk=os.getenv("TOS_SECRET_KEY"),
    endpoint="tos-cn-beijing.volces.com",  # 按地域配置
    region="cn-beijing"
)
```

### 3.4 基础操作映射

| 操作 | TOS API | 说明 |
|------|---------|------|
| 上传 | `put_object` / `put_object_from_file` | 存储/更新 .md 内容 |
| 下载 | `get_object` | 读取 .md 内容 |
| 列举 | `list_objects` | 按 prefix 列举「目录」下对象 |
| 删除 | `delete_object` | 删除单个 .md 文件 |
| 存在性 | `head_object` | 判断文件是否存在 |

---

## 四、Markdown 文件操作设计

### 4.1 CRUD API 概览

| 操作 | 方法 | 说明 |
|------|------|------|
| 创建 | `create(uri, content)` | 新建 .md 文件 |
| 读取 | `read(uri)` | 获取完整内容 |
| 更新 | `update(uri, content)` | 全量覆盖 |
| 删除 | `delete(uri)` | 删除文件 |
| 列举 | `list(uri)` | 列举目录下文件/子目录 |
| 存在 | `exists(uri)` | 检查 URI 是否存在 |

### 4.2 结构化格式操作（一级/二级标题等）

支持对已有 .md 内容做结构化编辑，而不必每次都全量读写。

#### 4.2.1 标题层级模型

Markdown 标题与层级：

- `#` → 一级 (h1)
- `##` → 二级 (h2)
- `###` → 三级 (h3)
- … 以此类推

#### 4.2.2 格式操作 API

| 操作 | 方法 | 说明 |
|------|------|------|
| 添加一级标题 | `add_heading(uri, text, level=1)` | 在文档末尾或指定位置插入 |
| 添加二级标题 | `add_heading(uri, text, level=2)` | 同上 |
| 在标题下插入内容 | `insert_under_heading(uri, heading_text, content)` | 在指定标题下插入段落 |
| 追加段落 | `append(uri, content)` | 在文档末尾追加 |
| 替换标题内容 | `replace_heading_content(uri, heading_text, new_content)` | 替换某标题下内容 |
| 获取标题列表 | `get_headings(uri)` | 返回所有标题及层级 |
| 按标题切片 | `get_section(uri, heading_text)` | 获取某标题下的内容块 |

#### 4.2.3 实现思路

- 使用 `mistune` 或正则解析 Markdown AST
- 维护标题到行号的映射，支持精确定位插入/替换
- 支持「在某个标题之后」插入新标题或内容

### 4.3 查询能力

不做向量检索，仅做「路径 + 文本」查询：

| 能力 | 说明 |
|------|------|
| 路径查询 | 通过 URI 精确访问 |
| 目录树 | `tree(uri)` 输出目录结构 |
| 关键词匹配 | `grep(uri, pattern)` 在指定文件或目录下做全文匹配（可选） |

---

## 五、配置设计

### 5.1 配置方式

- 环境变量
- 配置文件 `~/.openvfs/config.json`（可选）
- 代码内显式传参

### 5.2 配置项

```json
{
  "storage": {
    "provider": "tos",
    "bucket": "openvfs-bucket",
    "prefix": "openvfs/",
    "endpoint": "tos-cn-beijing.volces.com",
    "region": "cn-beijing"
  },
  "credentials": {
    "ak_env": "TOS_ACCESS_KEY",
    "sk_env": "TOS_SECRET_KEY"
  },
  "log": {
    "level": "INFO",
    "output": "stdout"
  }
}
```

> AK/SK 不建议写入配置文件，应通过环境变量注入。

---

## 六、包结构与 PyPI 发布

### 6.1 包结构

```
openvfs/
├── pyproject.toml
├── README.md
├── openvfs/
│   ├── __init__.py
│   ├── bootstrap.py       # 初始化入口
│   ├── vfs/               # VFS 领域模型与门面
│   ├── uri.py             # URI 解析与校验
│   ├── stores/
│   │   ├── __init__.py
│   │   ├── base.py        # BaseStore 抽象
│   │   └── tos.py         # TOS 实现
│   ├── filetypes/
│   │   ├── __init__.py
│   │   ├── parser.py      # 标题解析
│   │   └── editor.py      # 格式操作（add_heading 等）
│   └── config.py          # 配置加载
├── tests/
│   ├── test_client.py
│   ├── test_uri.py
│   └── test_markdown.py
└── docs/
    └── DESIGN.md
```

### 6.2 使用方式

```python
from openvfs import OpenVFS

# 初始化（自动从环境变量/配置文件加载）
client = OpenVFS()

# 或显式配置
client = OpenVFS(
    bucket="my-bucket",
    prefix="agent-docs/",
    endpoint="tos-cn-beijing.volces.com",
    region="cn-beijing"
)

# CRUD
client.create("openvfs://resources/project/readme.md", "# 项目说明\n\n...")
content = client.read("openvfs://resources/project/readme.md")
client.update("openvfs://resources/project/readme.md", new_content)
client.delete("openvfs://resources/project/readme.md")

# 格式操作
client.add_heading("openvfs://resources/project/readme.md", "安装步骤", level=2)
client.insert_under_heading("openvfs://resources/project/readme.md", "安装步骤", "pip install openvfs")

# 列举与树形结构
items = client.list("openvfs://resources/")
tree = client.tree("openvfs://resources/project/")
```

### 6.3 PyPI 发布

- 包名：`openvfs`
- 依赖：`tos`（火山云 SDK）
- 支持 Python 3.10+
- 使用 `build` + `twine` 发布

---

## 七、可观测性

### 7.1 操作轨迹

- 记录每次读/写/删的 URI、时间戳、操作类型
- 可选：输出为日志或结构化事件，便于调试与审计

### 7.2 错误与异常

- 统一异常类型：`MindMarkError`（OpenVFS 基础异常）、`NotFoundError`、`StorageError`
- 保留 TOS 原始 `request_id`，便于与火山云侧排查

---

## 八、实施阶段建议

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| Phase 1 | TOS 存储层封装、URI 解析、基础 CRUD | P0 |
| Phase 2 | MD 文件类型解析与标题操作（add_heading、insert_under_heading） | P0 |
| Phase 3 | list/tree、grep、配置与异常体系 | P1 |
| Phase 4 | 完善测试、文档、PyPI 发布 | P1 |

---

## 九、参考资料

- [OpenViking GitHub](https://github.com/volcengine/OpenViking)
- [火山云 TOS Python SDK 安装](https://www.volcengine.com/docs/6349/93479?lang=zh)
- [火山云 TOS Python SDK 初始化](https://www.volcengine.com/docs/6349/93483?lang=zh)
- [火山云 TOS Python SDK 快速入门](https://www.volcengine.com/docs/6349/92786?lang=zh)
- [火山云 TOS 普通上传](https://www.volcengine.com/docs/6349/92800?lang=zh)

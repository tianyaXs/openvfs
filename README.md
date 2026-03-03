# OpenVFS

Agent 专用 Markdown 文件系统，基于火山云 TOS 存储。支持按字段/值快速定位段落，类似数据库按字段查询。

## 安装

```bash
pip install openvfs
```

## 配置

环境变量或项目根目录 `.env`：

```bash
TOS_ACCESS_KEY=your-access-key-id
TOS_SECRET_KEY=your-secret-access-key
```

## 快速示例

**链式 API（推荐）**：

```python
from openvfs import MindMarkClient

client = MindMarkClient()

# 创建资源路径 → 文档 → 标题 → 内容块（支持 text/code/json/link）→ 写入
(client
  .path("resources", "project")
  .doc("readme.md")
  .heading("安装", level=2, id="install")
  .block("pip install openvfs", type="code", lang="bash")
  .heading("链接", level=2)
  .link("https://example.com", "示例")
  .write())

# 按属性获取
content = client.path("resources", "project").doc("readme.md").get_block(id="install")
```

**传统 API**：`create` / `read` / `set_section_by_id` / `get_section_by_id` 等，见 [使用说明](docs/USAGE.md)。

## 文档

- **[使用说明 (docs/USAGE.md)](docs/USAGE.md)**：完整 API 与用法
- [设计方案 (docs/DESIGN.md)](docs/DESIGN.md)：架构与设计
- [发布到 PyPI (docs/PUBLISHING.md)](docs/PUBLISHING.md)：构建与上传说明

## URI 规范

- 格式：`openvfs://{namespace}/{path}`
- 命名空间：`resources`、`user`、`agent`
- 示例：`openvfs://resources/my_project/docs/api.md`

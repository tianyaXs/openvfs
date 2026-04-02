# OpenVFS 重构与完善方案

## 目标

本方案用于推进 OpenVFS 的大范围设计完善，聚焦以下三件事：

1. 主类命名与对外入口统一。
2. 核心对象模型按职责重新整理。
3. 明确虚拟文件系统管理设计与 Markdown 管理设计的边界与协作方式。

该方案优先解决概念混杂问题，不通过兼容补丁掩盖结构缺陷。

---

## 一、主类命名方案

### 1.1 现状问题

当前主入口类为 `MindMarkClient`，但项目名称为 `openvfs`。

现状存在以下问题：

- 名称与项目品牌不一致。
- `MindMark` 偏业务化，不适合作为基础设施层长期抽象。
- `Client` 无法体现其同时承担 VFS 门面和 Markdown 管理入口的角色。

### 1.2 建议命名

建议将主入口类统一命名为：`OpenVFS`

保留以下命名策略：

- 对外主入口：`OpenVFS`
- 链式构建器：`DocumentBuilder`
- 文件对象：`VfsDocument`
- 目录对象：`VfsDirectory`

### 1.3 命名决策理由

- `OpenVFS` 与包名一致，认知成本最低。
- 该名称适合作为 façade（门面）对象。
- 后续若引入更多实现对象，不会再次触发命名漂移。

### 1.4 迁移顺序

#### Phase A：文档与方案统一
- 所有设计文档先统一使用 `OpenVFS`。

#### Phase B：代码层改名
- 在 `src/openvfs` 中将 `MindMarkClient` 改为 `OpenVFS`。
- 更新 `__init__.py` 导出。
- 更新 README 与测试示例。

#### Phase C：清理历史命名
- 删除 `MindMarkClient` 残留引用。
- 校验版本、注释、示例文本一致性。

---

## 二、对象设计整理

建议将系统对象划分为四层：

1. 系统入口层
2. 虚拟文件系统层
3. Markdown 结构层
4. 存储抽象层

### 2.1 系统入口层

#### `OpenVFS`
职责：

- 加载配置
- 初始化存储后端
- 提供文档与目录入口
- 提供高频便捷 API

不再承担：

- 具体 Markdown 段落编辑细节
- 标题查询算法实现
- 存储对象细节拼装逻辑之外的解析工作

### 2.2 虚拟文件系统层

#### `VfsUri`
职责：

- 解析 `openvfs://` URI
- 规范化 namespace 和 path
- 映射到对象存储 key

#### `VfsDirectory`
职责：

- 目录列举
- 目录树展示
- 逻辑目录遍历

#### `VfsDocument`
职责：

- 文档级 CRUD
- 文档存在性判断
- 将文档内容桥接到 Markdown 层

建议接口：

```python
doc = vfs.document("openvfs://resources/project/readme.md")
content = doc.read()
doc.write("# README")
markdown = doc.markdown()
```

### 2.3 Markdown 结构层

#### `MarkdownDocument`
职责：

- 持有文档文本
- 解析标题与块结构
- 提供查询与修改入口
- 渲染回 Markdown 字符串

#### `HeadingNode`
建议字段：

- `level`
- `text`
- `attrs`
- `line_start`
- `line_end`

#### `BlockNode`
建议字段：

- `type`
- `content`
- `attrs`
- `lang`
- `link_text`

#### `MarkdownEditor`
职责：

- 添加标题
- 插入内容块
- 替换段落
- 追加内容

#### `MarkdownQuery`
职责：

- 按 id 获取段落
- 按字段/值获取段落
- 按引用获取段落
- 按上下文提取片段
- 列举具备属性的段落

### 2.4 存储抽象层

#### `StorageBackend`
职责：

- 定义统一的对象存储接口

#### `TOSStorage`
职责：

- 落地火山云 TOS 访问
- 隐藏 SDK 细节

这一层保持稳定，不建议在本轮大改中扩散职责。

---

## 三、虚拟文件系统管理设计

### 3.1 设计目标

虚拟文件系统层解决的是“文档在哪里、如何被访问、如何映射到底层对象存储”的问题。

### 3.2 该层应负责的内容

- URI 解析与合法性校验
- namespace 约束
- 文件/目录路径表达
- `.md` 文件路径规范化
- 对象存储 key 映射
- 目录 list/tree 语义
- 存储后端切换能力

### 3.3 该层不应负责的内容

- 标题属性语法
- 文档段落插入与替换
- 内容块查询逻辑
- Markdown 结构解析

### 3.4 建议的 VFS API 形态

```python
vfs = OpenVFS()

directory = vfs.directory("openvfs://resources/project/")
items = directory.list()

doc = vfs.document("openvfs://resources/project/readme.md")
content = doc.read()
```

### 3.5 VFS 设计原则

- 路径语义优先于实现细节。
- 目录与文档对象分离，避免所有能力堆到入口类。
- URI 是统一身份标识，不直接暴露底层对象 key 给上层调用者。

---

## 四、Markdown 管理设计

### 4.1 设计目标

Markdown 管理层解决的是“文档内部如何组织、定位、修改”的问题。

### 4.2 该层应负责的内容

- 标题解析
- 标题属性解析
- 内容块格式化
- 块前属性注释解析
- 段落级查询
- 上下文提取
- 文档结构化更新

### 4.3 该层不应负责的内容

- bucket、endpoint、region
- namespace 策略
- 对象存储 list 与 tree
- URI 与 key 映射

### 4.4 关键设计判断

OpenVFS 当前并不是“任意 Markdown 通用编辑器”，而是“结构化 Markdown 文档管理器”。

这意味着：

- 核心模型是 `标题 + 内容块 + 属性`。
- “按字段/值查询段落”是主能力，不应被普通文本编辑语义稀释。
- 后续应围绕结构化查询和可预测修改增强，而不是扩展成通用 Markdown IDE。

### 4.5 Markdown API 建议

```python
markdown = doc.markdown()

section = markdown.query.get_by_id("install")
markdown.editor.set_section({"id": "install"}, "安装", "pip install openvfs")
doc.write(markdown.render())
```

### 4.6 Markdown 设计原则

- 结构化优先，避免语义漂移。
- 查询与编辑概念分离，防止一个对象无限膨胀。
- 文档模型保持纯内存对象，I/O 放在 VFS 层处理。

---

## 五、两套设计的边界与协作

### 5.1 一句话边界

- VFS 层负责定位“哪个文档”。
- Markdown 层负责定位“文档里的哪一段”。

### 5.2 协作关系

推荐通过 `VfsDocument` 连接两层：

```python
vfs = OpenVFS()
doc = vfs.document("openvfs://resources/project/readme.md")
markdown = doc.markdown()
section = markdown.query.get_by_field("id", "install")
doc.write(markdown.render())
```

### 5.3 不建议的做法

- 继续将所有 API 都直接堆在 `OpenVFS` 上。
- 在 Markdown 模块中直接处理 TOS 配置和对象 key。
- 将目录遍历逻辑和段落编辑逻辑混在同一对象里。

---

## 六、实施路线图

### Stage 1：命名统一

- 将 `MindMarkClient` 重命名为 `OpenVFS`
- 将 `DocChain` 重命名为 `DocumentBuilder`
- 修正文档、示例、测试中的历史命名

### Stage 2：对象拆分

- 新增 `VfsDocument` 与 `VfsDirectory`
- 将 list/tree 与文档 CRUD 从门面对象中迁移为明确对象职责
- 保留 `OpenVFS` 作为创建这些对象的工厂入口

### Stage 3：Markdown 模型收敛

- 增加 `MarkdownDocument`
- 将查询与编辑能力改为挂载在文档模型上
- 将现有 parser/editor 函数逐步收编为对象方法或内部实现

### Stage 4：接口收口

- 只保留少量高频 façade API
- 将结构化能力收敛到 `VfsDocument` 与 `MarkdownDocument`
- 清理历史别名与重复语义方法

---

## 七、建议优先级

### P0：必须先做

- 主类命名统一
- 文档层与 VFS 层职责边界固定
- 输出明确的对象分层方案

### P1：随后推进

- 显式引入 `VfsDocument` / `VfsDirectory`
- 显式引入 `MarkdownDocument`

### P2：按需推进

- 更细的节点模型
- 更丰富的 block 类型
- 更多存储后端实现

---

## 八、当前版本建议结论

针对当前代码库，建议你把 OpenVFS 的正式定位写成一句话：

**OpenVFS 是一个面向 Agent 的结构化 Markdown 虚拟文件系统：VFS 层负责文档定位与存储映射，Markdown 层负责文档内部结构化查询与修改。**

这句话可以作为 README、设计文档、后续重构的统一锚点。

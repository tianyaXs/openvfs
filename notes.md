# Notes: OpenVFS 现状调研

## Sources

### Source 1: `README.md`
- 位置：`README.md:1`
- 关键点：
  - 项目定位是 Agent 专用 Markdown 文件系统。
  - 底层依赖火山云 TOS。
  - 推荐链式 API，强调按属性定位段落。

### Source 2: `src/openvfs/client.py`
- 位置：`src/openvfs/client.py:30`
- 关键点：
  - `MindMarkClient` 作为主入口，承担配置、存储、URI 路由、CRUD、Markdown 查询/编辑。
  - 类职责过宽，是当前设计收敛的主要切入点。

### Source 3: `src/openvfs/chain.py`
- 位置：`src/openvfs/chain.py:50`
- 关键点：
  - `DocChain` 提供链式构建体验。
  - 本质是文档构建器，不应承担文件系统职责。

### Source 4: `src/openvfs/uri.py`
- 位置：`src/openvfs/uri.py:16`
- 关键点：
  - URI 解析与 object key 映射已经具备值对象雏形。
  - namespace 校验与 `.md` 规范化应继续保留在 VFS 层。

### Source 5: `src/openvfs/markdown/parser.py` 与 `src/openvfs/markdown/editor.py`
- 位置：`src/openvfs/markdown/parser.py:1`
- 位置：`src/openvfs/markdown/editor.py:1`
- 关键点：
  - Markdown 能力已经具备解析、插入、替换、按属性查询等基础能力。
  - 当前编辑与查询职责仍混合，后续应在概念上拆分。

### Source 6: `src/openvfs/storage/base.py` 与 `src/openvfs/storage/tos.py`
- 位置：`src/openvfs/storage/base.py:6`
- 位置：`src/openvfs/storage/tos.py:18`
- 关键点：
  - 存储抽象存在，底层仅有 TOS 实现。
  - 这层职责清晰，可作为稳定基础设施层保留。

## Synthesized Findings

### 命名问题
- `MindMarkClient` 与项目名 `openvfs` 不一致，削弱统一心智模型。
- `DocChain` 的行为更接近 `DocumentBuilder`，当前命名偏实现导向，不够语义化。

### 对象职责问题
- 主客户端耦合系统入口、VFS 路由、Markdown 管理、查询 API 封装。
- 文档对象与目录对象未显式建模，VFS 语义被弱化。
- Markdown 当前更像“结构化 Markdown DSL”，不是通用 Markdown AST 管理器。

### 边界问题
- VFS 层负责定位“哪个文档”。
- Markdown 层负责定位“文档里的哪一段”。
- 当前两层在 `MindMarkClient` 内交织，需要通过对象拆分恢复边界。

### 可行的演进方向
- 主入口类统一为 `OpenVFS`。
- 引入 `VfsDocument` / `VfsDirectory` 承接文件系统语义。
- 引入 `MarkdownDocument` / `MarkdownEditor` / `MarkdownQuery` 承接文档内部结构语义。
- `DocumentBuilder` 作为链式构建体验保留，但从系统入口中解耦。

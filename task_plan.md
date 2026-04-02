# Task Plan: OpenVFS 命名与架构完善

## Goal
为 OpenVFS 输出一套可执行的重构与完善计划，明确类命名、对象设计、虚拟文件系统管理设计、Markdown 管理设计的边界、阶段与落地路径。

## Phases
- [x] Phase 1: 计划建立与任务分解
- [x] Phase 2: 现状研究与问题归纳
- [x] Phase 3: 形成重构方案与迁移路径
- [x] Phase 4: 复核并交付文档
- [x] Phase 5: 执行第一阶段命名统一
- [x] Phase 6: 验证第一阶段改造
- [x] Phase 7: 拆分 VfsDocument 与 VfsDirectory
- [x] Phase 8: 接入门面委派并补测试
- [x] Phase 9: 重构可插拔 BaseStore 存储层
- [x] Phase 10: 解除 OpenVFS 对 TOS 的强绑定
- [x] Phase 11: 切换到 py-key-value-aio 默认存储
- [x] Phase 12: 增加 init_vfs 与薄适配导出
- [x] Phase 13: 目录结构重构到 vfs/filetypes/stores
- [x] Phase 14: 路径 API 重构为 cd_path/create_file/create_folder

## Decisions Made
- 用户日常使用不再暴露抽象 `path()`，改为显式动作：`cd_path()`、`create_file()`、`create_folder()`。
- 逻辑目录创建通过 `BaseStore.create_folder()` 下沉到底层存储适配层，以保证空目录也能被枚举。
- `mkdir()` 作为 `create_folder()` 的别名保留在门面层，便于内部调用。

## Errors Encountered
- `S3Store` 与 TOS 联通测试在 `HeadBucket` 阶段返回 403，暂未继续作为默认路径推进。
- `py-key-value-aio` 的异步 store 需要适配到同步 VFS，适配层已引入单独事件循环与目录索引记录。

## Status
**Completed (Current Iteration)** - 已完成 `cd_path/create_file/create_folder` API 重构，公开示例已同步，最小回归通过。下一步可继续设计 store factory 或异步入口。

# OpenVFS 目录结构

## 推荐结构

```text
src/openvfs/
├── __init__.py
├── __main__.py
├── bootstrap.py
├── exceptions.py
├── filetypes/
│   ├── __init__.py
│   └── md/
│       ├── __init__.py
│       ├── editor.py
│       └── parser.py
├── stores/
│   ├── __init__.py
│   ├── base.py
│   └── key_value_adapter.py
└── vfs/
    ├── __init__.py
    ├── builder.py
    ├── config.py
    ├── directory.py
    ├── document.py
    ├── facade.py
    └── uri.py
```

## 分层原则

- `bootstrap.py`：初始化入口，例如 `init_vfs()`
- `vfs/`：虚拟文件系统门面、目录对象、文档对象、URI 与配置
- `filetypes/md/`：MD 文件类型解析与编辑
- `stores/`：底层可插拔存储与适配层
- 包根目录只保留入口与异常定义

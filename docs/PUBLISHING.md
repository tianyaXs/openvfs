# 发布到 PyPI

## 发布前检查

1. **更新版本号**：在 `pyproject.toml` 中修改 `version = "x.y.z"`。
2. **填写项目链接**：将 `pyproject.toml` 中 `[project.urls]` 的 `your-username/openvfs` 改为你的仓库地址。
3. **（可选）作者信息**：在 `pyproject.toml` 的 `authors` 中填写姓名与邮箱。
4. **测试**：本地安装并跑测试：
   ```bash
   uv pip install -e ".[dev]"
   uv run pytest tests/ -v
   ```

## 构建

```bash
# 安装构建工具（若未安装）
uv pip install build

# 生成 sdist 与 wheel
uv run python -m build
```

产物在 `dist/` 目录：`openvfs-0.1.0.tar.gz`、`openvfs-0.1.0-py3-none-any.whl`。

## 上传到 PyPI

### 方式一：twine（推荐）

```bash
uv pip install twine

# 上传到 PyPI（正式）
uv run twine upload dist/*

# 或先上传到 TestPyPI 验证
uv run twine upload --repository testpypi dist/*
```

首次使用需在 [pypi.org](https://pypi.org) 注册账号，并配置 API Token。上传时按提示输入用户名和密码（用户名填 `__token__`，密码填 pypi 提供的 token）。

### 方式二：uv publish

若已安装 [uv](https://github.com/astral-sh/uv) 且配置好 PyPI token：

```bash
uv publish
```

## 发布后

- 用户安装：`pip install openvfs`
- 带开发依赖安装（本地开发）：`pip install openvfs[dev]`

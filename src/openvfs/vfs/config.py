"""配置加载。"""

import json
import os
from pathlib import Path
from typing import Any


def _config_path() -> Path:
    return Path.home() / ".openvfs" / "config.json"


def load_config() -> dict[str, Any]:
    """加载配置：环境变量 > 配置文件 > 默认值。"""
    defaults = {
        "namespaces": ["resources", "user", "agent"],
    }

    cfg_path = _config_path()
    if cfg_path.exists():
        try:
            with open(cfg_path, encoding="utf-8") as file:
                file_cfg = json.load(file)
            struct = file_cfg.get("structure", {})
            defaults.update(
                {
                    "namespaces": struct.get("namespaces", defaults["namespaces"]),
                }
            )
        except (json.JSONDecodeError, OSError):
            pass

    if os.getenv("OPENVFS_NAMESPACES"):
        defaults["namespaces"] = [item.strip() for item in os.getenv("OPENVFS_NAMESPACES", "").split(",") if item.strip()]

    return defaults

"""配置加载"""

import json
import os
from pathlib import Path
from typing import Any


def _config_path() -> Path:
    return Path.home() / ".openvfs" / "config.json"


def load_config() -> dict[str, Any]:
    """加载配置：环境变量 > 配置文件 > 默认值。"""
    defaults = {
        "store": "tos",
        "bucket": "openvfs",
        "prefix": "",
        "endpoint": "tos-cn-beijing.volces.com",
        "region": "cn-beijing",
        "ak_env": "TOS_ACCESS_KEY",
        "sk_env": "TOS_SECRET_KEY",
        "namespaces": ["resources", "user", "agent"],  # None 或 [] 表示不限制路径首段
    }

    cfg_path = _config_path()
    if cfg_path.exists():
        try:
            with open(cfg_path, encoding="utf-8") as f:
                file_cfg = json.load(f)
            storage = file_cfg.get("storage", {})
            creds = file_cfg.get("credentials", {})
            struct = file_cfg.get("structure", {})
            defaults.update(
                {
                    "store": storage.get("provider", defaults["store"]),
                    "bucket": storage.get("bucket", defaults["bucket"]),
                    "prefix": storage.get("prefix", defaults["prefix"]),
                    "endpoint": storage.get("endpoint", defaults["endpoint"]),
                    "region": storage.get("region", defaults["region"]),
                    "ak_env": creds.get("ak_env", defaults["ak_env"]),
                    "sk_env": creds.get("sk_env", defaults["sk_env"]),
                    "namespaces": struct.get("namespaces", defaults["namespaces"]),
                }
            )
        except (json.JSONDecodeError, OSError):
            pass

    # 环境变量覆盖
    if os.getenv("OPENVFS_STORE"):
        defaults["store"] = os.getenv("OPENVFS_STORE")
    if os.getenv("OPENVFS_BUCKET"):
        defaults["bucket"] = os.getenv("OPENVFS_BUCKET")
    if os.getenv("OPENVFS_PREFIX") is not None:
        defaults["prefix"] = os.getenv("OPENVFS_PREFIX", "")
    if os.getenv("OPENVFS_ENDPOINT"):
        defaults["endpoint"] = os.getenv("OPENVFS_ENDPOINT")
    if os.getenv("OPENVFS_REGION"):
        defaults["region"] = os.getenv("OPENVFS_REGION")

    return defaults

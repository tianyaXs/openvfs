"""Pytest 配置：过滤第三方库警告、加载 .env"""

import os
import warnings

# 从项目根 .env 加载凭证
def _load_dotenv():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))


_load_dotenv()

# 过滤 tos SDK 的 SyntaxWarning、DeprecationWarning
warnings.filterwarnings("ignore", category=SyntaxWarning, module="tos")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="tos")

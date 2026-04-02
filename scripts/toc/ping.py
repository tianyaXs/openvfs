"""TOS S3 兼容联通性测试脚本。"""

from __future__ import annotations

import asyncio
import os
import traceback
from typing import Any

from openvfs import OpenVfs, S3Store

TEST_URI = "openvfs://resources/ping/connectivity.md"
TEST_CONTENT = "# ping\n\nopenvfs connectivity test\n"


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少环境变量: {name}")
    return value


def _close_store(store: Any) -> None:
    close = getattr(store, "close", None)
    if close is None:
        return
    try:
        close()
    except Exception:
        traceback.print_exc()


def main() -> int:
    store: Any | None = None
    vfs = None
    try:
        access_key = _required_env("TOS_ACCESS_KEY")
        secret_key = _required_env("TOS_SECRET_KEY")
        bucket = os.getenv("OPENVFS_BUCKET", "mindmark")
        endpoint = os.getenv("OPENVFS_ENDPOINT", "tos-cn-beijing.volces.com")
        region = os.getenv("OPENVFS_REGION", "cn-beijing")

        s3_endpoint = endpoint if "tos-s3-" in endpoint else endpoint.replace("tos-", "tos-s3-", 1)
        print(f"[信息] bucket={bucket}")
        print(f"[信息] region={region}")
        print(f"[信息] endpoint={endpoint}")
        print(f"[信息] s3_endpoint={s3_endpoint}")

        store = S3Store(
            bucket_name=bucket,
            region_name=region,
            endpoint_url=f"https://{s3_endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        vfs = OpenVfs.init_vfs(store=store)

        print(f"[信息] 写入测试文档: {TEST_URI}")
        vfs.create(TEST_URI, TEST_CONTENT)

        print("[信息] 回读测试文档")
        content = vfs.read(TEST_URI)
        if content != TEST_CONTENT:
            raise RuntimeError("回读内容与写入内容不一致")

        print("[信息] 列举目录")
        items = vfs.list("openvfs://resources/ping")
        print(f"[信息] items={items}")
        if "connectivity.md" not in items:
            raise RuntimeError("目录列举未返回 connectivity.md")

        print("[信息] 清理测试文档")
        vfs.delete(TEST_URI)

        print("[成功] TOS S3 兼容联通测试通过")
        return 0
    except Exception as exc:
        print(f"[失败] {exc}")
        traceback.print_exc()
        return 1
    finally:
        if vfs is not None:
            _close_store(getattr(vfs, "_store", None))
        else:
            _close_store(store)


if __name__ == "__main__":
    raise SystemExit(main())

"""本地单元测试：不依赖真实 TOS，验证基础 VFS 与 Cell 行为。"""

from __future__ import annotations

from openvfs.client import Client
from openvfs.exceptions import NotFoundError


class InMemoryStorage:
    def __init__(self, bucket: str, prefix: str = "", **_: object) -> None:
        self.bucket = bucket
        self.prefix = (prefix or "").strip("/")
        self._prefix = f"{self.prefix}/" if self.prefix else ""
        self._data: dict[str, bytes] = {}

    def put(self, key: str, content: str | bytes) -> None:
        self._data[key] = content.encode("utf-8") if isinstance(content, str) else content

    def get(self, key: str) -> bytes:
        if key not in self._data:
            raise NotFoundError(key)
        return self._data[key]

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self._data

    def list_keys(self, prefix: str, delimiter: str = "/") -> list[str]:
        full_prefix = f"{self._prefix}{prefix.lstrip('/')}"
        if full_prefix and not full_prefix.endswith(delimiter):
            full_prefix += delimiter

        dirs: set[str] = set()
        files: set[str] = set()
        for key in self._data:
            if not key.startswith(full_prefix):
                continue
            rel = key[len(full_prefix) :]
            if not rel:
                continue
            if delimiter in rel:
                dirs.add(rel.split(delimiter, 1)[0] + delimiter)
            else:
                files.add(rel)
        return sorted(dirs) + sorted(files)


def _client(monkeypatch):
    monkeypatch.setattr("openvfs.client.TOSStorage", InMemoryStorage)
    return Client(bucket="test", namespaces=[])


def test_path_crud(monkeypatch):
    client = _client(monkeypatch)
    p = client.path("resources/app")

    p.create_file("config.json", '{"v":1}')
    assert p.exists_file("config.json")

    file = p.find_file("config.json")
    assert file.read() == '{"v":1}'

    p.update_file("config.json", '{"v":2}')
    file2 = p.find_file("config.json")
    assert file2.read() == '{"v":2}'

    p.delete("config.json")
    assert not p.exists_file("config.json")


def test_client_uri_and_list(monkeypatch):
    client = _client(monkeypatch)
    base = "openvfs://resources/demo"

    client.create_file(f"{base}/a.txt", "A")
    client.create_file(f"{base}/nested/b.txt", "B")

    items = client.list(base)
    assert items == ["nested/", "a.txt"]

    tree = client.tree(base)
    assert "nested/" in tree
    assert "a.txt" in tree


def test_file_cells_crud_and_multi_attrs_find(monkeypatch):
    client = _client(monkeypatch)
    uri = "openvfs://resources/demo/cells.md"
    client.create_file(uri, "")

    file = client.find(uri)
    file.add_cell(cell_type="heading", content="Quick Start", attrs={"id": "h1", "scope": "guide"}, level=2)
    file.add_cell(cell_type="code", content="pip install openvfs", attrs={"id": "install", "scope": "guide"}, lang="bash")
    file.add_cell(cell_type="json", content='{"name": "openvfs"}', attrs={"id": "meta", "scope": "data"})

    target = file.find_cell(id="install", scope="guide")
    assert target.type == "code"
    assert "pip install" in target.content

    updated = file.update_cell({"id": "install", "scope": "guide"}, content="uv add openvfs")
    assert updated.content == "uv add openvfs"

    removed = file.delete_cell(id="meta", scope="data")
    assert removed == 1

    remain = file.list_cells()
    assert len(remain) == 2
    assert file.find_cell(id="install", scope="guide").content == "uv add openvfs"
    assert len(file.find_cells(scope="guide")) == 2


def test_file_add_cells_batch(monkeypatch):
    client = _client(monkeypatch)
    uri = "openvfs://resources/demo/batch.md"
    client.create_file(uri, "")
    file = client.find(uri)

    file.add_cells(
        [
            {"type": "heading", "content": "API", "attrs": {"id": "api", "scope": "doc"}, "meta": {"level": 2}},
            {"type": "link", "content": "https://example.com", "attrs": {"id": "ref", "scope": "doc"}},
        ]
    )

    assert len(file.list_cells()) == 2
    assert file.find_cell(id="api", scope="doc").type == "heading"


def test_folder_object_and_create_folder(monkeypatch):
    client = _client(monkeypatch)
    root = "openvfs://resources/workspace"
    client.create_folder(f"{root}/docs")
    assert client.exists_folder(f"{root}/docs")

    folder = client.find_folder(f"{root}/docs")
    folder.create_file("readme.md", "hello")
    assert folder.exists_file("readme.md")
    assert folder.find_file("readme.md").read() == "hello"


def test_path_supports_folder_ops(monkeypatch):
    client = _client(monkeypatch)
    p = client.path("resources/path_space")
    p.create_folder("notes")
    assert p.exists_folder("notes")

    notes = p.find_folder("notes")
    notes.create_file("todo.txt", "x")
    assert notes.find_file("todo.txt").read() == "x"

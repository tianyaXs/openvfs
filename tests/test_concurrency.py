from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import unittest

from openvfs import OpenVfs


class ConcurrencyBehaviorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.vfs = OpenVfs.init_vfs()

    def test_add_cell_is_thread_safe_on_single_instance(self) -> None:
        path = "resources/tests/concurrent-add-cell"
        file = self.vfs.find_file(path, must_exist=False)
        self.assertIsNotNone(file)
        assert file is not None
        file.create("# root\n")

        total_per_worker = 40

        def worker(worker_id: int) -> None:
            for index in range(total_per_worker):
                cell_id = f"w{worker_id}-{index}"
                self.vfs.add_cell(
                    path,
                    title=f"Task {cell_id}",
                    content=f"payload {cell_id}",
                    attrs={"id": cell_id},
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker, 1), executor.submit(worker, 2)]
            for future in futures:
                future.result()

        cells = self.vfs.list_cell(path)
        self.assertEqual(len(cells), total_per_worker * 2 + 1)
        ids = {cell.attrs.get("id") for cell in cells}
        for worker_id in (1, 2):
            for index in range(total_per_worker):
                self.assertIn(f"w{worker_id}-{index}", ids)

    def test_builder_write_keeps_all_parallel_appends(self) -> None:
        total_per_worker = 30

        def worker(worker_id: int) -> None:
            for index in range(total_per_worker):
                token = f"worker-{worker_id}-line-{index}"
                (
                    self.vfs.cd_path("resources", "tests")
                    .create_file("builder-concurrent")
                    .text(token)
                    .write()
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker, 1), executor.submit(worker, 2)]
            for future in futures:
                future.result()

        content = self.vfs.read("resources/tests/builder-concurrent")
        for worker_id in (1, 2):
            for index in range(total_per_worker):
                token = f"worker-{worker_id}-line-{index}"
                self.assertIn(token, content)


if __name__ == "__main__":
    unittest.main()

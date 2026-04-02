from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import unittest

from openvfs import Cell, OpenVfs


class UpdateCellTest(unittest.TestCase):
    def setUp(self) -> None:
        self.vfs = OpenVfs.init_vfs()

    def test_update_cell_by_id(self) -> None:
        path = "resources/tests/update-cell"
        self.vfs.add_cell(path, "A", "old-a", attrs={"id": "a"})
        self.vfs.add_cell(path, "B", "old-b", attrs={"id": "b"})

        updated = self.vfs.update_cell(path, "@id=a", "new-a")
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertIsInstance(updated, Cell)
        assert isinstance(updated, Cell)
        self.assertEqual(updated.content.strip(), "new-a")

        cell_a = self.vfs.find_cell(path, "@id=a")
        self.assertIsInstance(cell_a, Cell)
        assert isinstance(cell_a, Cell)
        self.assertEqual(cell_a.content.strip(), "new-a")
        cell_b = self.vfs.find_cell(path, "@id=b")
        self.assertIsInstance(cell_b, Cell)
        assert isinstance(cell_b, Cell)
        self.assertEqual(cell_b.content.strip(), "old-b")

    def test_update_cell_zero_or_one_allows_miss(self) -> None:
        path = "resources/tests/update-cell-zero-or-one"
        self.vfs.add_cell(path, "A", "old-a", attrs={"id": "a"})
        result = self.vfs.update_cell(path, "@id=missing", "noop", expect="zero_or_one")
        self.assertIsNone(result)

    def test_update_cell_parallel_updates_keep_both_results(self) -> None:
        path = "resources/tests/update-cell-parallel"
        self.vfs.add_cell(path, "A", "old-a", attrs={"id": "a"})
        self.vfs.add_cell(path, "B", "old-b", attrs={"id": "b"})

        rounds = 25

        def worker(cell_id: str, prefix: str) -> None:
            for index in range(rounds):
                self.vfs.update_cell(path, f"@id={cell_id}", f"{prefix}-{index}")

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(worker, "a", "A"),
                executor.submit(worker, "b", "B"),
            ]
            for future in futures:
                future.result()

        cell_a = self.vfs.find_cell(path, "@id=a")
        cell_b = self.vfs.find_cell(path, "@id=b")
        self.assertIsInstance(cell_a, Cell)
        self.assertIsInstance(cell_b, Cell)
        assert isinstance(cell_a, Cell)
        assert isinstance(cell_b, Cell)
        self.assertEqual(cell_a.content.strip(), f"A-{rounds - 1}")
        self.assertEqual(cell_b.content.strip(), f"B-{rounds - 1}")


if __name__ == "__main__":
    unittest.main()

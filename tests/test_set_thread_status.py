from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "skills" / "manage-codex-thread-status" / "scripts" / "set_thread_status.py"
SPEC = importlib.util.spec_from_file_location("set_thread_status", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UpdatedTitleTests(unittest.TestCase):
    def test_replaces_existing_status_prefix(self) -> None:
        self.assertEqual(
            MODULE.updated_title("✅ Existing topic", "in-progress", None),
            "⏳ Existing topic",
        )

    def test_preserves_unprefixed_title_body(self) -> None:
        self.assertEqual(
            MODULE.updated_title("Existing topic", "needs-attention", None),
            "🚨 Existing topic",
        )

    def test_explicit_title_body_changes_topic(self) -> None:
        self.assertEqual(
            MODULE.updated_title("✅ Old topic", "done", "New topic"),
            "✅ New topic",
        )


class RequireResultTests(unittest.TestCase):
    def test_rejects_rpc_error(self) -> None:
        with self.assertRaisesRegex(MODULE.AppServerError, "thread/name/set failed"):
            MODULE.require_result({"error": {"code": -32603, "message": "write failed"}}, "thread/name/set")

    def test_rejects_missing_result(self) -> None:
        with self.assertRaisesRegex(MODULE.AppServerError, "returned no result"):
            MODULE.require_result({"id": 1}, "thread/read")

    def test_returns_result(self) -> None:
        self.assertEqual(MODULE.require_result({"result": {"thread": {}}}, "thread/read"), {"thread": {}})


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "skills" / "manage-codex-thread-status" / "scripts" / "set_thread_status.py"
SKILL = Path(__file__).parents[1] / "skills" / "manage-codex-thread-status" / "SKILL.md"
AUTOMATION_PROMPT = Path(__file__).parents[1] / "skills" / "manage-codex-thread-status" / "references" / "automation-prompt.md"
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

    def test_replaces_all_duplicate_status_prefixes(self) -> None:
        self.assertEqual(
            MODULE.updated_title("✅ 🚨 ⏳ Existing topic", "in-progress", None),
            "⏳ Existing topic",
        )

    def test_replaces_duplicate_status_prefixes_without_spaces(self) -> None:
        self.assertEqual(
            MODULE.updated_title("✅🚨 ⏳Existing topic", "done", None),
            "✅ Existing topic",
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

    def test_same_title_is_classified_as_refresh_write(self) -> None:
        self.assertEqual(MODULE.write_kind("⏳ Existing topic", "⏳ Existing topic"), "refresh")

    def test_changed_title_is_classified_as_change_write(self) -> None:
        self.assertEqual(MODULE.write_kind("✅ Existing topic", "⏳ Existing topic"), "change")


class RequireResultTests(unittest.TestCase):
    def test_rejects_rpc_error(self) -> None:
        with self.assertRaisesRegex(MODULE.AppServerError, "thread/name/set failed"):
            MODULE.require_result({"error": {"code": -32603, "message": "write failed"}}, "thread/name/set")

    def test_rejects_missing_result(self) -> None:
        with self.assertRaisesRegex(MODULE.AppServerError, "returned no result"):
            MODULE.require_result({"id": 1}, "thread/read")

    def test_returns_result(self) -> None:
        self.assertEqual(MODULE.require_result({"result": {"thread": {}}}, "thread/read"), {"thread": {}})


class AutomationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompt = AUTOMATION_PROMPT.read_text()
        cls.skill = SKILL.read_text()

    def test_prompt_scans_threads_and_reads_ambiguous_state(self) -> None:
        self.assertIn("List up to 50 recent Threads", self.prompt)
        self.assertIn("read enough of its latest turns", self.prompt)

    def test_prompt_contains_all_status_rules(self) -> None:
        for status in ("`⏳`", "`🚨`", "`✅`"):
            self.assertIn(status, self.prompt)
        self.assertIn("Be conservative with `✅`", self.prompt)

    def test_prompt_preserves_topic_and_verifies_updates(self) -> None:
        self.assertIn("strip all consecutive", self.prompt)
        self.assertIn("Preserve the remaining title body exactly", self.prompt)
        self.assertIn("verify both its title and current native/turn status", self.prompt)
        self.assertIn("changed state during the audit", self.prompt)
        self.assertIn("update its prefix once more", self.prompt)

    def test_skill_requires_real_scheduled_runtime(self) -> None:
        self.assertIn("every 20 minutes", self.skill)
        self.assertIn("Do not call the product complete", self.skill)
        self.assertNotIn("Do not poll, create a daemon, or scan historical threads", self.skill)


class InstallationStatusTests(unittest.TestCase):
    def make_installation(self, prompt: str) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        codex_home = Path(temporary.name)
        skill_dir = codex_home / "community" / "repo" / "skills" / "manage-codex-thread-status"
        (skill_dir / "references").mkdir(parents=True)
        (skill_dir / "references" / "automation-prompt.md").write_text(
            "# Prompt\n\nContract: `manage-codex-thread-status/v1`\n\ncanonical"
        )
        (codex_home / "skills").mkdir()
        (codex_home / "skills" / "manage-codex-thread-status").symlink_to(skill_dir)
        automation_dir = codex_home / "automations" / "codex-thread"
        automation_dir.mkdir(parents=True)
        (automation_dir / "automation.toml").write_text(
            'id = "codex-thread"\nkind = "heartbeat"\nname = "Codex Thread 状态同步"\n'
            f'prompt = "{prompt}"\nstatus = "ACTIVE"\nrrule = "FREQ=MINUTELY;INTERVAL=20"\n'
        )
        return temporary, codex_home, skill_dir

    def test_accepts_one_exact_active_20_minute_automation(self) -> None:
        temporary, codex_home, skill_dir = self.make_installation(
            "Contract: `manage-codex-thread-status/v1`\\n\\ncanonical"
        )
        with temporary:
            result = MODULE.installation_status(codex_home, skill_dir)
            self.assertTrue(result["ok"])
            self.assertEqual(result["active_20_minute_automation_count"], 1)

    def test_rejects_prompt_drift(self) -> None:
        temporary, codex_home, skill_dir = self.make_installation("stale")
        with temporary:
            self.assertFalse(MODULE.installation_status(codex_home, skill_dir)["ok"])

    def test_rejects_second_active_coordinator_with_different_name(self) -> None:
        prompt = "Contract: `manage-codex-thread-status/v1`\\n\\ncanonical"
        temporary, codex_home, skill_dir = self.make_installation(prompt)
        with temporary:
            duplicate = codex_home / "automations" / "duplicate"
            duplicate.mkdir()
            (duplicate / "automation.toml").write_text(
                'id = "duplicate"\nkind = "heartbeat"\nname = "Renamed coordinator"\n'
                f'prompt = "{prompt}"\nstatus = "ACTIVE"\nrrule = "FREQ=MINUTELY;INTERVAL=20"\n'
            )
            result = MODULE.installation_status(codex_home, skill_dir)
            self.assertFalse(result["ok"])
            self.assertEqual(result["active_20_minute_automation_count"], 2)

    def test_rejects_wrong_schedule_or_status(self) -> None:
        prompt = "Contract: `manage-codex-thread-status/v1`\\n\\ncanonical"
        temporary, codex_home, skill_dir = self.make_installation(prompt)
        with temporary:
            config = codex_home / "automations" / "codex-thread" / "automation.toml"
            config.write_text(config.read_text().replace("ACTIVE", "PAUSED"))
            self.assertFalse(MODULE.installation_status(codex_home, skill_dir)["ok"])

    def test_rejects_skill_link_mismatch(self) -> None:
        prompt = "Contract: `manage-codex-thread-status/v1`\\n\\ncanonical"
        temporary, codex_home, skill_dir = self.make_installation(prompt)
        with temporary:
            link = codex_home / "skills" / "manage-codex-thread-status"
            link.unlink()
            link.symlink_to(codex_home / "wrong-skill")
            self.assertFalse(MODULE.installation_status(codex_home, skill_dir)["ok"])


if __name__ == "__main__":
    unittest.main()

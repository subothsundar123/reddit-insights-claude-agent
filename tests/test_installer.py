import importlib.util
import json
import pathlib
import plistlib
import tempfile
import unittest


SETUP_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "setup_unix.py"
SPEC = importlib.util.spec_from_file_location("insights_setup", SETUP_PATH)
assert SPEC and SPEC.loader
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)


class InstallerTests(unittest.TestCase):
    def test_macos_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp)
            self.assertEqual(
                SETUP.find_claude_config("macos", home),
                home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            )
            self.assertIn("Library", str(SETUP.default_install_dir("macos", home)))

    def test_config_merge_preserves_other_servers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            config_path = root / "Claude" / "claude_desktop_config.json"
            config_path.parent.mkdir()
            config_path.write_text(
                json.dumps({"mcpServers": {"existing": {"command": "keep-me"}}, "theme": "dark"}),
                encoding="utf-8",
            )
            backup = SETUP.merge_claude_config(
                config_path,
                pathlib.Path("/opt/insights/.venv/bin/python"),
                "https://github.com/example/data.git",
                root / "Nubra Product Insights",
            )
            merged = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertIsNotNone(backup)
            self.assertEqual(merged["theme"], "dark")
            self.assertEqual(merged["mcpServers"]["existing"]["command"], "keep-me")
            self.assertEqual(
                merged["mcpServers"]["reddit-product-insights"]["env"]["INSIGHTS_DESKTOP_LOCAL_ONLY"],
                "1",
            )

    def test_launchd_has_daily_and_login_catch_up(self):
        payload = SETUP.launchd_payload(
            pathlib.Path("/tmp/agent/python"), "https://example.test/data.git", pathlib.Path("/tmp/data"), 8
        )
        self.assertEqual(payload["StartCalendarInterval"], {"Hour": 8, "Minute": 0})
        self.assertTrue(payload["RunAtLoad"])
        self.assertEqual(payload["EnvironmentVariables"]["INSIGHTS_DESKTOP_LOCAL_ONLY"], "0")
        plistlib.dumps(payload)

    def test_systemd_timer_is_persistent(self):
        service, timer = SETUP.systemd_units(
            pathlib.Path("/home/test/agent python"),
            "https://example.test/data.git",
            pathlib.Path("/home/test/Nubra Product Insights"),
            8,
        )
        self.assertIn("OnCalendar=*-*-* 08:00:00", timer)
        self.assertIn("Persistent=true", timer)
        self.assertIn("INSIGHTS_DESKTOP_LOCAL_ONLY=0", service)
        self.assertIn("ExecStart=", service)


if __name__ == "__main__":
    unittest.main()

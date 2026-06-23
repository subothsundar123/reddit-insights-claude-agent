import os
import pathlib
import shutil
import tempfile
import unittest

PUBLISHER = pathlib.Path(r"C:\Users\suboth sundar\Downloads\reddit_scraper_github_publisher")

class DailyFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = pathlib.Path(tempfile.mkdtemp(prefix="insights-agent-test-"))
        os.environ["INSIGHTS_DATA_REPO_PATH"] = str(PUBLISHER)
        os.environ["INSIGHTS_LOCAL_DATA_DIR"] = str(self.temp)
        os.environ.pop("INSIGHTS_DESKTOP_LOCAL_ONLY", None)

    def tearDown(self):
        os.environ.pop("INSIGHTS_DESKTOP_LOCAL_ONLY", None)
        shutil.rmtree(self.temp, ignore_errors=True)

    def test_daily_is_incremental_and_grounded(self):
        from reddit_insights_agent.core import daily_insights
        first = daily_insights(30)
        second = daily_insights(30)
        self.assertEqual(first["sync"]["new_dumps"], ["2026-06-22", "2026-06-23"])
        self.assertEqual(second["sync"]["new_dumps"], [])
        self.assertEqual(first["sync"]["catalog_version"], "1.0.0")
        self.assertEqual(first["analysis"]["sample"]["posts"], 318)
        self.assertEqual(first["analysis"]["sample"]["direct_posts"], 272)
        self.assertEqual(first["analysis"]["sample"]["web_research_summaries"], 46)
        self.assertIn("/feature-demand", first["available_commands"])
        self.assertNotIn("report_markdown", first)
        self.assertFalse(list((self.temp / "reports").glob("*.md")))
        self.assertFalse(list((self.temp / "reports").glob("*.pdf")))
        self.assertGreaterEqual(len(first["product_opportunities"]), 5)
        self.assertTrue(all(item["solution"] for item in first["product_opportunities"]))
        self.assertEqual(set(first["roadmap"]), {"Now", "Next", "Later"})

    def test_feature_lookup(self):
        from reddit_insights_agent.core import daily_insights, feature_lookup
        daily_insights(30)
        result = feature_lookup("UAT")
        self.assertTrue(any(row["status"] == "available" for row in result))

    def test_desktop_uses_saved_files_without_remote_sync(self):
        from reddit_insights_agent.core import daily_insights
        initial = daily_insights(30)
        self.assertEqual(initial["sync"]["mode"], "github_sync")
        os.environ["INSIGHTS_DESKTOP_LOCAL_ONLY"] = "1"
        os.environ["INSIGHTS_DATA_REPO_PATH"] = str(self.temp / "does-not-exist")
        desktop = daily_insights(30)
        self.assertEqual(desktop["sync"]["mode"], "local_files_only")
        self.assertEqual(desktop["sync"]["available_through"], "2026-06-23")
        self.assertEqual(desktop["analysis"]["sample"]["posts"], 318)

    def test_daily_prompt_returns_chat_report_only(self):
        from reddit_insights_agent.server import daily_product_insights
        prompt = daily_product_insights(30)
        self.assertIn("existing capabilities users are missing", prompt.lower())
        self.assertIn("what Nubra can improve now", prompt)
        self.assertIn("directly in this chat", prompt)
        self.assertNotIn("create_insights_pdf", prompt)

if __name__ == "__main__": unittest.main()

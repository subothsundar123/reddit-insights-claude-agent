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

    def tearDown(self):
        shutil.rmtree(self.temp, ignore_errors=True)

    def test_daily_is_incremental_and_grounded(self):
        from reddit_insights_agent.core import daily_insights
        first = daily_insights(30)
        second = daily_insights(30)
        self.assertEqual(first["sync"]["new_dumps"], ["2026-06-22"])
        self.assertEqual(second["sync"]["new_dumps"], [])
        self.assertEqual(first["sync"]["catalog_version"], "1.0.0")
        self.assertEqual(first["analysis"]["sample"]["posts"], 276)
        self.assertIn("/feature-demand", first["available_commands"])

    def test_feature_lookup(self):
        from reddit_insights_agent.core import daily_insights, feature_lookup
        daily_insights(30)
        result = feature_lookup("UAT")
        self.assertTrue(any(row["status"] == "available" for row in result))

if __name__ == "__main__": unittest.main()

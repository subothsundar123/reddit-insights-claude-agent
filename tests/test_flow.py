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
        report = first["report_markdown"]
        self.assertIn("## 1. Executive Summary", report)
        self.assertIn("## 2. Most Discussed Topics and Product Response", report)
        self.assertIn("Product thinking", report)
        self.assertIn("Suggested solution", report)
        self.assertIn("## 6. Product Roadmap", report)
        self.assertNotIn("Strategy-builder expectations", report)
        self.assertNotIn("Other market discussion", report)
        self.assertNotIn("Data available through", report)
        self.assertNotIn("Confidence", report)
        self.assertNotIn("Evidence and Confidence", report)
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

    def test_pdf_is_created_without_markdown_file(self):
        from reddit_insights_agent.server import create_insights_pdf
        result = create_insights_pdf(
            executive_summary=["API reliability needs a visible product response."],
            topics=[{
                "topic": "API reliability",
                "discussion": "Users discuss reconnect behaviour.",
                "product_thinking": "Reliability builds trust.",
                "solution": "Publish a health dashboard.",
            }],
            api_capabilities=[{
                "capability": "WebSocket monitoring",
                "demand": "Repeated reliability questions",
                "nubra_status": "Proposed",
                "action": "Add status visibility and SDK examples.",
            }],
            segment_split=[{
                "segment": "API/Algo",
                "needs": "Reliability and recovery",
                "product_use": "Improve activation and trust",
            }],
            webinars=[{
                "title": "Reliable WebSockets",
                "audience": "API developers",
                "why": "Recurring reliability questions",
                "outcome": "Improve adoption",
            }],
            roadmap={"Now": ["Publish status guidance"], "Next": ["Add analytics"], "Later": []},
            awareness_gaps=["Improve WebSocket documentation."],
        )
        pdf_path = pathlib.Path(result.structuredContent["pdf_path"])
        self.assertTrue(pdf_path.exists())
        self.assertEqual(pdf_path.suffix.lower(), ".pdf")
        self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))
        self.assertFalse(list((self.temp / "reports").glob("*.md")))

if __name__ == "__main__": unittest.main()

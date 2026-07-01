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
        self.assertEqual(first["sync"]["new_dumps"], ["2026-06-22", "2026-06-23", "2026-06-24", "2026-06-28", "2026-06-29", "2026-06-30"])
        self.assertEqual(second["sync"]["new_dumps"], [])
        self.assertEqual(first["sync"]["catalog_version"], "1.1.0")
        self.assertGreaterEqual(first["analysis"]["sample"]["posts"], 662)
        self.assertGreaterEqual(first["analysis"]["sample"]["direct_posts"], 272)
        self.assertGreaterEqual(first["analysis"]["sample"]["web_research_summaries"], 390)
        self.assertIn("github_search_api", first["analysis"]["sample"]["source_methods"])
        self.assertIn("hacker_news_algolia_api", first["analysis"]["sample"]["source_methods"])
        self.assertIn("broker_docs_page_fetch", first["analysis"]["sample"]["source_methods"])
        self.assertIn("/feature-requests", first["available_commands"])
        self.assertIn("/new-feature-analysis", first["available_commands"])
        self.assertIn("/ask-insights", first["available_commands"])
        self.assertIn("/status", first["available_commands"])
        self.assertIn("/update-connector", first["available_commands"])
        self.assertIn("/retail-feature-research", first["available_commands"])
        self.assertIn("/channel-insights", first["available_commands"])
        self.assertIn("/youtube-insights", first["available_commands"])
        self.assertIn("/seo-insights", first["available_commands"])
        self.assertNotIn("report_markdown", first)
        self.assertFalse(list((self.temp / "reports").glob("*.md")))
        self.assertFalse(list((self.temp / "reports").glob("*.pdf")))
        self.assertGreaterEqual(len(first["product_opportunities"]), 5)
        self.assertTrue(all(item["solution"] for item in first["product_opportunities"]))
        self.assertEqual(set(first["roadmap"]), {"Now", "Next", "Later"})
        self.assertIn("emerging_topic_candidates", first["analysis"])
        self.assertIn("competitor_signals", first["analysis"])
        self.assertIn("cross_topic_insights", first["analysis"])
        self.assertTrue(first["analysis"]["cross_topic_insights"])
        self.assertFalse(first["cache_hit"])
        self.assertTrue(second["cache_hit"])
        self.assertTrue(first["opportunity_scores"])
        self.assertTrue(all("opportunity_score" in item for item in first["opportunity_scores"]))
        self.assertTrue(first["feature_gap_matrix"])
        self.assertTrue(first["trend_changes"]["changes"])
        from reddit_insights_agent.core import TOPICS
        self.assertIn("Fundamental data & research", TOPICS)
        self.assertIn("Scanners, indicators & alerts", TOPICS)
        self.assertIn("SDK, MCP & integrations", TOPICS)

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
        self.assertEqual(desktop["sync"]["available_through"], "2026-06-30")
        self.assertGreaterEqual(desktop["analysis"]["sample"]["posts"], 662)

    def test_missing_catalog_self_heals_in_local_only_mode(self):
        from reddit_insights_agent.core import connector_status, daily_insights, sync
        daily_insights(30)
        (self.temp / "catalog" / "current.json").unlink()
        os.environ["INSIGHTS_DESKTOP_LOCAL_ONLY"] = "1"
        result = sync()
        self.assertEqual(result["health"], "healthy")
        self.assertTrue((self.temp / "catalog" / "current.json").exists())
        self.assertEqual(connector_status()["status"], "ready")

    def test_corrupted_dump_self_heals(self):
        from reddit_insights_agent.core import daily_insights, sync
        daily_insights(30)
        dump = self.temp / "raw" / "daily-dumps" / "2026-06-29" / "signals.jsonl.gz"
        original = dump.read_bytes()
        dump.write_bytes(b"corrupted")
        result = sync()
        self.assertEqual(result["health"], "healthy")
        self.assertEqual(dump.read_bytes(), original)

    def test_universal_query_returns_decision_inputs(self):
        from reddit_insights_agent.core import ask_insights
        result = ask_insights("What option chain features should Nubra prioritize?", 30)
        inputs = result["answer_inputs"]
        self.assertTrue(inputs["relevant_topics"])
        self.assertTrue(inputs["product_opportunities"])
        self.assertTrue(inputs["feature_gap_matrix"])
        self.assertTrue(inputs["evidence"])
        self.assertTrue(result["suggested_followups"])
        upcoming = ask_insights("What upcoming retail features should Nubra launch?", 30)
        self.assertGreaterEqual(len(upcoming["answer_inputs"]["retail_upcoming_features"]), 10)
        self.assertTrue(all(
            row["classification"] == "Upcoming"
            for row in upcoming["answer_inputs"]["feature_gap_matrix"]
        ))

    def test_connector_status_has_counts_and_tools(self):
        from reddit_insights_agent.core import connector_status, daily_insights
        daily_insights(30)
        result = connector_status()
        self.assertEqual(result["version"], "2.5.0")
        self.assertEqual(result["status"], "ready")
        self.assertGreater(result["counts"]["records"], 0)
        self.assertGreater(result["counts"]["features"], 0)
        self.assertGreaterEqual(result["counts"]["seo_keywords"], 1000)
        self.assertGreaterEqual(result["counts"]["seo_clusters"], 100)
        self.assertIn("ask_product_insights", result["available_tools"])
        self.assertIn("get_seo_keywords", result["available_tools"])

    def test_daily_prompt_returns_chat_report_only(self):
        from reddit_insights_agent.server import daily_product_insights
        prompt = daily_product_insights(30, "youtube", "retail")
        self.assertIn("existing capabilities users are missing", prompt.lower())
        self.assertIn("what nubra can improve now", prompt.lower())
        self.assertIn("only in chat", prompt)
        self.assertIn("Channel selection: youtube", prompt)
        self.assertIn("Focus selection: retail", prompt)
        self.assertIn("If focus is retail", prompt)
        self.assertNotIn("create_insights_pdf", prompt)

    def test_simple_analysis_prompts_are_available(self):
        from reddit_insights_agent.server import (
            ask_product_question,
            competitors,
            connector_health,
            feature_gaps,
            feature_requests,
            get_nubra_app_context,
            get_retail_upcoming_features,
            improve_now,
            new_ideas,
            new_feature_analysis,
            roadmap,
            retail_feature_research,
            seo_insights,
            trend_check,
            topic_links,
            youtube_insights,
            webinar_ideas,
        )
        prompts = {
            "ask_product_question": ask_product_question("What should Nubra improve?", 30),
            "connector_health": connector_health(),
            "competitors": competitors(30),
            "feature_requests": feature_requests(30),
            "feature_gaps": feature_gaps(30),
            "trend_check": trend_check(7, 30),
            "topic_links": topic_links(30),
            "youtube_insights": youtube_insights(30),
            "improve_now": improve_now(30),
            "new_ideas": new_ideas(30),
            "new_feature_analysis": new_feature_analysis(30),
            "retail_feature_research": retail_feature_research(30),
            "seo_insights": seo_insights(25, "retail", "option"),
            "webinar_ideas": webinar_ideas(30),
            "roadmap": roadmap(30),
        }
        self.assertEqual(len(prompts), 15)
        self.assertTrue(all("chat" in text.lower() for name, text in prompts.items() if name != "connector_health"))
        self.assertIn("ask_product_insights", prompts["ask_product_question"])
        self.assertIn("get_connector_status", prompts["connector_health"])
        self.assertIn("Product, SDK, MCP and Support", prompts["improve_now"])
        self.assertIn("Already available", prompts["feature_gaps"])
        self.assertIn("Underlying user need", prompts["feature_requests"])
        self.assertIn("recent rate and share", prompts["trend_check"])
        self.assertIn("Learning outcome", prompts["webinar_ideas"])
        self.assertIn("Suggested success measure", prompts["roadmap"])
        self.assertIn("emerging_topic_candidates", prompts["new_ideas"])
        self.assertIn("competitor_signals", prompts["competitors"])
        self.assertIn("Feature Coverage Table", prompts["retail_feature_research"])
        self.assertIn("Upcoming Feature Map", prompts["new_feature_analysis"])
        self.assertIn("250-instrument auto-refresh watchlists", prompts["new_feature_analysis"])
        self.assertIn("strategy-level P&L and risk-reward SL-TP", prompts["new_feature_analysis"])
        self.assertEqual(get_retail_upcoming_features()["count"], 34)
        self.assertIn("Nubra Android App", get_nubra_app_context())
        self.assertIn("cross_topic_insights", prompts["topic_links"])
        self.assertIn("YouTube", prompts["youtube_insights"])
        self.assertIn("comments", prompts["youtube_insights"])
        self.assertIn("get_seo_keywords", prompts["seo_insights"])
        self.assertIn("Highest-Value SEO Opportunities", prompts["seo_insights"])
        analysis_prompts = [text for name, text in prompts.items() if name not in {"connector_health"}]
        self.assertTrue(all("Start directly with the strongest insights" in text for text in analysis_prompts))
        self.assertTrue(all("do not return a plan" in text for text in analysis_prompts))

    def test_seo_keyword_catalog_syncs(self):
        from reddit_insights_agent.core import seo_keyword_catalog
        result = seo_keyword_catalog(limit=10, segment="retail")
        self.assertTrue(result["available"])
        self.assertGreaterEqual(result["summary"]["included_rows"]["priority_keywords"], 1000)
        self.assertTrue(result["priority_keywords"])
        self.assertTrue(result["search_seed_keywords"]["retail"])

if __name__ == "__main__": unittest.main()

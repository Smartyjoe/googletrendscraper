import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ["API_SECRET_KEY"] = "test-secret"

import pytrends_api  # noqa: E402


async def _fake_pipeline(**kwargs):
    title = kwargs.get("title", "")
    description = kwargs.get("description", "")
    if title and description:
        task_type = "hybrid"
    elif title:
        task_type = "discovery"
    else:
        task_type = "verification"

    return {
        "meta": {
            "status": "success",
            "task_type": task_type,
            "research_depth": kwargs.get("depth", "deep"),
            "timestamp": "2026-02-28T00:00:00",
            "latency_seconds": 0.1,
            "latency_budget_seconds": 6.0,
            "budget_exceeded": False,
        },
        "intent_analysis": {"entities": [], "claims": [], "tone": "neutral", "search_queries": ["q1", "q2", "q3"]},
        "seo_intel": {"primary_keywords": [], "rising_trends": [], "suggested_h2_headers": ["h2-a"]},
        "user_context_analysis": {"confirmed_facts": [], "conflict_points": [], "gaps": [], "new_insights": []},
        "source_material": [],
        "pipeline": {"openrouter_enabled": False, "search_enabled": False, "extractor_enabled": False, "sources_collected": 0},
    }


class TestSIRAEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(pytrends_api.app)
        cls.headers = {"X-API-Key": "test-secret"}

    def test_sira_title_only_mode(self):
        with patch("pytrends_api.run_sira_pipeline", side_effect=_fake_pipeline):
            response = self.client.post(
                "/api/sira/research",
                json={"title": "The Future of AI", "research_depth": "fast"},
                headers=self.headers,
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["meta"]["task_type"], "discovery")

    def test_sira_description_only_mode(self):
        with patch("pytrends_api.run_sira_pipeline", side_effect=_fake_pipeline):
            response = self.client.post(
                "/api/sira/research",
                json={"description": "Analyze how coffee shops use robots.", "research_depth": "deep"},
                headers=self.headers,
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["meta"]["task_type"], "verification")

    def test_sira_hybrid_mode(self):
        with patch("pytrends_api.run_sira_pipeline", side_effect=_fake_pipeline):
            response = self.client.post(
                "/api/sira/research",
                json={
                    "title": "Coffee Tech Revolution 2026",
                    "description": "Focus on automated brewing in Seattle.",
                    "research_depth": "deep",
                },
                headers=self.headers,
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["meta"]["task_type"], "hybrid")

    def test_sira_invalid_payload(self):
        response = self.client.post(
            "/api/sira/research",
            json={"research_depth": "deep"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

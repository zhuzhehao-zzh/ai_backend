"""Integration tests for the POST /api/submit endpoint."""

import json
from unittest.mock import AsyncMock
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app


class TestSubmitEndpoint:
    """Full-stack test with mocked LLM and isolated filesystem."""

    MOCK_LLM_RESPONSE = {
        "profileSummary": {
            "cluster": "技术探索型",
            "province": "广东",
            "score": "610",
            "subjectTrack": "理科",
            "preferredCities": ["深圳", "杭州"],
        },
        "top": [
            {
                "id": "software-engineering",
                "name": "软件工程",
                "recommendationBand": "强推荐",
                "matchScore": 96,
                "aiRisk": "低",
                "outlook": "稳定增长",
                "competitiveness": 94,
                "summary": "高度匹配",
                "schoolStrategy": "优先计算机强校",
                "cities": [{"name": "深圳", "note": "产业密集"}],
                "companies": [{"name": "华为"}],
                "roles": [
                    {
                        "id": "ai-engineer",
                        "name": "AI 工程师",
                        "currentDemand": "高需求",
                        "requirements": ["Python", "大模型"],
                    }
                ],
                "yearPlan": {
                    "year1": ["学 Python"],
                    "year2": ["学数据结构"],
                    "year3": ["做项目"],
                    "year4": ["找实习"],
                },
            }
        ],
        "cautious": [],
        "all": [],
    }

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", input_dir)
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", output_dir)

        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / "admission-guide.md"
        prompt_file.write_text("{student_data}", encoding="utf-8")
        monkeypatch.setattr("routes.api.PROMPT_DIR", prompt_dir)

        mock_completion = AsyncMock()
        mock_completion.choices = [AsyncMock()]
        mock_completion.choices[0].message.content = json.dumps(self.MOCK_LLM_RESPONSE)
        mock_completion.usage = "mock"

        mock_create = AsyncMock(return_value=mock_completion)
        monkeypatch.setattr(
            "services.model_pipeline.client.chat.completions.create",
            mock_create,
        )

    def test_submit_arbitrary_fields(self):
        """Any JSON with any field names should be accepted."""
        client = TestClient(app)
        payload = {
            "subjectTrack": "理科",
            "province": "广东",
            "score": 610,
            "a_new_field": "some value",
            "another_one": 42,
        }
        response = client.post("/api/submit", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["profileSummary"]["cluster"] == "技术探索型"
        assert len(data["top"]) == 1

    def test_submit_minimal_payload(self):
        """Even a single-field JSON should work."""
        client = TestClient(app)
        response = client.post("/api/submit", json={"only": "this field"})
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data

    def test_submit_empty_object(self):
        """Empty JSON object should be accepted (model gets {})."""
        client = TestClient(app)
        response = client.post("/api/submit", json={})
        assert response.status_code == 200

    def test_submit_returns_rich_response(self):
        client = TestClient(app)
        payload = {"score": 610, "interests": "编程"}
        response = client.post("/api/submit", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {
            "report_id", "generated_at", "profileSummary",
            "top", "cautious", "all",
        }

    def test_submit_creates_input_file(self, tmp_path):
        client = TestClient(app)
        client.post("/api/submit", json={"test": "data"})
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        assert len(list(input_dir.iterdir())) == 1
        assert len(list(output_dir.iterdir())) == 1

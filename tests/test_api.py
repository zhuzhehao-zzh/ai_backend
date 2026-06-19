"""Integration tests for the POST /api/submit endpoint."""

import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app


class TestSubmitEndpoint:
    """Full-stack test with mocked LLM and isolated filesystem."""

    BASE_PAYLOAD = {
        "subjectTrack": "理科",
        "province": "广东",
        "score": 610,
        "interests": "写代码、研究 AI",
        "skills": "数学能力、逻辑推理",
        "preferences": "高收入潜力、技术壁垒",
        "preferredCities": ["深圳", "杭州"],
        "dislikes": "不想学医",
    }

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
                "outlook": "稳定增长，但基础编码岗位门槛提高",
                "competitiveness": 94,
                "summary": "逻辑能力和 AI 兴趣高度匹配",
                "schoolStrategy": "优先计算机学科强校",
                "cities": [
                    {"name": "深圳", "note": "AI 应用、智能硬件和金融科技岗位密集"}
                ],
                "companies": [{"name": "华为"}, {"name": "腾讯"}],
                "roles": [
                    {
                        "id": "ai-application-engineer",
                        "name": "AI 应用工程师",
                        "currentDemand": "企业需要能把大模型能力接入业务的人才",
                        "requirements": ["Python", "大模型 API", "Web 开发"],
                    }
                ],
                "yearPlan": {
                    "year1": ["学 Python", "学高数"],
                    "year2": ["学数据结构", "学数据库"],
                    "year3": ["学机器学习", "做 AI 项目"],
                    "year4": ["准备校招", "复盘项目"],
                },
            }
        ],
        "cautious": [],
        "all": [],
    }

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Redirect file I/O to temp dirs and mock the LLM call."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", input_dir)
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", output_dir)

        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / "admission-guide.md"
        prompt_file.write_text("高考分数 {score}", encoding="utf-8")
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

    def test_submit_success(self):
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)

        assert response.status_code == 200
        data = response.json()

        assert "report_id" in data
        assert "generated_at" in data
        assert data["profileSummary"]["cluster"] == "技术探索型"
        assert len(data["top"]) == 1
        assert data["top"][0]["id"] == "software-engineering"

    def test_submit_has_year_plan(self):
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)
        assert response.status_code == 200

        data = response.json()
        top_item = data["top"][0]
        assert "yearPlan" in top_item
        assert len(top_item["yearPlan"]["year1"]) >= 1
        assert len(top_item["yearPlan"]["year4"]) >= 1

    def test_submit_missing_required_fields_returns_422(self):
        client = TestClient(app)
        response = client.post(
            "/api/submit",
            json={"province": "广东"},
        )
        assert response.status_code == 422

    def test_submit_invalid_score_returns_422(self):
        client = TestClient(app)
        payload = {
            "subjectTrack": "理科",
            "province": "广东",
            "score": 999,
            "interests": "编程",
            "skills": "数学",
            "preferences": "高收入",
            "dislikes": "学医",
        }
        response = client.post("/api/submit", json=payload)
        assert response.status_code == 422

    def test_submit_empty_body_returns_422(self):
        client = TestClient(app)
        response = client.post("/api/submit", json={})
        assert response.status_code == 422

    def test_submit_creates_input_and_output_files(self, tmp_path):
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)
        assert response.status_code == 200

        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"

        input_files = list(input_dir.iterdir())
        output_files = list(output_dir.iterdir())
        assert len(input_files) == 1
        assert len(output_files) == 1

    def test_submit_response_keys_match_expected(self):
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)
        assert response.status_code == 200

        data = response.json()
        assert set(data.keys()) == {
            "report_id", "generated_at", "profileSummary",
            "top", "cautious", "all",
        }

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
        "interests": "写代码、研究 AI、解决工程问题",
        "skills": "数学能力、逻辑推理、自学能力",
        "preferences": "高收入潜力、技术壁垒、稳定性",
        "preferredCities": ["深圳", "杭州"],
        "dislikes": "不想学医、不接受高压行业",
    }

    MOCK_LLM_RESPONSE = {
        "recommendations": [
            {
                "university": "深圳大学",
                "major": "计算机科学与技术",
                "match_score": 0.9,
                "rationale": "分数匹配，专业实力强，位于深圳，就业前景好",
            },
            {
                "university": "杭州电子科技大学",
                "major": "人工智能",
                "match_score": 0.85,
                "rationale": "杭州互联网产业发达，专业方向与兴趣吻合",
            },
        ],
        "action_items": [
            "建议优先考虑深圳和杭州的高校，符合城市偏好",
            "计算机类专业填报时注意区分计算机科学与技术和软件工程",
        ],
    }

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Redirect file I/O to temp dirs and mock the LLM call."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", input_dir)
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", output_dir)

        # Create a test prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / "admission-guide.md"
        prompt_file.write_text(
            "高考分数 {score}",
            encoding="utf-8",
        )
        monkeypatch.setattr("routes.api.PROMPT_DIR", prompt_dir)

        # Mock the LLM call
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
        assert len(data["recommendations"]) == 2
        assert data["recommendations"][0]["university"] == "深圳大学"
        assert data["recommendations"][1]["university"] == "杭州电子科技大学"
        assert len(data["action_items"]) == 2

    def test_submit_student_summary_in_response(self):
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        summary = data["student_summary"]
        assert summary["subjectTrack"] == "理科"
        assert summary["province"] == "广东"
        assert summary["score"] == 610
        assert summary["preferredCities"] == ["深圳", "杭州"]

    def test_submit_missing_required_fields_returns_422(self):
        client = TestClient(app)
        response = client.post(
            "/api/submit",
            json={"province": "广东"},  # missing most required fields
        )
        assert response.status_code == 422

    def test_submit_invalid_score_returns_422(self):
        client = TestClient(app)
        payload = {
            "subjectTrack": "理科",
            "province": "广东",
            "score": 999,  # exceeds 750
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
        assert input_files[0].suffix == ".json"
        assert output_files[0].suffix == ".json"

    def test_submit_response_matches_saved_report(self):
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)
        assert response.status_code == 200

        data = response.json()
        assert set(data.keys()) == {
            "report_id", "generated_at", "student_summary",
            "recommendations", "action_items",
        }

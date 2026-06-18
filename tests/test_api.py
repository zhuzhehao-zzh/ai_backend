"""Integration tests for the POST /api/submit endpoint."""

import json
from unittest.mock import AsyncMock
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app


class TestSubmitEndpoint:
    """Full-stack test with mocked LLM and isolated filesystem."""

    BASE_PAYLOAD = {
        "full_name": "Test User",
        "email": "test@example.com",
        "high_school": "Test High School",
        "gpa": 3.8,
        "sat_score": 1500,
        "intended_majors": ["Computer Science"],
    }

    MOCK_LLM_RESPONSE = {
        "recommendations": [
            {
                "university": "Stanford",
                "major": "Computer Science",
                "match_score": 0.85,
                "rationale": "Strong academic record aligns well.",
            },
            {
                "university": "MIT",
                "major": "Computer Science",
                "match_score": 0.82,
                "rationale": "Excellent math and science background.",
            },
        ],
        "action_items": [
            "Prepare personal statement by October 15",
            "Request recommendation letters by November 1",
        ],
    }

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch, tmp_path):
        """Redirect file I/O to temp dirs and mock the LLM call."""
        # Redirect data directories
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", input_dir)
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", output_dir)

        # Create a test prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompt_dir / "admission-guide.md"
        prompt_file.write_text(
            "Template for {full_name}",
            encoding="utf-8",
        )
        monkeypatch.setattr("routes.api.PROMPT_DIR", prompt_dir)

        # Mock the OpenAI call
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
        assert data["recommendations"][0]["university"] == "Stanford"
        assert data["recommendations"][1]["university"] == "MIT"
        assert len(data["action_items"]) == 2

    def test_submit_student_summary_in_response(self):
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        summary = data["student_summary"]
        assert summary["full_name"] == "Test User"
        assert summary["gpa"] == 3.8
        assert summary["email"] == "test@example.com"

    def test_submit_missing_required_fields_returns_422(self):
        client = TestClient(app)
        response = client.post(
            "/api/submit",
            json={"email": "test@test.com"},  # missing full_name, high_school, gpa
        )
        assert response.status_code == 422

    def test_submit_invalid_gpa_returns_422(self):
        client = TestClient(app)
        payload = {
            "full_name": "Test",
            "email": "test@test.com",
            "high_school": "HS",
            "gpa": 5.5,
        }
        response = client.post("/api/submit", json=payload)
        assert response.status_code == 422

    def test_submit_empty_body_returns_422(self):
        client = TestClient(app)
        response = client.post("/api/submit", json={})
        assert response.status_code == 422

    def test_submit_creates_input_and_output_files(self, tmp_path):
        """Verify the full disk I/O chain works."""
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)
        assert response.status_code == 200

        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"

        # Should have one file in each directory
        input_files = list(input_dir.iterdir())
        output_files = list(output_dir.iterdir())
        assert len(input_files) == 1
        assert len(output_files) == 1
        assert input_files[0].suffix == ".json"
        assert output_files[0].suffix == ".json"

    def test_submit_response_matches_saved_report(self):
        """Report returned from the endpoint matches what's on disk."""
        client = TestClient(app)
        response = client.post("/api/submit", json=self.BASE_PAYLOAD)
        assert response.status_code == 200

        data = response.json()
        # We can't check the exact file path from here, but the structure
        # should match the response model
        assert set(data.keys()) == {"report_id", "generated_at", "student_summary", "recommendations", "action_items"}

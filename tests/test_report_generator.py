"""Tests for the report generator service."""

import json
import pytest
from pathlib import Path

from services.report_generator import save_report

pytestmark = pytest.mark.asyncio


class TestReportGenerator:
    """save_report — report structure, disk output, defaults."""

    BASE_STUDENT = {
        "full_name": "Test",
        "email": "t@t.com",
        "high_school": "HS",
        "gpa": 3.8,
        "intended_majors": ["CS"],
    }

    async def test_returns_correct_structure(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        model_response = {
            "recommendations": [
                {
                    "university": "MIT",
                    "major": "Computer Science",
                    "match_score": 0.9,
                    "rationale": "Excellent profile fit",
                }
            ],
            "action_items": ["Submit application by Nov 1", "Prepare recommendation letters"],
        }

        report = await save_report(model_response, self.BASE_STUDENT)

        assert "report_id" in report
        assert "generated_at" in report
        assert len(report["recommendations"]) == 1
        assert report["recommendations"][0]["university"] == "MIT"
        assert len(report["action_items"]) == 2

    async def test_student_summary_filters_keys(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        student_info = {
            "full_name": "Alice",
            "email": "alice@example.com",
            "high_school": "West High",
            "gpa": 3.9,
            "intended_majors": ["Biology"],
            "phone": "1234567890",  # should be filtered out
            "sat_score": 1500,  # should be filtered out
        }

        report = await save_report({}, student_info)

        summary = report["student_summary"]
        assert summary["full_name"] == "Alice"
        assert summary["email"] == "alice@example.com"
        assert summary["high_school"] == "West High"
        assert summary["gpa"] == 3.9
        assert summary["intended_majors"] == ["Biology"]
        assert "phone" not in summary
        assert "sat_score" not in summary

    async def test_writes_json_file_to_disk(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report({}, self.BASE_STUDENT)

        filepath = test_dir / f"{report['report_id']}.json"
        assert filepath.exists()

        saved = json.loads(filepath.read_text(encoding="utf-8"))
        assert saved["report_id"] == report["report_id"]
        assert saved["generated_at"] == report["generated_at"]

    async def test_empty_model_response_uses_empty_defaults(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report({}, self.BASE_STUDENT)
        assert report["recommendations"] == []
        assert report["action_items"] == []

    async def test_creates_parent_directory_if_missing(self, monkeypatch, tmp_path):
        deep_dir = tmp_path / "x" / "y" / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", deep_dir)

        report = await save_report({}, self.BASE_STUDENT)
        filepath = deep_dir / f"{report['report_id']}.json"
        assert filepath.exists()
        assert deep_dir.exists()

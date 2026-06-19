"""Tests for the report generator service."""

import json
import pytest
from pathlib import Path

from services.report_generator import save_report

pytestmark = pytest.mark.asyncio


class TestReportGenerator:
    """save_report — report structure, disk output, defaults."""

    BASE_STUDENT = {
        "subjectTrack": "理科",
        "province": "广东",
        "score": 610,
        "interests": "写代码、研究 AI",
        "skills": "数学能力、逻辑推理",
        "preferences": "高收入潜力、技术壁垒",
        "preferredCities": ["深圳", "杭州"],
        "dislikes": "不想学医",
    }

    async def test_returns_correct_structure(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        model_response = {
            "recommendations": [
                {
                    "university": "深圳大学",
                    "major": "计算机科学与技术",
                    "match_score": 0.9,
                    "rationale": "分数匹配，专业对口",
                }
            ],
            "action_items": ["建议优先填报提前批", "准备好综合素质评价材料"],
        }

        report = await save_report(model_response, self.BASE_STUDENT)

        assert "report_id" in report
        assert "generated_at" in report
        assert len(report["recommendations"]) == 1
        assert report["recommendations"][0]["university"] == "深圳大学"
        assert len(report["action_items"]) == 2

    async def test_student_summary_filters_keys(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report({}, self.BASE_STUDENT)

        summary = report["student_summary"]
        assert summary["subjectTrack"] == "理科"
        assert summary["province"] == "广东"
        assert summary["score"] == 610
        assert "skills" not in summary  # filtered out
        assert "dislikes" not in summary  # filtered out
        assert "preferences" not in summary  # filtered out

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

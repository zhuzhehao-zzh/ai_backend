"""Tests for the report generator service."""

import json
import pytest
from pathlib import Path

from services.report_generator import save_report

pytestmark = pytest.mark.asyncio


class TestReportGenerator:
    """save_report — wraps model output with metadata and saves to disk."""

    MOCK_MODEL_OUTPUT = {
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

    async def test_wraps_model_output_with_metadata(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report(self.MOCK_MODEL_OUTPUT, {})

        assert "report_id" in report
        assert "generated_at" in report
        assert report["profileSummary"]["cluster"] == "技术探索型"
        assert len(report["top"]) == 1
        assert report["top"][0]["id"] == "software-engineering"
        assert report["cautious"] == []
        assert report["all"] == []

    async def test_passes_through_full_model_output(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report(self.MOCK_MODEL_OUTPUT, {})
        # The model output fields should be directly on the report
        assert "profileSummary" in report
        assert "top" in report
        assert "cautious" in report
        assert "all" in report
        # Every top item should have a yearPlan
        for item in report["top"]:
            assert "yearPlan" in item
            assert "year1" in item["yearPlan"]
            assert "year2" in item["yearPlan"]
            assert "year3" in item["yearPlan"]
            assert "year4" in item["yearPlan"]

    async def test_writes_json_file_to_disk(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report(self.MOCK_MODEL_OUTPUT, {})
        filepath = test_dir / f"{report['report_id']}.json"
        assert filepath.exists()

        saved = json.loads(filepath.read_text(encoding="utf-8"))
        assert saved["report_id"] == report["report_id"]
        assert saved["profileSummary"]["cluster"] == "技术探索型"

    async def test_empty_model_output_uses_defaults(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report({}, {})
        assert "report_id" in report
        assert "generated_at" in report

    async def test_creates_parent_directory_if_missing(self, monkeypatch, tmp_path):
        deep_dir = tmp_path / "x" / "y" / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", deep_dir)

        report = await save_report(self.MOCK_MODEL_OUTPUT, {})
        filepath = deep_dir / f"{report['report_id']}.json"
        assert filepath.exists()
        assert deep_dir.exists()

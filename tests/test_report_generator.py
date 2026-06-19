"""Tests for the report generator service."""

import json
import pytest
from pathlib import Path

from services.report_generator import save_report

pytestmark = pytest.mark.asyncio


class TestReportGenerator:
    """save_report — wraps model output with metadata and saves to disk."""

    MOCK_OUTPUT = {
        "profileSummary": {"cluster": "技术探索型"},
        "top": [
            {
                "id": "software-engineering",
                "name": "软件工程",
                "matchScore": 96,
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

    async def test_wraps_with_metadata(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report(self.MOCK_OUTPUT)

        assert "report_id" in report
        assert "generated_at" in report
        assert report["profileSummary"]["cluster"] == "技术探索型"
        assert len(report["top"]) == 1
        assert report["cautious"] == []

    async def test_passes_through_all_model_keys(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report(self.MOCK_OUTPUT)
        assert "profileSummary" in report
        assert "top" in report
        assert "cautious" in report
        assert "all" in report

    async def test_writes_json_file_to_disk(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report(self.MOCK_OUTPUT)
        filepath = test_dir / f"{report['report_id']}.json"
        assert filepath.exists()

        saved = json.loads(filepath.read_text(encoding="utf-8"))
        assert saved["report_id"] == report["report_id"]

    async def test_empty_output_still_gets_metadata(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", test_dir)

        report = await save_report({})
        assert "report_id" in report
        assert "generated_at" in report

    async def test_creates_parent_directory_if_missing(self, monkeypatch, tmp_path):
        deep_dir = tmp_path / "x" / "y" / "output"
        monkeypatch.setattr("services.report_generator.DATA_OUTPUT_DIR", deep_dir)

        report = await save_report(self.MOCK_OUTPUT)
        filepath = deep_dir / f"{report['report_id']}.json"
        assert filepath.exists()
        assert deep_dir.exists()

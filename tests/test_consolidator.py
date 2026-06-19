"""Tests for the data consolidation service."""

import json
import pytest
from pathlib import Path

from models.submission import StudentInfo
from services.consolidator import consolidate_and_save

pytestmark = pytest.mark.asyncio


class TestConsolidator:
    """consolidate_and_save — file creation and data fidelity."""

    BASE_INFO = {
        "subjectTrack": "理科",
        "province": "广东",
        "score": 610,
        "interests": "编程",
        "skills": "数学",
        "preferences": "高收入",
        "dislikes": "学医",
    }

    async def test_creates_json_file(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        info = StudentInfo(**self.BASE_INFO)
        filepath = await consolidate_and_save(info)
        assert filepath.exists()
        assert filepath.suffix == ".json"
        assert filepath.parent == test_dir

    async def test_saved_data_is_valid_json_with_all_fields(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        info = StudentInfo(
            subjectTrack="理科",
            province="广东",
            score=610,
            interests="写代码、研究 AI",
            skills="数学能力、逻辑推理",
            preferences="高收入潜力、技术壁垒",
            preferredCities=["深圳", "杭州"],
            dislikes="不想学医、不接受高压行业",
        )

        filepath = await consolidate_and_save(info)
        raw = filepath.read_text(encoding="utf-8")
        data = json.loads(raw)

        assert data["subjectTrack"] == "理科"
        assert data["province"] == "广东"
        assert data["score"] == 610
        assert data["interests"] == "写代码、研究 AI"
        assert data["preferredCities"] == ["深圳", "杭州"]

    async def test_optional_fields_excluded_when_empty(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        info = StudentInfo(**self.BASE_INFO)

        filepath = await consolidate_and_save(info)
        raw = filepath.read_text(encoding="utf-8")
        data = json.loads(raw)

        # preferredCities has default_factory=list, so it should be [] not None
        # With exclude_none=True, empty list [] is NOT excluded (it's not None)
        assert "preferredCities" in data
        assert data["preferredCities"] == []

    async def test_creates_parent_directory_if_missing(self, monkeypatch, tmp_path):
        deep_dir = tmp_path / "a" / "b" / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", deep_dir)

        info = StudentInfo(**self.BASE_INFO)
        filepath = await consolidate_and_save(info)
        assert filepath.exists()
        assert deep_dir.exists()

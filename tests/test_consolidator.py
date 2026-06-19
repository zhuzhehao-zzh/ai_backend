"""Tests for the data consolidation service."""

import json
import pytest
from pathlib import Path

from services.consolidator import consolidate_and_save

pytestmark = pytest.mark.asyncio


class TestConsolidator:
    """consolidate_and_save — file creation and data fidelity."""

    BASE_DATA = {
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

        filepath = await consolidate_and_save(self.BASE_DATA)
        assert filepath.exists()
        assert filepath.suffix == ".json"
        assert filepath.parent == test_dir

    async def test_saved_data_preserves_all_keys(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        data = {
            "subjectTrack": "理科",
            "province": "广东",
            "score": 610,
            "extra_field": "anything",
        }

        filepath = await consolidate_and_save(data)
        raw = filepath.read_text(encoding="utf-8")
        saved = json.loads(raw)

        assert saved["subjectTrack"] == "理科"
        assert saved["extra_field"] == "anything"
        assert len(saved) == 4

    async def test_empty_dict_saves_ok(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        filepath = await consolidate_and_save({})
        raw = filepath.read_text(encoding="utf-8")
        assert json.loads(raw) == {}

    async def test_creates_parent_directory_if_missing(self, monkeypatch, tmp_path):
        deep_dir = tmp_path / "a" / "b" / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", deep_dir)

        filepath = await consolidate_and_save(self.BASE_DATA)
        assert filepath.exists()
        assert deep_dir.exists()

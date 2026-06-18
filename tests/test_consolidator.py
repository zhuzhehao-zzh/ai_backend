"""Tests for the data consolidation service."""

import json
import pytest
from pathlib import Path

from models.submission import StudentInfo
from services.consolidator import consolidate_and_save

pytestmark = pytest.mark.asyncio


class TestConsolidator:
    """consolidate_and_save — file creation and data fidelity."""

    async def test_creates_json_file(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        info = StudentInfo(
            full_name="Test Student",
            email="test@example.com",
            high_school="Test High School",
            gpa=3.5,
        )

        filepath = await consolidate_and_save(info)
        assert filepath.exists()
        assert filepath.suffix == ".json"
        assert filepath.parent == test_dir

    async def test_saved_data_is_valid_json_with_all_fields(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        info = StudentInfo(
            full_name="Test Student",
            email="test@example.com",
            phone="13800138000",
            high_school="Test High School",
            gpa=3.5,
            sat_score=1400,
            intended_majors=["Engineering", "Physics"],
            extracurriculars=["Chess Club", "Soccer"],
        )

        filepath = await consolidate_and_save(info)
        raw = filepath.read_text(encoding="utf-8")
        data = json.loads(raw)

        assert data["full_name"] == "Test Student"
        assert data["gpa"] == 3.5
        assert data["sat_score"] == 1400
        assert data["intended_majors"] == ["Engineering", "Physics"]
        assert data["extracurriculars"] == ["Chess Club", "Soccer"]
        assert data["phone"] == "13800138000"

    async def test_optional_fields_excluded_when_none(self, monkeypatch, tmp_path):
        test_dir = tmp_path / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", test_dir)

        info = StudentInfo(
            full_name="A",
            email="a@b.com",
            high_school="HS",
            gpa=3.0,
        )

        filepath = await consolidate_and_save(info)
        raw = filepath.read_text(encoding="utf-8")
        data = json.loads(raw)

        # exclude_none=True so None fields should be absent
        assert "phone" not in data
        assert "date_of_birth" not in data
        assert "sat_score" not in data
        assert "act_score" not in data
        assert "budget_range" not in data
        assert "personal_statement" not in data

    async def test_creates_parent_directory_if_missing(self, monkeypatch, tmp_path):
        deep_dir = tmp_path / "a" / "b" / "input"
        monkeypatch.setattr("services.consolidator.DATA_INPUT_DIR", deep_dir)

        info = StudentInfo(
            full_name="B",
            email="b@b.com",
            high_school="HS",
            gpa=3.0,
        )

        filepath = await consolidate_and_save(info)
        assert filepath.exists()
        assert deep_dir.exists()

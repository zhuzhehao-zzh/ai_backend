"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from models.submission import StudentInfo


class TestStudentInfo:
    """StudentInfo model — required fields, ranges, defaults."""

    def test_valid_full_data(self):
        data = {
            "full_name": "Zhang Wei",
            "email": "zhangwei@example.com",
            "high_school": "Beijing No.4 High School",
            "gpa": 3.8,
            "sat_score": 1450,
            "intended_majors": ["Computer Science"],
        }
        info = StudentInfo(**data)
        assert info.full_name == "Zhang Wei"
        assert info.gpa == 3.8
        assert info.sat_score == 1450

    def test_minimal_required_fields_only(self):
        info = StudentInfo(
            full_name="Li Ming",
            email="liming@test.com",
            high_school="Test High School",
            gpa=3.5,
        )
        assert info.intended_majors == []
        assert info.extracurriculars == []
        assert info.phone is None

    def test_missing_required_field_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo()  # missing full_name, email, high_school, gpa

    def test_empty_full_name_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                full_name="",
                email="test@test.com",
                high_school="HS",
                gpa=3.0,
            )

    def test_invalid_gpa_above_range_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                full_name="Test",
                email="test@test.com",
                high_school="HS",
                gpa=5.0,
            )

    def test_invalid_gpa_below_range_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                full_name="Test",
                email="test@test.com",
                high_school="HS",
                gpa=-0.5,
            )

    def test_invalid_sat_below_min_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                full_name="Test",
                email="test@test.com",
                high_school="HS",
                gpa=3.0,
                sat_score=200,
            )

    def test_invalid_sat_above_max_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                full_name="Test",
                email="test@test.com",
                high_school="HS",
                gpa=3.0,
                sat_score=1700,
            )

    def test_invalid_act_below_min_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                full_name="Test",
                email="test@test.com",
                high_school="HS",
                gpa=3.0,
                act_score=0,
            )

    def test_all_list_fields_default_to_empty(self):
        info = StudentInfo(
            full_name="A",
            email="a@b.com",
            high_school="HS",
            gpa=3.0,
        )
        assert info.intended_majors == []
        assert info.coursework == []
        assert info.preferred_regions == []
        assert info.extracurriculars == []
        assert info.awards == []

    def test_personal_statement_max_length(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                full_name="Test",
                email="test@test.com",
                high_school="HS",
                gpa=3.0,
                personal_statement="x" * 5001,
            )

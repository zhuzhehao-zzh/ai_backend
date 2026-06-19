"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from models.submission import StudentInfo


class TestStudentInfo:
    """StudentInfo model — required fields, ranges, defaults."""

    def test_valid_full_data(self):
        data = {
            "subjectTrack": "理科",
            "province": "广东",
            "score": 610,
            "interests": "写代码、研究 AI",
            "skills": "数学能力、逻辑推理",
            "preferences": "高收入潜力、技术壁垒",
            "preferredCities": ["深圳", "杭州"],
            "dislikes": "不想学医",
        }
        info = StudentInfo(**data)
        assert info.subjectTrack == "理科"
        assert info.province == "广东"
        assert info.score == 610
        assert info.preferredCities == ["深圳", "杭州"]

    def test_minimal_required_fields_only(self):
        info = StudentInfo(
            subjectTrack="理科",
            province="广东",
            score=600,
            interests="编程",
            skills="数学",
            preferences="高收入",
            dislikes="学医",
        )
        assert info.preferredCities == []

    def test_missing_required_field_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo()  # missing all required fields

    def test_empty_province_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                subjectTrack="理科",
                province="",
                score=600,
                interests="编程",
                skills="数学",
                preferences="高收入",
                dislikes="学医",
            )

    def test_score_below_zero_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                subjectTrack="理科",
                province="广东",
                score=-1,
                interests="编程",
                skills="数学",
                preferences="高收入",
                dislikes="学医",
            )

    def test_score_above_750_fails(self):
        with pytest.raises(ValidationError):
            StudentInfo(
                subjectTrack="理科",
                province="广东",
                score=751,
                interests="编程",
                skills="数学",
                preferences="高收入",
                dislikes="学医",
            )

    def test_score_at_boundaries_succeeds(self):
        info_min = StudentInfo(
            subjectTrack="文科",
            province="北京",
            score=0,
            interests="a",
            skills="b",
            preferences="c",
            dislikes="d",
        )
        assert info_min.score == 0

        info_max = StudentInfo(
            subjectTrack="文科",
            province="北京",
            score=750,
            interests="a",
            skills="b",
            preferences="c",
            dislikes="d",
        )
        assert info_max.score == 750

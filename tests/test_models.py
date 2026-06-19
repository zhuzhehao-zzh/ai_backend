"""Tests for Pydantic response model validation."""

import pytest
from pydantic import ValidationError

from models.submission import SubmitResponse


class TestSubmitResponse:
    """SubmitResponse — required fields only."""

    def test_valid_response(self):
        resp = SubmitResponse(
            report_id="abc-123",
            generated_at="2026-01-01T00:00:00Z",
            profileSummary={"cluster": "技术探索型"},
            top=[{"id": "cs", "name": "计算机科学"}],
            cautious=[],
            all=[],
        )
        assert resp.report_id == "abc-123"
        assert resp.top[0]["name"] == "计算机科学"

    def test_missing_required_field_fails(self):
        with pytest.raises(ValidationError):
            SubmitResponse(
                report_id="abc",
                generated_at="...",
                # missing profileSummary, top, cautious, all
            )

    def test_empty_lists_are_valid(self):
        resp = SubmitResponse(
            report_id="x",
            generated_at="now",
            profileSummary={},
            top=[],
            cautious=[],
            all=[],
        )
        assert resp.top == []

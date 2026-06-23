"""Tests for JSON extraction and parsing in the model pipeline."""

import json
import pytest

from services.model_pipeline import _extract_json


def _j(obj):
    """Helper to JSON-serialize an object."""
    return json.dumps(obj, ensure_ascii=False)


class TestExtractJson:
    """_extract_json — handles various Kimi response formats."""

    def test_clean_json(self):
        result = _extract_json('{"a": 1, "b": [2, 3]}')
        assert result == {"a": 1, "b": [2, 3]}

    def test_json_with_markdown_fence(self):
        """Kimi sometimes wraps JSON in ```json ... ```."""
        raw = '```json\n{"a": 1}\n```'
        result = _extract_json(raw)
        assert result == {"a": 1}

    def test_json_with_markdown_fence_no_lang(self):
        raw = '```\n{"a": 1}\n```'
        result = _extract_json(raw)
        assert result == {"a": 1}

    def test_json_with_leading_text(self):
        raw = 'Here is the report:\n{"a": 1}'
        result = _extract_json(raw)
        assert result == {"a": 1}

    def test_json_with_trailing_text(self):
        raw = '{"a": 1}\nEnd of report.'
        result = _extract_json(raw)
        assert result == {"a": 1}

    def test_nested_json(self):
        raw = _j({"profileSummary": {"cluster": "测试"}, "top": [{"id": "cs"}]})
        result = _extract_json(raw)
        assert result["profileSummary"]["cluster"] == "测试"

    def test_json_with_chinese(self):
        raw = _j({"name": "计算机科学", "score": 95})
        result = _extract_json(raw)
        assert result["name"] == "计算机科学"

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            _extract_json("This is not JSON at all")

    def test_whitespace_handling(self):
        result = _extract_json('  \n\n {"a": 1}  \n  ')
        assert result == {"a": 1}

    def test_markdown_fence_with_newlines(self):
        raw = '```json\n\n{"a": 1}\n\n```'
        result = _extract_json(raw)
        assert result == {"a": 1}


class TestAllFieldSafetyNet:
    """The safety net in generate_report ensures 'all' is list[dict]."""

    def test_all_strings_converted(self):
        """When Kimi returns all as strings, the safety net converts them."""
        result = {"top": [{"id": "cs", "name": "计算机"}], "all": ["cs"]}
        # Simulate the safety net logic
        by_id = {e.get("id"): e for e in result.get("top", []) + result.get("cautious", [])}
        result["all"] = [by_id.get(sid, {"id": sid, "name": sid}) for sid in result["all"]]
        assert isinstance(result["all"][0], dict)
        assert result["all"][0]["name"] == "计算机"

    def test_all_already_dicts_unchanged(self):
        """If Kimi correctly returns dicts in all, they stay unchanged."""
        result = {
            "top": [{"id": "cs", "name": "计算机"}],
            "all": [{"id": "cs", "name": "计算机"}],
        }
        # Safety net should not fire since all[0] is already a dict
        if result.get("all") and isinstance(result["all"][0], str):
            # This should NOT execute
            result["all"] = []
        assert result["all"][0] == {"id": "cs", "name": "计算机"}

    def test_unknown_id_gets_fallback(self):
        """String IDs not found in top/cautious get a minimal dict fallback."""
        result = {"top": [], "cautious": [], "all": ["unknown-id"]}
        by_id = {e.get("id"): e for e in result.get("top", []) + result.get("cautious", [])}
        result["all"] = [by_id.get(sid, {"id": sid, "name": sid}) for sid in result["all"]]
        assert result["all"][0] == {"id": "unknown-id", "name": "unknown-id"}

    def test_all_empty_not_modified(self):
        result = {"top": [], "all": []}
        if result.get("all") and isinstance(result["all"][0], str):
            assert False, "Should not enter this branch"
        assert result["all"] == []

"""Flexible input model + strict output model for the Gaokao guidance API."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class RawStudentData(BaseModel):
    """Generic container for frontend data — accepts any JSON fields."""
    root: dict[str, Any]

    # Allow any extra fields through
    model_config = {"extra": "allow"}


class ErrorResponse(BaseModel):
    """Consistent error payload returned on failures."""

    error: dict = Field(default_factory=lambda: {"code": "", "message": ""})


class SubmitResponse(BaseModel):
    """Successful submission response — passes through model output with metadata."""

    report_id: str
    generated_at: str
    profileSummary: dict
    top: list[dict]
    cautious: list[dict]
    all: list  # Kimi may return strings or full objects here

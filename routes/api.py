"""Thin route handler — delegates to services for all business logic."""

import logging
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException

from models.submission import SubmitResponse
from services.consolidator import consolidate_and_save
from services.model_pipeline import generate_report
from services.report_generator import save_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["submission"])

PROMPT_DIR = Path("prompts")


@router.post("/submit", response_model=SubmitResponse)
async def submit(data: dict = Body(...)):
    """Receive arbitrary student data, feed to Kimi, return structured report."""
    try:
        # 1. Save raw student data to disk
        data_path = await consolidate_and_save(data)

        # 2. Generate report via LLM
        prompt_path = PROMPT_DIR / "admission-guide.md"
        model_response = await generate_report(data_path, prompt_path)

        # 3. Save report and return frontend-friendly payload
        report = await save_report(model_response)

        return report

    except Exception as exc:
        logger.exception("Submission failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(exc)},
        )

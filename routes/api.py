"""Thin route handler — delegates to services for all business logic."""

import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException

from models.submission import SubmitResponse
from services.consolidator import consolidate_and_save
from services.model_pipeline import generate_report
from services.report_generator import save_report
from services.database import save_request, save_response, save_feedback
from services.history_service import get_pattern_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["submission"])

PROMPT_DIR = Path("prompts")


@router.post("/submit", response_model=SubmitResponse)
async def submit(data: dict = Body(...)):
    """Receive student data → save → enrich with history → call Kimi → save response."""
    request_id = str(uuid.uuid4())

    try:
        # 1. Save raw student data to disk and DB
        data_path = await consolidate_and_save(data)
        try:
            await save_request(request_id, data)
        except Exception:
            logger.warning("DB save failed (request)", exc_info=True)

        # 2. Get historical patterns for prompt enrichment
        patterns = await get_pattern_summary()

        # 3. Generate report via LLM (with patterns)
        prompt_path = PROMPT_DIR / "admission-guide.md"
        model_response = await generate_report(data_path, prompt_path, patterns)

        # 4. Save report
        report = await save_report(model_response)

        # 5. Save response to DB (async, non-blocking)
        try:
            await save_response(
                response_id=report["report_id"],
                request_id=request_id,
                report=model_response,
            )
        except Exception:
            logger.warning("DB save failed (response)", exc_info=True)

        return report

    except Exception as exc:
        logger.exception("Submission failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(exc)},
        )


@router.post("/feedback")
async def feedback(body: dict = Body(...)):
    """Record user feedback (rating 1-5) for a response."""
    response_id = body.get("response_id")
    rating = body.get("rating")
    comment = body.get("comment")

    if not response_id or not rating:
        raise HTTPException(status_code=400, detail="response_id and rating are required")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 1-5")

    try:
        await save_feedback(response_id, rating, comment)
        return {"status": "ok", "message": "Feedback recorded"}
    except Exception as exc:
        logger.exception("Feedback save failed")
        raise HTTPException(status_code=500, detail=str(exc))

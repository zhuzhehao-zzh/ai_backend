"""Thin route handler — delegates to services for all business logic."""

import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Request

from models.submission import SubmitResponse
from services.consolidator import consolidate_and_save
from services.model_pipeline import generate_report
from services.report_generator import save_report
from services.database import save_request, save_response, save_feedback
from services.history_service import get_pattern_summary

from services.stats_service import get_stats
from services.security import (
    check_rate_limit,
    validate_json_depth,
    scan_data_for_injection,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["submission"])

PROMPT_DIR = Path("prompts")


def _real_ip(request: Request) -> str:
    """Get real client IP from X-Forwarded-For or direct connection."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/submit", response_model=SubmitResponse)
async def submit(data: dict = Body(...), request: Request = None):
    """Receive student data → security checks → save → Kimi → save response."""
    client_ip = _real_ip(request) if request else "unknown"
    request_id = str(uuid.uuid4())

    # ── Security checks ──────────────────────────────────────────
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests, please wait")

    try:
        validate_json_depth(data)
    except ValueError as e:
        logger.warning("SECURITY | %s | invalid JSON structure: %s", client_ip, e)
        raise HTTPException(status_code=400, detail=str(e))

    flagged = scan_data_for_injection(data)
    if flagged:
        logger.warning("SECURITY | %s | prompt injection flagged in: %s", client_ip, flagged)
        raise HTTPException(status_code=400, detail="Input contains prohibited patterns")

    # ── Process request ─────────────────────────────────────────
    logger.info(
        "REQUEST  | %s | %s | keys=%s",
        client_ip, request_id, list(data.keys()),
    )

    try:
        data_path = await consolidate_and_save(data)
        try:
            await save_request(request_id, data, client_ip)
        except Exception:
            logger.warning("DB save failed (request)", exc_info=True)

        patterns = await get_pattern_summary()
        prompt_path = PROMPT_DIR / "admission-guide.md"
        model_response = await generate_report(data_path, prompt_path, patterns)
        report = await save_report(model_response)

        try:
            await save_response(
                response_id=report["report_id"],
                request_id=request_id,
                report=model_response,
            )
        except Exception:
            logger.warning("DB save failed (response)", exc_info=True)

        top_names = [t.get("name", "?") for t in model_response.get("top", [])]
        logger.info(
            "RESPONSE | %s | %s | top=%s report_id=%s",
            client_ip, request_id, top_names, report["report_id"],
        )

        return report

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("ERROR    | %s | %s | %s", client_ip, request_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(exc)},
        )


@router.post("/feedback")
async def feedback(body: dict = Body(...), request: Request = None):
    """Record user feedback (rating 1-5) for a response."""
    client_ip = _real_ip(request) if request else "unknown"
    response_id = body.get("response_id")
    rating = body.get("rating")
    comment = body.get("comment")

    if not response_id or not rating:
        raise HTTPException(status_code=400, detail="response_id and rating are required")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 1-5")

    try:
        await save_feedback(response_id, rating, comment)
        logger.info(
            "FEEDBACK | %s | response=%s rating=%d",
            client_ip, response_id, rating,
        )
        return {"status": "ok", "message": "Feedback recorded"}
    except Exception as exc:
        logger.exception("FEEDBACK FAIL | %s", client_ip)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats")
async def stats(request: Request = None):
    """Return usage statistics from DB, including current IP's request count."""
    try:
        client_ip = _real_ip(request) if request else None
        return await get_stats(client_ip)
    except Exception as exc:
        logger.exception("Stats failed")
        raise HTTPException(status_code=500, detail=str(exc))

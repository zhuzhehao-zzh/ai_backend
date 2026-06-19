"""Save the model-generated report to disk and return a frontend-safe payload."""

import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone

import aiofiles

logger = logging.getLogger(__name__)

DATA_OUTPUT_DIR = Path("data/output")


async def save_report(model_response: dict) -> dict:
    """Wrap model response with metadata and save to disk."""
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report_id = str(uuid.uuid4())
    report = {
        "report_id": report_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **model_response,
    }

    filepath = DATA_OUTPUT_DIR / f"{report_id}.json"
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(json.dumps(report, indent=2, ensure_ascii=False))

    logger.info("Report saved to %s", filepath)
    return report

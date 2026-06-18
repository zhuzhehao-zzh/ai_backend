"""Save incoming student data to a structured JSON file in data/input/."""

import json
import uuid
import logging
from pathlib import Path

import aiofiles

from models.submission import StudentInfo

logger = logging.getLogger(__name__)

DATA_INPUT_DIR = Path("data/input")


async def consolidate_and_save(info: StudentInfo) -> Path:
    """Write validated student data to a JSON file and return its path."""
    DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)

    filepath = DATA_INPUT_DIR / f"{uuid.uuid4()}.json"
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(info.model_dump_json(indent=2, exclude_none=True))

    logger.info("Consolidated data saved to %s", filepath)
    return filepath

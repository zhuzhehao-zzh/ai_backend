---
name: report-generator
description: Generate and store reports from model output. Use when saving a report to disk, formatting it for frontend delivery, or defining the report data structure.
---

# Report Generator Skill

Use this skill when generating reports from the model's output, saving them to disk, and returning them to the frontend.

## Scope
- Report structure and formatting
- File output (JSON, Markdown)
- Frontend-friendly response shapes
- Report metadata and lookup

## Output Locations
- Raw model output / report: `data/output/{report_id}.json`

## Report Data Structure

```json
{
  "report_id": "uuid",
  "generated_at": "ISO-8601",
  "student_summary": { ... },
  "recommendations": [
    { "university": "...", "major": "...", "match_score": 0.95, "rationale": "..." }
  ],
  "action_items": [ "Deadline: ...", "Requirement: ..." ]
}
```

## Pattern

```python
# services/report_generator.py
from pathlib import Path
import json, uuid
from datetime import datetime, timezone

DATA_OUTPUT_DIR = Path("data/output")

async def save_report(model_response: dict, student_info: dict) -> dict:
    """Save the report and return a frontend-friendly payload."""
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "report_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "student_summary": student_info,
        "recommendations": model_response.get("recommendations", []),
        "action_items": model_response.get("action_items", []),
    }

    filepath = DATA_OUTPUT_DIR / f"{report['report_id']}.json"
    async with aiofiles.open(filepath, "w") as f:
        await f.write(json.dumps(report, indent=2, ensure_ascii=False))

    return report  # returned to frontend, no raw model output
```

## Validation
- Report is valid JSON
- All expected keys present before saving
- File path is deterministic from report_id for later retrieval
- Frontend response excludes raw model output unless requested

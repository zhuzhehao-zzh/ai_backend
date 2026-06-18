---
name: college-admissions-backend
description: Build and maintain FastAPI endpoints for the college application guidance backend. Use when creating new API routes, handling student data submission, or consolidating form input into structured files.
---

# College Admissions Backend Skill

Use this skill when implementing or modifying the FastAPI backend for the college application guidance website.

## Scope
- API route creation and modification
- Student data submission and validation
- Data consolidation into JSON files
- File I/O for input/output data

## Workflow

1. **Define the Pydantic model** in `models/` — match the frontend form fields exactly
2. **Create the service function** in `services/` — one function per operation, stateless
3. **Add the route** in `main.py` or a router module — thin handler, delegates to service
4. **Wire up dependencies** — ensure `services/` and `models/` modules are importable

## Data Consolidation Pattern

When receiving form data, consolidate into a single JSON structure:

```python
# services/consolidator.py
from pathlib import Path
import json, uuid
from models.submission import StudentInfo

DATA_INPUT_DIR = Path("data/input")

async def consolidate_and_save(info: StudentInfo) -> Path:
    """Save consolidated student data to a JSON file and return the path."""
    DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_INPUT_DIR / f"{uuid.uuid4()}.json"
    async with aiofiles.open(filepath, "w") as f:
        await f.write(info.model_dump_json(indent=2))
    return filepath
```

## Validation
- Pydantic model covers all fields and types before the service layer runs
- Saved JSON is immediately readable and valid
- File paths use `pathlib.Path`, never string concatenation
- API responses use Pydantic response models for self-documentation

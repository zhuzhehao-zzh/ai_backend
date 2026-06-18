# College Application Guidance Backend

## Tech Stack
- **Runtime**: Python 3.11+
- **Framework**: FastAPI + Uvicorn
- **Validation**: Pydantic v2
- **Model**: OpenAI SDK (gpt-4o / gpt-4o-mini)
- **Config**: python-dotenv (.env)

## Data Flow
1. Frontend sends student info via POST → single `/api/submit` endpoint
2. Backend consolidates all fields into one structured JSON file (stored in `data/input/`)
3. The JSON file is read, combined with a prompt template, and sent to the LLM
4. LLM returns a structured report → saved to `data/output/` and returned to frontend

## Project Structure
```
ai_backend/
├── main.py              # FastAPI app entry point, router registration
├── models/              # Pydantic schemas
├── services/            # Business logic (consolidation, model call, report)
├── data/
│   ├── input/           # Consolidated student data files
│   └── output/          # Generated reports
├── prompts/             # LLM prompt templates (Markdown)
├── .codewhale/
│   └── instructions.md  # This file
├── requirements.txt
├── .env                 # API keys (git-ignored)
└── .gitignore
```

## API Conventions
- All responses use Pydantic response models
- Consistent error format: `{"error": {"code": "...", "message": "..."}}`
- Endpoints are async
- Input validated at the Pydantic layer

## Coding Conventions
- Type hints everywhere
- Services are stateless — receive input, return output
- File I/O is async where practical (aiofiles)
- Logging with Python's `logging` module, not print
- Separation: route handlers (thin) → services (logic) → model client (external)

## Verification
- `pytest` for unit/integration tests (future)
- Pydantic validation catches shape mismatches
- Manually: `curl` or the frontend to test endpoints

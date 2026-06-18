# AI Backend — College Application Guidance

A Python-based AI backend service that helps students fill out their college application preferences. It receives student information from a frontend, consolidates it, feeds it to a Large Language Model (LLM), and returns a structured report with university recommendations and action items.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Runtime** | Python 3.11+ |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/latest/) |
| **LLM Client** | [OpenAI SDK](https://github.com/openai/openai-python) (AsyncOpenAI) |
| **File I/O** | aiofiles (async) |
| **Config** | python-dotenv (`.env`) |

---

## Project Structure

```
ai_backend/
├── main.py                      # FastAPI entry point — app creation, router wiring, logging setup
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest configuration (asyncio_mode = auto)
├── .gitignore                   # Git ignore rules
├── .env                         # API keys & secrets (git-ignored, not committed)
│
├── models/                      # Pydantic schemas — request/response validation
│   └── submission.py            # StudentInfo, SubmitResponse, ErrorResponse
│
├── routes/                      # API route definitions (thin handlers)
│   └── api.py                   # POST /api/submit — the single submission endpoint
│
├── services/                    # Business logic (stateless, receive input → return output)
│   ├── consolidator.py          # Save validated student data to a JSON file on disk
│   ├── model_pipeline.py        # Load data + prompt → call LLM → parse JSON report
│   └── report_generator.py      # Save report to disk & return frontend-safe payload
│
├── prompts/                     # LLM prompt templates
│   └── admission-guide.md       # Template with all student fields + JSON output schema
│
├── data/                        # Runtime file storage (created automatically)
│   ├── input/                   # Consolidated student data JSON files
│   └── output/                  # Generated report JSON files
│
├── tests/                       # Pytest test suite
│   ├── conftest.py              # Test configuration (dummy API key, fixtures)
│   ├── test_models.py           # Pydantic model validation (required fields, ranges, defaults)
│   ├── test_consolidator.py     # Data consolidation & file output
│   ├── test_report_generator.py # Report structure & disk output
│   └── test_api.py              # Full integration test with mocked LLM
│
├── .codewhale/                  # CodeWhale AI assistant configuration
│   ├── instructions.md          # Project constitution (tech stack, conventions, data flow)
│   └── skills/                  # Custom skills for focused AI assistance
│       ├── college-admissions-backend/  # API patterns, data consolidation
│       ├── model-pipeline/              # LLM call & response parsing
│       └── report-generator/            # Report output & formatting
│
└── venv/                        # Python virtual environment (not committed)
```

---

## Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  User fills form → clicks "Submit" → POST /api/submit        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                 1. ROUTE (routes/api.py)                     │
│     Receives StudentInfo → validates via Pydantic            │
│     Thin handler, delegates everything to services           │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│             2. CONSOLIDATOR (services/consolidator.py)       │
│     Writes student JSON to data/input/{uuid}.json            │
│     (exclude_none=True — only saves provided fields)         │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│             3. MODEL PIPELINE (services/model_pipeline.py)   │
│     Reads data JSON + prompt template                        │
│     Renders template with student data                       │
│     Calls OpenAI (gpt-4o-mini, response_format=json_object)  │
│     Parses JSON response → recommendations + action_items    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│             4. REPORT GENERATOR (services/report_generator.py)│
│     Builds structured report (student_summary, recs, items)  │
│     Saves to data/output/{report_id}.json                    │
│     Returns frontend-safe payload (no raw model output)      │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                        RESPONSE                              │
│  { report_id, generated_at, student_summary,                 │
│    recommendations: [{university, major, match_score,        │
│                        rationale}],                          │
│    action_items: ["string", ...] }                            │
└──────────────────────────────────────────────────────────────┘
```

---

## API Reference

### `POST /api/submit`

Receives student form data and returns a college application guidance report.

**Request Body** (JSON):

```json
{
  "full_name": "Zhang Wei",
  "email": "zhangwei@example.com",
  "phone": "13800138000",
  "date_of_birth": "2006-05-15",
  "high_school": "Beijing No.4 High School",
  "graduation_year": 2025,
  "gpa": 3.8,
  "sat_score": 1450,
  "act_score": null,
  "intended_majors": ["Computer Science", "Mathematics"],
  "coursework": ["AP Calculus BC", "AP Physics C"],
  "preferred_regions": ["California", "New York"],
  "budget_range": "30k-60k",
  "extracurriculars": ["Math Club President", "Varsity Basketball"],
  "awards": ["National Math Olympiad Finalist"],
  "personal_statement": "I want to combine AI and healthcare..."
}
```

**Required fields**: `full_name`, `email`, `high_school`, `gpa`

**Validation rules**:
| Field | Constraint |
|---|---|
| `full_name` | min length 1 |
| `gpa` | 0.0 – 4.0 |
| `sat_score` | 400 – 1600 |
| `act_score` | 1 – 36 |
| `graduation_year` | 2024 – 2030 |
| `personal_statement` | max 5000 characters |

**Success Response** (200):

```json
{
  "report_id": "a1b2c3d4-...",
  "generated_at": "2026-06-18T22:00:00+00:00",
  "student_summary": {
    "full_name": "Zhang Wei",
    "email": "zhangwei@example.com",
    "high_school": "Beijing No.4 High School",
    "gpa": 3.8,
    "intended_majors": ["Computer Science"]
  },
  "recommendations": [
    {
      "university": "Stanford",
      "major": "Computer Science",
      "match_score": 0.85,
      "rationale": "Strong academic record aligns well."
    }
  ],
  "action_items": [
    "Prepare personal statement by October 15",
    "Request recommendation letters by November 1"
  ]
}
```

**Error Response** (422 — validation error):

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "gpa"],
      "msg": "Input should be greater than or equal to 0",
      "input": -0.5
    }
  ]
}
```

**Error Response** (500 — internal error):

```json
{
  "detail": {
    "code": "INTERNAL_ERROR",
    "message": "Description of what went wrong"
  }
}
```

---

## Setup

### Prerequisites

- Python 3.11+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd ai_backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set your API key
echo "OPENAI_API_KEY=sk-..." > .env
```

### Run the server

```bash
python3 main.py
```

Server starts at `http://localhost:8000`. Docs are at `http://localhost:8000/docs`.

### Test it with curl

```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Zhang Wei",
    "email": "zhangwei@example.com",
    "high_school": "Beijing No.4 High School",
    "gpa": 3.8,
    "sat_score": 1450,
    "intended_majors": ["Computer Science"]
  }'
```

---

## Testing

The test suite covers **27 test cases** across 4 test files:

| File | Tests | Focus |
|---|---|---|
| `tests/test_models.py` | 12 | Pydantic validation — required fields, value ranges, defaults, max lengths |
| `tests/test_consolidator.py` | 4 | File creation, JSON data fidelity, `exclude_none` behavior, directory creation |
| `tests/test_report_generator.py` | 5 | Report structure, `student_summary` filtering, disk output, empty defaults |
| `tests/test_api.py` | 7 | Full integration: success path, validation errors, file I/O chain, response structure |

### Run tests

```bash
# From project root with venv activated
./venv/bin/pytest

# With verbose output
./venv/bin/pytest -v

# Run a specific test file
./venv/bin/pytest tests/test_models.py
```

Tests use:
- `tmp_path` — isolated temp directories so no real data is touched
- `monkeypatch` — replaces module-level paths and the OpenAI call with mocks
- `AsyncMock` — simulates the LLM response without calling the real API

---

## Configuration

| Environment variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key for LLM calls |

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-key-here
```

---

## Skills & Prompts (for AI-assisted development)

This project includes configuration files that enhance AI assistant (CodeWhale) sessions:

- **`.codewhale/instructions.md`** — Persistent project constitution. Tells the AI about the tech stack, data flow, project structure, and coding conventions every session.
- **`.codewhale/skills/college-admissions-backend/SKILL.md`** — API endpoint patterns, data consolidation workflow
- **`.codewhale/skills/model-pipeline/SKILL.md`** — LLM call patterns, prompt rendering, response parsing
- **`.codewhale/skills/report-generator/SKILL.md`** — Report structure definition, output formatting

These travel with the repo — any AI assistant that supports CodeWhale or OpenCode will discover them automatically.

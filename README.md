# AI Backend — College Application Guidance

A Python-based AI backend service that helps students fill out their college application preferences. It receives student information from a frontend, consolidates it, feeds it to a Large Language Model (LLM), and returns a structured report with university recommendations and action items.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Runtime** | Python 3.11+ |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/latest/) |
| **LLM Client** | [OpenAI SDK](https://github.com/openai/openai-python) (AsyncOpenAI, pointed at Moonshot AI) |
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
│     Calls Kimi (moonshot-v1-8k, response_format=json_object)  │
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

Receives student Gaokao (高考) information and returns a college guidance report.

**Request Body** (JSON):

```json
{
  "subjectTrack": "理科",
  "province": "广东",
  "score": 610,
  "interests": "写代码、研究 AI、解决工程问题",
  "skills": "数学能力、逻辑推理、自学能力",
  "preferences": "高收入潜力、技术壁垒、稳定性",
  "preferredCities": ["深圳", "杭州"],
  "dislikes": "不想学医、不接受高压行业"
}
```

**Required fields**: `subjectTrack`, `province`, `score`, `interests`, `skills`, `preferences`, `dislikes`

**Validation rules**:
| Field | Constraint |
|---|---|
| `score` | 0 – 750 |
| `province` | min length 1 |

**Success Response** (200):

```json
{
  "report_id": "a1b2c3d4-...",
  "generated_at": "2026-06-19T21:00:00+00:00",
  "profileSummary": {
    "cluster": "技术探索型",
    "province": "广东",
    "score": "610",
    "subjectTrack": "理科",
    "preferredCities": ["深圳", "杭州"]
  },
  "top": [
    {
      "id": "software-engineering",
      "name": "软件工程",
      "recommendationBand": "强推荐",
      "matchScore": 96,
      "aiRisk": "低",
      "outlook": "稳定增长，但基础编码岗位门槛提高",
      "competitiveness": 94,
      "summary": "学生的逻辑能力和 AI 兴趣高度匹配",
      "schoolStrategy": "优先考虑计算机学科实力强、产业资源丰富的城市",
      "cities": [{"name": "深圳", "note": "AI 应用、智能硬件和金融科技岗位密集"}],
      "companies": [{"name": "华为"}, {"name": "腾讯"}],
      "roles": [
        {
          "id": "ai-application-engineer",
          "name": "AI 应用工程师",
          "currentDemand": "企业需要能把大模型能力接入真实业务的人才",
          "requirements": ["Python", "大模型 API", "Web 开发"]
        }
      ],
      "yearPlan": {
        "year1": ["学习 Python 或 Java", "学习高等数学和线性代数"],
        "year2": ["学习数据结构与算法", "掌握数据库和计算机网络"],
        "year3": ["学习机器学习和大模型应用", "完成 AI 项目"],
        "year4": ["准备校招笔试面试", "复盘实习项目"]
      }
    }
  ],
  "cautious": [],
  "all": []
}
```

**Error Response** (422 — validation error):

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "score"],
      "msg": "Input should be less than or equal to 750",
      "input": 800
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
- A [Moonshot AI (Kimi) API key](https://platform.moonshot.ai/)

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
echo "MOONSHOT_API_KEY=sk-..." > .env
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
    "subjectTrack": "理科",
    "province": "广东",
    "score": 610,
    "interests": "写代码、研究 AI",
    "skills": "数学能力、逻辑推理",
    "preferences": "高收入潜力、技术壁垒",
    "preferredCities": ["深圳", "杭州"],
    "dislikes": "不想学医"
  }'
```

---

## Testing

The test suite covers **23 test cases** across 4 test files:

| File | Tests | Focus |
|---|---|---|
| `tests/test_models.py` | 7 | Pydantic validation — required fields, score range (0-750), empty defaults |
| `tests/test_consolidator.py` | 4 | File creation, JSON data fidelity, optional fields, directory creation |
| `tests/test_report_generator.py` | 5 | Report wrapping, `profileSummary`/`top`/`cautious`/`all` pass-through, yearPlan validation |
| `tests/test_api.py` | 7 | Full integration: success path, rich nested response, validation errors, file I/O chain |

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
- `monkeypatch` — replaces module-level paths and the LLM call with mocks
- `AsyncMock` — simulates the LLM response without calling the real API

---

## Configuration

| Environment variable | Required | Description |
|---|---|---|
| `MOONSHOT_API_KEY` | Yes | Your Moonshot AI (Kimi) API key |
| `MOONSHOT_BASE_URL` | No | API base URL (default: `https://api.moonshot.ai/v1`) |
| `MOONSHOT_MODEL` | No | Model ID (default: `moonshot-v1-8k`) |

Create a `.env` file in the project root:

```
MOONSHOT_API_KEY=sk-your-key-here
```

---

## Skills & Prompts (for AI-assisted development)

This project includes configuration files that enhance AI assistant (CodeWhale) sessions:

- **`.codewhale/instructions.md`** — Persistent project constitution. Tells the AI about the tech stack, data flow, project structure, and coding conventions every session.
- **`.codewhale/skills/college-admissions-backend/SKILL.md`** — API endpoint patterns, data consolidation workflow
- **`.codewhale/skills/model-pipeline/SKILL.md`** — LLM call patterns, prompt rendering, response parsing
- **`.codewhale/skills/report-generator/SKILL.md`** — Report structure definition, output formatting

These travel with the repo — any AI assistant that supports CodeWhale or OpenCode will discover them automatically.

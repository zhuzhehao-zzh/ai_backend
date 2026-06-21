# AI Backend — College Application Guidance (Gaokao)

A Python-based AI backend service that helps Chinese students make informed college application decisions based on their Gaokao (高考) scores. It accepts arbitrary student data, queries a local knowledge base (university rankings, admission scores, major details) via LLM function calling, and returns a structured report with personalized recommendations, career outlook, and a 4-year study plan.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Runtime** | Python 3.11+ |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **LLM Client** | [OpenAI SDK](https://github.com/openai/openai-python) (AsyncOpenAI, pointed at Moonshot AI / Kimi) |
| **Database** | MySQL 8.0 + aiomysql (async pool) |
| **Validation** | Pydantic v2 (output only) |
| **File I/O** | aiofiles (async) |
| **Config** | python-dotenv (`.env`) |

---

## Project Structure

```
ai_backend/
├── main.py                      # FastAPI entry point, logging setup, DB pool lifecycle
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest config
├── DEPLOY.md                    # Cloud deployment & systemd guide
├── .gitignore
├── .env                         # API keys & DB credentials (git-ignored)
│
├── models/
│   └── submission.py            # SubmitResponse (output model with profileSummary/top/cautious/all)
│
├── routes/
│   └── api.py                   # POST /api/submit + POST /api/feedback
│
├── services/
│   ├── consolidator.py          # Save raw JSON to data/input/
│   ├── model_pipeline.py        # 3-phase workflow: Explore → Analyze → Report (with function calling)
│   ├── report_generator.py      # Save final report to data/output/
│   ├── database.py              # MySQL connection pool & CRUD (requests, responses, feedback)
│   ├── history_service.py       # Historical pattern computation from past feedback
│   ├── security.py              # Rate limiting, injection detection, prompt boundaries
│   └── knowledge_service.py     # Knowledge base tools (callable by Kimi via function calling)
│
├── prompts/
│   └── admission-guide.md       # LLM prompt template
│
├── data/
│   ├── input/                   # Raw student data (JSON)
│   ├── output/                  # Generated reports (JSON)
│   └── knowledge/               # Knowledge base files
│       ├── universities.json    # 985/211/双一流 university list
│       ├── admission_scores.json# 2024 admission cutoffs by province
│       └── majors.json          # Major details: AI risk, outlook, companies, roles
│
├── scripts/
│   └── test_cloud.py            # Full integration test suite (run via SSH)
│
├── tests/                       # 17 pytest test cases
│
└── .codewhale/                  # AI assistant config (instructions + skills)
```

---

## How It Works — 3-Phase Pipeline

```
Frontend POST /api/submit
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 1. SECURITY CHECK                               │
│    ├── Rate limit (20 req/min per IP)           │
│    ├── JSON depth validation                     │
│    └── Prompt injection scan                    │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ 2. SAVE TO DISK & DB                            │
│    ├── Raw JSON → data/input/{uuid}.json        │
│    └── MySQL: requests table                    │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ 3. 3-PHASE LLM WORKFLOW                         │
│                                                  │
│  Phase 1 — EXPLORATION                          │
│    Kimi calls our tools:                        │
│    ├── get_admission_scores(province, score)    │
│    ├── get_major_details(interests)             │
│    └── get_university_info(city)                │
│                                                  │
│  Phase 2 — DEEP ANALYSIS                        │
│    Kimi analyzes: AI risk, outlook, schools,    │
│    companies, learning paths for each option    │
│                                                  │
│  Phase 3 — FINAL REPORT                         │
│    Kimi generates structured JSON:              │
│    { profileSummary, top[], cautious[], all[] } │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│ 4. SAVE & RETURN                                │
│    ├── Report → data/output/{uuid}.json         │
│    ├── MySQL: responses table                   │
│    └── Return to frontend                       │
└─────────────────────────────────────────────────┘
```

---

## API Reference

### `POST /api/submit`

Accepts any JSON object with student information. Field-agnostic — the LLM determines which fields are meaningful.

**Request** (any JSON):
```json
{
  "subjectTrack": "理科",
  "province": "广东",
  "score": 610,
  "interests": "写代码、研究 AI",
  "skills": "数学能力、逻辑推理",
  "preferences": "高收入潜力、技术壁垒",
  "preferredCities": ["深圳", "杭州"],
  "dislikes": "不想学医"
}
```

**Response** (200):
```json
{
  "report_id": "uuid",
  "generated_at": "2026-06-21T10:00:00Z",
  "profileSummary": {
    "cluster": "技术探索型",
    "province": "广东",
    "score": "610",
    "subjectTrack": "理科",
    "preferredCities": ["深圳"]
  },
  "top": [
    {
      "id": "computer-science",
      "name": "计算机科学与技术",
      "recommendationBand": "强推荐",
      "matchScore": 95,
      "aiRisk": "低",
      "outlook": "就业面最广，薪资高，AI时代核心专业",
      "competitiveness": 90,
      "summary": "与学生的兴趣和高分匹配",
      "schoolStrategy": "优先选择深圳大学和南方科技大学",
      "cities": [{"name": "深圳", "note": "高新技术企业密集"}],
      "companies": [{"name": "华为"}, {"name": "腾讯"}],
      "roles": [{"id": "swe", "name": "软件工程师", "currentDemand": "高", "requirements": ["Java", "Python", "数据结构"]}],
      "yearPlan": {
        "year1": ["打好编程基础", "学习算法和数据结构"],
        "year2": ["参与实际项目", "提升实践能力"],
        "year3": ["实习于知名IT企业", "积累工作经验"],
        "year4": ["准备毕业设计", "关注行业动态", "准备就业"]
      }
    }
  ],
  "cautious": [],
  "all": []
}
```

### `POST /api/feedback`

Record user feedback for a generated report.

**Request:**
```json
{
  "response_id": "uuid-from-report",
  "rating": 4,
  "comment": "推荐很准确"
}
```

**Response:** `{"status": "ok", "message": "Feedback recorded"}`

---

## Setup

```bash
# Clone
git clone <repo-url>
cd ai_backend

# Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
echo "MOONSHOT_API_KEY=sk-your-kimi-key" > .env
echo "MOONSHOT_BASE_URL=https://api.moonshot.cn/v1" >> .env

# MySQL (see DEPLOY.md for full setup)
echo "DB_HOST=localhost" >> .env
echo "DB_USER=aibackend" >> .env
echo "DB_PASS=Aibackend2024!" >> .env
echo "DB_NAME=ai_backend" >> .env

# Run
python main.py
```

---

## Testing

```bash
# Unit tests (17 test cases)
./venv/bin/pytest -v

# Full cloud integration test (via SSH)
./venv/bin/python scripts/test_cloud.py --ssh
```

---

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `MOONSHOT_API_KEY` | Yes | — | Kimi API key |
| `MOONSHOT_BASE_URL` | No | `https://api.moonshot.ai/v1` | Kimi API endpoint |
| `MOONSHOT_MODEL` | No | `moonshot-v1-8k` | Kimi model name |
| `DB_HOST` | No | `localhost` | MySQL host |
| `DB_PORT` | No | `3306` | MySQL port |
| `DB_USER` | No | `aibackend` | MySQL user |
| `DB_PASS` | No | `Aibackend2024!` | MySQL password |
| `DB_NAME` | No | `ai_backend` | MySQL database |
| `LOG_DIR` | No | `/root/Desktop/career/log` | Log file directory |
| `DEV` | No | — | Set to `true` for hot-reload |

---

## Security

| Layer | Protection |
|---|---|
| Rate limiting | 20 requests/min per IP |
| JSON depth check | Max 6 levels nesting |
| Key/array limits | Max 50 keys, 100 items per array |
| Prompt injection scan | Detects "ignore instructions", "system prompt" etc. |
| Prompt boundaries | Student data wrapped in `[学生数据开始]/[学生数据结束]` |

## Knowledge Base

The system includes curated reference data files in `data/knowledge/`:

| File | Content |
|---|---|
| `universities.json` | 37 key universities with 985/211/双一流 tiers, cities, types |
| `admission_scores.json` | 2024 admission cutoffs for 5+ provinces |
| `majors.json` | 11 major categories with AI risk, outlook, companies, roles, requirements |

Kimi queries this data dynamically via function calling — only what's needed per student.

## Deployment

See `DEPLOY.md` for full production deployment guide (Nginx, systemd, MySQL, HTTPS).

Quick commands on cloud server:
```bash
cd /root/Desktop/career/ai_backend
sudo git pull origin main
sudo pkill -f "python.*main.py"
sudo nohup ./venv/bin/python -u main.py > /tmp/server.log 2>&1 &
```

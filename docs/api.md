# API Reference

## Base URL

- **Production**: `http://101.43.30.20`
- **Local**: `http://localhost:8000`

---

## Endpoints

### `GET /`

Server status check.

**Response:**
```json
{"message": "AI Backend is running"}
```

---

### `GET /health`

Health check for monitoring.

**Response:**
```json
{"status": "ok"}
```

---

### `POST /api/submit`

Submit student Gaokao information and receive a personalized college guidance report.

**Request:** Accepts any JSON object (field-agnostic).

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

**Response (200):**
```json
{
  "report_id": "uuid",
  "generated_at": "ISO-8601",
  "profileSummary": {
    "cluster": "学生类型标签",
    "province": "广东",
    "score": "610",
    "subjectTrack": "理科",
    "preferredCities": ["深圳"]
  },
  "top": [
    {
      "id": "major-id",
      "name": "专业名",
      "recommendationBand": "强推荐/推荐/可选",
      "matchScore": 0-100,
      "aiRisk": "低/中/高",
      "outlook": "行业前景",
      "competitiveness": 0-100,
      "summary": "匹配理由",
      "schoolStrategy": "择校策略",
      "cities": [{"name": "城市", "note": "产业特点"}],
      "companies": [{"name": "目标公司"}],
      "roles": [{"id": "role-id", "name": "岗位", "currentDemand": "需求", "requirements": ["技能"]}],
      "yearPlan": {"year1": ["建议"], "year2": ["建议"], "year3": ["建议"], "year4": ["建议"]}
    }
  ],
  "cautious": [],
  "all": []
}
```

**Security:**
- Rate limited: 20 requests/min per IP
- JSON depth checked (max 6 levels)
- Prompt injection scanned
- Request logged with client IP

---

### `POST /api/feedback`

Record user feedback (rating) for a generated report. Used for historical pattern learning.

**Request:**
```json
{
  "response_id": "uuid-from-report",
  "rating": 4,
  "comment": "推荐很准确（可选）"
}
```

**Response:**
```json
{"status": "ok", "message": "Feedback recorded"}
```

---

### `GET /api/stats`

Return real-time usage statistics.

**Response:**
```json
{
  "total_requests": 42,
  "unique_ips": 15
}
```

Note: Counters reset on server restart. IPs from `X-Forwarded-For` header when behind proxy.

---

## API Flow

```
POST /api/submit
  │
  ├─ Security check (rate limit, injection scan)
  ├─ Save student data to disk + MySQL
  ├─ Phase 1: Kimi explores (queries tools for scores, majors, universities)
  ├─ Phase 2: Kimi analyzes (deep-dive into options)
  ├─ Phase 3: Kimi generates structured JSON report
  ├─ Save report to disk + MySQL
  └─ Return report to frontend

POST /api/feedback
  │
  ├─ Save rating + comment to MySQL
  └─ (Used later for historical pattern injection)

GET /api/stats
  │
  └─ Return in-memory counters
```

## Data Flow (Knowledge Tools)

Kimi can call these tools during Phase 1 & 2:

| Tool | Description | Source |
|---|---|---|
| `get_admission_scores(province, score)` | Query admission cutoffs for matching universities | `data/knowledge/admission_scores.json` |
| `get_university_info(city, name)` | Look up university tier, city, type | `data/knowledge/universities.json` |
| `get_university_details(name)` | Detailed per-university data: major scores, employment, rankings | `data/knowledge/universities/*.json` |
| `get_major_details(interest_keywords)` | Query major outlook, AI risk, target companies, skills | `data/knowledge/majors.json` |

---
name: model-pipeline
description: Implement the data-to-model pipeline. Use when calling the LLM with consolidated student data, managing prompt templates, or parsing the model response into a structured report.
---

# Model Pipeline Skill

Use this skill when implementing the pipeline that feeds consolidated student data to the LLM and parses the response.

## Scope
- LLM client setup (OpenAI SDK)
- Prompt template loading and rendering
- Model invocation with consolidated data
- Response parsing into structured report

## Assumptions
- Model: OpenAI gpt-4o / gpt-4o-mini (configured via `OPENAI_API_KEY` in `.env`)
- Prompt templates stored in `prompts/` as `.md` or `.j2` files
- Model response is expected in a structured format (JSON or markdown sections)

## Workflow

1. **Load prompt template** from `prompts/` directory
2. **Render template** with consolidated student data (JSON fields)
3. **Call the model** via OpenAI SDK with the rendered prompt
4. **Parse response** — extract structured sections from the model output
5. **Return parsed report** to the caller

## Key Pattern

```python
# services/model_pipeline.py
from openai import AsyncOpenAI
from pathlib import Path
import json

client = AsyncOpenAI()  # reads OPENAI_API_KEY from env

async def generate_report(data_path: Path, prompt_template_path: Path) -> dict:
    # 1. Load data
    data = json.loads(data_path.read_text())

    # 2. Load and render prompt
    template = prompt_template_path.read_text()
    prompt = template.format(**data)  # or use Jinja2

    # 3. Call model
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    # 4. Parse response
    report = json.loads(response.choices[0].message.content)
    return report
```

## Validation
- Prompt template renders without KeyError for all required fields
- Model response is valid JSON (when `response_format` is used)
- API key is loaded from `.env`, not hardcoded
- Errors from OpenAI (rate limits, auth) are caught and surfaced clearly

# Enterprise AI Platform

The central portfolio project. The current release is a tested FastAPI incident backend with domain rules and interchangeable in-memory/PostgreSQL persistence.

## Current Architecture

```text
HTTP request → Pydantic schema → FastAPI route → IncidentService
                                               → Incident domain rules
                                               → repository
                                                   ├── in-memory
                                                   └── PostgreSQL
```

Docker packaging is scheduled for Week 4; Hugging Face inference for Week 5.

## Run with the existing environment

```bash
lab-pt
cd "$HOME/ai-systems-lab/projects/enterprise-ai-platform"
python -m pip install -e '.[dev]'
uvicorn enterprise_ai_platform.api:app --reload
```

No new virtual environment is required or expected.

## Verify

```bash
pytest
```

Open `http://127.0.0.1:8000/docs` for the API contract.

## PostgreSQL

With the local development database running:

```bash
export DATABASE_URL='postgresql+psycopg://enterprise_ai:enterprise_ai_dev@localhost:5432/enterprise_ai'
alembic upgrade head
pytest
uvicorn enterprise_ai_platform.api:app --reload
```

## Current Limitations

- no authentication, pagination or audit trail yet
- no model or agent is integrated yet
- readiness currently checks application availability only

These limitations map directly to later roadmap milestones rather than being hidden.

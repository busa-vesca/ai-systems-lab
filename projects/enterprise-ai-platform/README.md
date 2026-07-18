# Enterprise AI Platform

The central portfolio project. The current release is a real, tested FastAPI incident backend with domain rules and in-memory persistence. Planned layers are added one milestone at a time.

## Current Architecture

```text
HTTP request → Pydantic schema → FastAPI route → IncidentService
                                               → Incident domain rules
                                               → in-memory store
```

PostgreSQL is intentionally scheduled for Week 3; Docker for Week 4; Hugging Face for Week 5.

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

## Current Limitations

- data is lost when the process restarts
- no authentication, pagination or audit trail yet
- no model or agent is integrated yet
- readiness currently checks application availability only

These limitations map directly to later roadmap milestones rather than being hidden.

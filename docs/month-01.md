# Month 1 — Production Backend Foundation

## Outcome

Build and understand the first production layers of `projects/enterprise-ai-platform` without repeating environment setup.

**Status:** the four engineering milestones below are implemented. This file is
the Month 1 learning record, not a list of future claims.

```text
Week 1  domain and service logic
Week 2  FastAPI and API tests
Week 3  PostgreSQL and migrations
Week 4  Docker runtime
```

Hugging Face starts in Week 5. PostgreSQL, Docker and model inference are separate stages.

## Environment Contract

- Activate the existing environment with `lab-pt`.
- Do not create, move, symlink or teach `.venv`/`.venv-pt`.
- Do not troubleshoot the environment unless a concrete command fails.
- Install only dependencies needed by the current milestone.

## Week 1 — Domain and Service

Read and extend the existing incident code. Focus on dataclasses/enums, type hints, validation, explicit exceptions, service methods and state transitions. Tests must cover valid and invalid behavior.

Done when the owner can explain object creation, lookup, update, error paths and why the service owns workflow rules.

## Week 2 — FastAPI

Use the implemented API as the learning surface. Trace JSON → Pydantic schema → service → domain object → response. Extend tests before adding endpoints.

Done when create/list/fetch/update, 404s and invalid transitions are tested and explainable. Storage stays in memory.

## Week 3 — PostgreSQL

Add SQLAlchemy models and a PostgreSQL repository, Alembic migration, constraints, sessions/transactions, pagination and database integration tests. Do not add Docker or a model in the same milestone.

Completed: migrations build a clean schema and the repository/API integration
tests run against PostgreSQL.

## Week 4 — Docker

Add a non-root image, Compose for API + PostgreSQL, environment configuration, health checks and verified clean-start commands. Do not add Hugging Face yet.

Completed: Compose starts API and PostgreSQL, migrations run automatically, the
container runs as a non-root user, readiness passes and database/model volumes
persist across restarts.

## Career Outputs This Month

- Week 1: inventory existing ML/CV/Jetson/Linux evidence
- Week 2: draft two measurable CV bullets and STAR stories
- Week 3: update LinkedIn/GitHub positioning
- Week 4: compare the portfolio against 10 current target vacancies

## Teaching Contract

Use working code, not setup rituals. Explain one concept, trace it in the project, give one bounded task, review the result, then continue. Never claim a planned layer already exists.

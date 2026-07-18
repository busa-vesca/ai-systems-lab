# Month 1 — Production Python, FastAPI and PostgreSQL

## Outcome

By the end of Month 1, ship a containerized backend service that demonstrates production-oriented Python engineering and includes a small Hugging Face Transformer integration.

## Project: Incident Intelligence API

The service manages operational incidents and exposes a first AI capability for classification or summarization.

### Core entities

- User
- Incident
- IncidentEvent
- ModelPrediction

### Minimum API

```text
GET    /health
GET    /ready
POST   /incidents
GET    /incidents/{incident_id}
GET    /incidents
PATCH  /incidents/{incident_id}
POST   /incidents/{incident_id}/classify
```

### Required engineering features

- Python package structure
- type hints
- Pydantic settings
- FastAPI schemas and dependencies
- PostgreSQL
- SQLAlchemy 2.x
- Alembic migrations
- repository and service layers
- structured logging
- consistent error responses
- request correlation ID
- unit and integration tests
- Dockerfile and Docker Compose
- Ruff and mypy
- GitHub Actions CI
- Hugging Face model isolated behind an interface

## Week 1 — Python Engineering Core

### Learn

- packages, modules and imports
- type hints and static checking
- classes, dataclasses and protocols
- dependency inversion at a practical level
- configuration through environment variables
- domain-specific exceptions
- logging
- pytest fixtures and parametrization

### Build

Create a domain package for incidents with:

- typed entities
- status enum
- validation rules
- in-memory repository
- service methods
- CLI commands
- unit tests

### Acceptance criteria

- `pytest` passes
- `ruff check .` passes
- `mypy` passes on application code
- invalid incident transitions raise clear domain errors
- logs are structured and contain useful context

## Week 2 — FastAPI

### Learn

- HTTP methods and status codes
- Pydantic request and response models
- FastAPI dependency injection
- sync versus async handlers
- exception handlers
- middleware
- OpenAPI documentation
- API testing with TestClient/httpx

### Build

Expose the incident service through REST endpoints.

### Acceptance criteria

- all endpoints have explicit response models
- invalid input produces predictable error JSON
- `/health` reports process health
- `/ready` reports dependency readiness
- API behavior is covered by tests

## Week 3 — PostgreSQL

### Learn

- tables, keys, constraints and indexes
- transactions
- SQLAlchemy 2.x sessions and models
- Alembic migrations
- integration testing against PostgreSQL

### Build

Replace the in-memory repository with PostgreSQL while preserving the service interface.

### Acceptance criteria

- a fresh database can be created only from migrations
- duplicate and missing-resource cases are handled
- transactions rollback on failure
- list queries support pagination
- integration tests verify persistence

## Week 4 — Docker, CI and First Transformer

### Learn

- Docker layers and image caching
- Compose networking
- environment and secret handling
- non-root containers
- CI checks
- Hugging Face `pipeline()`
- model revision pinning
- inference latency measurement

### Build

Add an incident classification or summarization endpoint using a small Hugging Face model.

The model must be loaded once at application startup or lazily cached—not once per request.

### Acceptance criteria

- `docker compose up --build` starts API and PostgreSQL
- migrations run predictably
- the container does not run as root
- CI runs lint, type checks and tests
- the model name and revision are configurable
- inference latency is logged
- model failures return a controlled service error
- README contains setup and curl examples

## Daily 5-Hour Structure

```text
2 h  implement the current feature
1 h  focused concept lesson
1 h  tests, refactoring and debugging
1 h  algorithms, SQL or interview review
```

## Weekly Review

At the end of each week, produce:

- working code
- passing tests
- one architecture note
- one failure example and its fix
- one concise GitHub progress summary
- five interview questions answered aloud

## Month 1 Definition of Done

Month 1 is complete when a new developer can clone the repository, follow the README, start the system with Docker Compose, create and query incidents, invoke the Transformer endpoint, run the test suite and understand the architecture without private instructions.

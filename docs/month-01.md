# Month 1 — Code-First Production Python

## Goal

Build one small Incident Tracker gradually, understand every line, then turn the same logic into a tested API with persistence.

The month is intentionally ordered as:

```text
plain Python
→ tests and modules
→ FastAPI
→ PostgreSQL and Docker
→ first Hugging Face endpoint
```

Infrastructure must not appear before the code it supports is understood.

## Week 1 — Incident Tracker in one Python file

### Learn

- `dataclass`
- `Enum`
- type hints
- attributes and methods
- validation
- explicit exceptions
- lists of objects
- finding and updating objects

### Build

Start with one file: `incident_tracker.py`.

It should gradually contain:

- `IncidentStatus`
- `Incident`
- incident creation
- status transitions
- validation rules
- custom errors
- list storage
- search by ID
- update logic

### Rules

- no `pyproject.toml` at the beginning
- no package layout at the beginning
- no Ruff or mypy as a learning gate
- no Docker, database, FastAPI or Hugging Face
- no diagnostic commands without a concrete problem
- one new concept per step

### Definition of Done

- the file runs directly with Python
- the learner can explain every class, field and function
- invalid data raises a clear error
- incidents can be created, listed, found and updated
- at least three failure cases are demonstrated

## Week 2 — Modules and unit tests

### Learn

- small functions
- imports
- `if __name__ == "__main__"`
- separation into 2–3 files
- pytest basics
- assertions
- test naming
- fixtures only when they remove repetition
- parametrization only when it improves clarity

### Build

Move the understood one-file program into a minimal structure such as:

```text
incident_tracker/
├── models.py
├── service.py
└── main.py

tests/
└── test_incidents.py
```

Only after this works:

- create a virtual environment
- add a minimal dependency file or `pyproject.toml`
- add Ruff
- consider mypy as a useful check, not a blocker

### Definition of Done

- tests cover success and failure paths
- imports are understood
- the CLI or direct entry point works
- no unnecessary architectural layers exist

## Week 3 — FastAPI

### Learn

- HTTP request and response
- REST resources
- methods and status codes
- Pydantic schemas
- path and query parameters
- exception handlers
- dependency injection in a simple form
- API testing

### Build

Expose the existing Incident Tracker logic through:

```text
GET    /health
POST   /incidents
GET    /incidents
GET    /incidents/{incident_id}
PATCH  /incidents/{incident_id}
```

Use in-memory storage first.

### Definition of Done

- endpoints call already understood Python logic
- validation errors are predictable
- missing incidents return a controlled response
- API tests cover the core paths
- OpenAPI docs work

## Week 4 — PostgreSQL, Docker and first Transformer

### Learn

- tables and rows
- primary keys and constraints
- basic SQL
- SQLAlchemy models and sessions
- Alembic migrations
- Docker image and Compose networking
- Hugging Face `pipeline()` basics
- model loading once, not per request

### Build

1. Replace in-memory storage with PostgreSQL.
2. Add a Dockerfile and Compose for API + database.
3. Only after the backend is stable, add one small endpoint:

```text
POST /incidents/{incident_id}/classify
```

The Transformer must be hidden behind a small service function or class and cached after loading.

### Definition of Done

- migrations create a fresh database
- API and database start through Docker Compose
- tests still pass
- model failures are controlled
- model is not loaded on every request
- README contains only commands that were actually tested

## Daily Rhythm

```text
2 h  write and understand project code
1 h  focused explanation of the current concept
1 h  tests, debugging and refactoring
1 h  algorithms, SQL or interview review
```

## Teaching Contract

Every lesson must follow this sequence:

1. Explain one concept simply.
2. Show one tiny unrelated example.
3. Give one practical task in the project.
4. Wait for the learner's answer.
5. Review the code and explain mistakes.
6. Add tooling only when the code creates a real need for it.

A lesson is unsuccessful when most of the time is spent checking files, environments or configuration instead of reading and writing Python.

## Month 1 Result

At the end of the month, the learner should be able to explain the full evolution:

```text
one Python file
→ modules and tests
→ REST API
→ PostgreSQL persistence
→ Docker deployment
→ cached Transformer inference
```

Understanding and explanation are required; mere repository structure is not evidence of skill.
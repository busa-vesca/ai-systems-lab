# Production AI Engineer Roadmap

## Mission

Become interview-ready for Production / Enterprise AI Engineer roles in 12 weeks and job-ready within 3–5 months.

Study capacity: approximately 5 focused hours per day, 6 days per week.

## Operating Principles

1. Learn through working code, not infrastructure rituals.
2. Add only one major concept at a time.
3. Do not introduce tooling before it solves a real problem.
4. Every week must produce code that can be explained without notes.
5. Begin interview preparation early, but keep the main project focused.
6. Treat tests, evals, deployment and documentation as later layers built on understood code.

## Weekly Time Budget

```text
2 h  main project code
1 h  focused Python/backend concept
1 h  tests, debugging and refactoring
1 h  algorithms, SQL or interview review
```

## Month 1 — Production Python First

### Week 1: Incident Tracker in one file

- dataclass
- Enum
- type hints
- object creation
- methods
- validation
- explicit exceptions
- lists of objects
- search and update logic

Deliverable: a readable `incident_tracker.py` that creates, finds and updates incidents.

No `pyproject.toml`, package layout, linters, Docker, database or framework setup during the first learning steps.

### Week 2: Functions, modules and tests

- split large logic into small functions
- separate code into 2–3 modules only after the one-file version is understood
- imports and `__main__`
- pytest basics
- fixtures and parametrization only when useful
- error cases
- simple CLI

Deliverable: small multi-file Incident Tracker with meaningful unit tests.

Tooling may be added only at the end of the week: virtual environment, minimal dependency file and Ruff. `mypy` is optional, not a blocker.

### Week 3: FastAPI Foundation

- HTTP and REST fundamentals
- Pydantic request/response models
- status codes
- exception handlers
- dependency injection at a basic practical level
- health endpoint
- API tests

Deliverable: tested FastAPI API using the already understood Incident Tracker logic and an in-memory store.

### Week 4: PostgreSQL and Docker basics

- SQL fundamentals
- tables, keys and constraints
- SQLAlchemy 2.x basics
- migrations with Alembic
- replace in-memory storage with PostgreSQL
- Dockerfile and Compose
- one small Hugging Face `pipeline()` endpoint only after the backend works

Deliverable: API + PostgreSQL started through Docker Compose, with tests and a small cached Transformer integration.

## Month 2 — Hugging Face and Enterprise Agents

### Week 5: Transformers in Production

- AutoTokenizer and AutoModel
- tokenization, padding, truncation and attention masks
- text classification and embeddings
- model loading and caching
- CPU/GPU device selection
- batching and latency measurement
- model cards and Hub revisions

Deliverable: versioned Hugging Face inference service with tests and benchmarks.

### Week 6: Tool Calling

- structured outputs
- tool schemas
- validation
- retries and timeouts
- permissions and allowlists
- persistence of runs and tool results

Deliverable: agent with safe deterministic tools.

### Week 7: Stateful Agent Workflow

- explicit state machines
- LangGraph fundamentals
- checkpoints
- human approval
- failure recovery
- resumable execution

Deliverable: incident-analysis workflow with approval before sensitive actions.

### Week 8: Enterprise Integration

- authentication basics
- roles and permissions
- background jobs and Redis
- audit trail
- prompt-injection defenses

Deliverable: multi-user agent API with durable history and auditable decisions.

Start targeted applications and mock interviews during this week.

## Month 3 — Evals, Cloud and MLOps

### Week 9: Evals

- versioned datasets
- deterministic assertions
- tool-selection evaluation
- groundedness checks
- safety checks
- latency and cost budgets
- regression reports

Deliverable: automated eval suite that detects a bad release.

### Week 10: AWS Deployment

- IAM basics
- ECR
- ECS or EC2
- RDS PostgreSQL
- S3
- Secrets Manager
- CloudWatch

Deliverable: deployed demo with secrets outside source control.

### Week 11: MLOps and Observability

- GitHub Actions deployment pipeline
- MLflow basics
- OpenTelemetry traces
- metrics and alerting
- model/prompt versioning
- rollback strategy

Deliverable: observable deployment with version metadata and rollback instructions.

### Week 12: Interview Release

- architecture diagram
- design trade-offs
- failure and load scenarios
- polished README
- demo material
- STAR stories
- Python, SQL, backend, AI and system-design review

Deliverable: interview-ready portfolio release.

## Interview Preparation Track

Run in parallel from Week 1, but never replace project coding.

Priorities:

- arrays, hash maps, two pointers, stack, queue and binary search
- Python mutability, functions, classes, exceptions, typing and testing
- HTTP, REST, SQL, transactions and indexes
- tokenization, embeddings, Transformers, agents and evals

## Scope Control

Defer until the core portfolio is interview-ready:

- advanced Kubernetes administration
- distributed model training
- deep CUDA optimization
- complex TensorRT pipelines
- new ESP32 or greenhouse expansion
- training large language models from scratch

Jetson, OpenCV and edge deployments remain supporting case studies.
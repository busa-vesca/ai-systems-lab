# Production AI Engineer Roadmap

## Mission

Become interview-ready for Production / Enterprise AI Engineer roles in 12 weeks and job-ready within 3–5 months.

Study capacity: approximately 5 focused hours per day, 6 days per week.

## Operating Principles

1. Build one coherent production system instead of many disconnected tutorials.
2. Learn each topic immediately inside working code.
3. Ship visible evidence every week.
4. Begin CV, LinkedIn and interview preparation before the project is perfect.
5. Prefer depth in the core stack over shallow exposure to many frameworks.
6. Treat tests, evals, logging, deployment and documentation as product features.

## Weekly Time Budget

```text
2 h  main production project
1 h  Python/backend fundamentals
1 h  interview algorithms, SQL or system design
1 h  cloud, MLOps, documentation or review
```

## Month 1 — Production Python and Backend

### Week 1: Python Engineering

- project structure and virtual environments
- functions, classes, dataclasses and protocols
- typing and mypy basics
- configuration and environment variables
- exceptions and error boundaries
- structured logging
- pytest fundamentals
- Ruff formatting and linting

Deliverable: typed Python package with CLI, configuration, logging and tests.

### Week 2: FastAPI Foundation

- HTTP and REST fundamentals
- request/response schemas with Pydantic
- dependency injection
- status codes and exception handlers
- async versus sync execution
- health and readiness endpoints
- API tests

Deliverable: tested FastAPI task/incident service using an in-memory repository abstraction.

### Week 3: PostgreSQL Persistence

- relational modeling
- SQL fundamentals
- SQLAlchemy 2.x
- transactions and sessions
- Alembic migrations
- indexes and constraints
- repository/service separation

Deliverable: PostgreSQL-backed service with repeatable migrations and integration tests.

### Week 4: Docker and Production Hardening

- Dockerfile and Compose
- environment-specific configuration
- non-root container user
- startup and shutdown lifecycle
- timeouts and idempotency basics
- structured logging and request correlation IDs
- CI checks with GitHub Actions
- Hugging Face `pipeline()` introduction behind a service interface

Deliverable: containerized API with PostgreSQL, CI, documentation and a small Transformer-powered endpoint.

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

Deliverable: agent with at least four safe, deterministic tools.

### Week 7: Stateful Agent Workflow

- explicit state machines
- LangGraph fundamentals
- checkpoints
- human-in-the-loop approval
- failure recovery
- resumable execution

Deliverable: incident-analysis workflow with approval before sensitive actions.

### Week 8: Enterprise Integration

- authentication basics
- roles and permissions
- background jobs and Redis
- webhooks/events conceptually
- audit trail
- prompt injection defenses

Deliverable: multi-user agent API with durable history and auditable decisions.

Start targeted applications and mock interviews during this week.

## Month 3 — Evals, Cloud and MLOps

### Week 9: Evals

- versioned datasets
- deterministic assertions
- tool-selection and trajectory evaluation
- hallucination and groundedness checks
- safety and permission checks
- latency and token-cost budgets
- regression reports

Deliverable: automated eval suite that blocks a bad release.

### Week 10: AWS Deployment

- IAM basics
- ECR
- ECS or EC2
- RDS PostgreSQL
- S3
- Secrets Manager
- CloudWatch

Deliverable: deployed public demo with secrets outside source control.

### Week 11: MLOps and Observability

- GitHub Actions deployment pipeline
- MLflow basics
- OpenTelemetry traces
- metrics and alerting
- model and prompt versioning
- rollback strategy

Deliverable: observable deployment with version metadata and rollback instructions.

### Week 12: Interview Release

- architecture diagram
- design trade-offs
- load and failure scenarios
- polished README
- short demo video or screenshots
- STAR stories
- Python, SQL, backend, AI and system-design review

Deliverable: interview-ready portfolio release.

## Interview Preparation Track

Run in parallel from Week 1.

### Algorithms

Prioritize 35–50 deeply understood problems:

- arrays and hash maps
- two pointers
- stack and queue
- binary search
- linked-list basics
- trees and recursion basics
- BFS/DFS basics

### Python

- data model and mutability
- iterators and generators
- decorators
- context managers
- exceptions
- typing
- async and concurrency basics
- testing and mocking

### Backend and Data

- HTTP and REST
- authentication
- SQL joins and indexes
- transactions
- caching
- queues
- idempotency
- rate limiting
- horizontal scaling

### AI Systems

- tokenization and embeddings
- Transformer inference
- RAG
- agents and tool calling
- evals
- prompt injection
- model choice
- latency and cost
- monitoring and drift

## Job-Ready Evidence

Before claiming a skill, be able to show:

- source code
- tests or evals
- architecture reasoning
- measured results
- failure handling
- deployment evidence
- clear documentation

## Scope Control

Defer until the core portfolio is interview-ready:

- advanced Kubernetes administration
- distributed model training
- deep CUDA kernel optimization
- complex TensorRT pipelines
- new ESP32 or greenhouse hardware expansion
- training large language models from scratch

Jetson, OpenCV and edge deployments remain valuable supporting case studies.

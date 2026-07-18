# AI Systems Lab

A production-oriented learning and portfolio repository for becoming an **Enterprise AI Engineer**.

The main goal is to build, deploy, evaluate, monitor, and explain complete AI systems—not isolated notebooks or model demos.

## Career Target

**Production / Enterprise AI Engineer**

Target capabilities:

```text
Python engineering
→ backend APIs and databases
→ Hugging Face / ML inference
→ AI agents and tool calling
→ evals and regression testing
→ Docker and CI/CD
→ AWS deployment
→ observability and MLOps
→ end-to-end production ownership
```

Interview target: **begin interviewing after 12 weeks**.
Job target: **3–5 months**, with approximately 5 focused study hours per day.

## Primary Stack

- Python 3.11+
- FastAPI, Pydantic, SQLAlchemy, Alembic
- PostgreSQL, Redis
- Pytest, Ruff, mypy
- Docker, Docker Compose
- GitHub Actions
- AWS: IAM, ECR, ECS/EC2, RDS, S3, CloudWatch, Secrets Manager
- Hugging Face: Transformers, Datasets, Tokenizers, Hub, PEFT/LoRA basics
- LLM APIs, structured output, tool calling, LangGraph
- Evals: deterministic checks, agent trajectory tests, regression suites, latency and cost tracking
- MLOps/LLMOps: MLflow, OpenTelemetry, Prometheus/Grafana basics, model and prompt versioning

## 12-Week Roadmap

| Phase | Weeks | Deliverable |
|---|---:|---|
| Production Python | 1–2 | Typed package, config, logging, tests and CLI |
| Backend foundation | 3–4 | FastAPI + PostgreSQL + migrations + Docker |
| Hugging Face inference | 5 | Transformer model served through a production API |
| Enterprise agent | 6–8 | Stateful tool-calling workflow with persistence and approval |
| Evals and reliability | 9 | Regression dataset, quality, safety, latency and cost checks |
| Cloud and MLOps | 10–11 | AWS deployment, CI/CD, secrets, logs, traces and rollback plan |
| Interview release | 12 | Public demo, architecture document, polished README and interview stories |

See [ROADMAP.md](ROADMAP.md) for detailed milestones and [docs/month-01.md](docs/month-01.md) for the first-month execution plan.

## Portfolio Projects

### 1. Enterprise Knowledge & Operations Agent

A production AI service that accepts business incidents or document questions, uses controlled tools, persists state, requests human approval for sensitive actions, and produces traceable results.

Required evidence:

- FastAPI service and OpenAPI contract
- PostgreSQL persistence and migrations
- Hugging Face or hosted-model integration
- LangGraph or explicit state-machine orchestration
- authentication and permissions basics
- retries, timeouts, idempotency and failure handling
- eval dataset and regression tests
- Docker and GitHub Actions
- AWS deployment
- structured logs, metrics and traces

### 2. Production ML Service

A classical ML or small Transformer service demonstrating training/inference separation, experiment tracking, versioned artifacts, deployment, monitoring and drift awareness.

### 3. Edge AI Case Study

Existing Jetson, CUDA, OpenCV and real-device work remains as supporting evidence of Linux, hardware integration, networking, debugging and constrained deployment experience.

## Repository Structure

```text
ai-systems-lab/
├── 01-python-engineering/
├── 02-backend-foundations/
├── 03-huggingface-transformers/
├── 04-agent-systems/
├── 05-evals/
├── 06-cloud-aws/
├── 07-mlops-observability/
├── projects/
│   ├── enterprise-ai-agent/
│   ├── production-ml-service/
│   └── edge-ai-case-study/
├── docs/
│   ├── month-01.md
│   ├── architecture/
│   └── interview-notes/
├── ROADMAP.md
└── README.md
```

Directories are created only when they contain working code or documentation. Empty technology folders are avoided.

## Definition of Done

A learning milestone is complete only when it includes:

- working code
- type hints and clear boundaries
- tests
- error handling and structured logging
- reproducible local setup
- Docker support where applicable
- documented design decisions
- measurable acceptance criteria
- a clean Git history

An AI milestone additionally requires:

- a versioned evaluation dataset
- baseline quality metrics
- latency and cost measurements
- failure examples
- regression protection

A production milestone additionally requires:

- deployment instructions
- secrets handling
- health/readiness checks
- monitoring or tracing
- rollback and failure-recovery notes

## Weekly Operating Rule

Every week must produce visible engineering evidence: an endpoint, test suite, database migration, model service, agent tool, eval report, Docker image, deployment, dashboard, architecture decision or interview-ready case study.

## Supporting Background

This repository also preserves practical experience with Linux, Docker, SSH, networking, NVIDIA Jetson, CUDA, PyTorch, OpenCV, cameras, local LLM runtimes and physical-system integration. These are supporting differentiators rather than the primary learning direction.

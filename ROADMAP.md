# Production / Enterprise AI Engineer — 12 Weeks

## Mission

Begin targeted applications in Week 6, active applications and interviews from Week 8, and reach a credible job-ready portfolio within 3–5 months.

The roadmap extends one central project: `projects/enterprise-ai-platform`. Existing ML, CV and edge labs are supporting evidence, not prerequisites to repeat.

## Working Rules

1. Use the existing `lab-pt` environment. Never recreate a venv as a lesson.
2. Add one major production layer per milestone.
3. Documentation must distinguish current implementation from planned work.
4. Every week ships evidence: code, tests, a measured result, or an interview artifact.
5. Do not expand greenhouse, ESP32, CUDA, TensorRT or Kubernetes scope before interviews begin.

## Weekly Plan

### Week 1 — Production Python Domain

Understand and extend incident entities, status transitions, typed errors and an in-memory service. Add focused unit tests. No environment setup lesson.

### Week 2 — FastAPI Backend

Expose health, readiness, create, list, fetch and update endpoints. Use Pydantic schemas, dependency injection and controlled HTTP errors. Keep storage in memory.

### Week 3 — PostgreSQL

Add SQLAlchemy 2.x, sessions, constraints, repository implementation, Alembic migrations and database integration tests. PostgreSQL is the only major infrastructure addition.

### Week 4 — Docker Runtime

Add a non-root Dockerfile, Compose for API + PostgreSQL, environment configuration, startup/health checks and verified clean-start instructions. Do not add a model in this milestone.

### Week 5 — Hugging Face Inference

Add a pinned small model behind a model-service boundary, load it once, mock it in normal tests, and measure latency. Implement `POST /incidents/{id}/classify`.

### Week 6 — Safe Tool Calling

Add structured tool schemas, validation, allowlists, retries, timeouts and persisted tool results. Begin 2–3 targeted applications per study day.

### Week 7 — Stateful Agent Workflow

Add explicit workflow state, checkpoints, resumability, human approval and recovery from tool/model failures. Run the first technical mock interview.

### Week 8 — Enterprise Integration

Add authentication basics, roles, audit trail, background work and prompt-injection controls. Begin active applications and weekly mock interviews.

### Week 9 — Evals

Create versioned evaluation cases for tool selection, task completion, groundedness, safety, latency and cost. Block regressions in CI.

### Week 10 — AWS

Deploy using ECR plus ECS/EC2, RDS, Secrets Manager and CloudWatch with least-privilege IAM. Keep deployment reproducible and budget-aware.

### Week 11 — CI/CD and Observability

Add GitHub Actions deployment gates, OpenTelemetry traces, operational metrics, version metadata, alerting and rollback instructions.

### Week 12 — Interview Release

Publish architecture and trade-offs, failure/load scenarios, demo evidence and concise STAR stories. Practice Python, SQL, backend, AI and system design using the project.

## Parallel Career Track

| Week | Output |
|---:|---|
| 1 | Inventory existing PyTorch/CV/Jetson/Linux evidence; start interview notes |
| 2 | Draft CV bullets and two STAR stories |
| 3 | Align LinkedIn and GitHub profile with Production AI positioning |
| 4 | Review CV against 10 target vacancies |
| 5 | Build a target-company/application tracker |
| 6 | First targeted applications |
| 7 | First technical and behavioral mocks |
| 8–12 | Active applications, interviews, feedback-driven fixes |

## Weekly Time Budget

```text
2 h  central project
1 h  current backend/AI concept
1 h  tests, debugging, refactoring
1 h  SQL, algorithms, interview or applications
```

## Deferred Scope

Advanced Kubernetes, distributed training, deep CUDA/TensorRT work, new ESP32/greenhouse modules and training large models from scratch are deferred until the interview pipeline is active.

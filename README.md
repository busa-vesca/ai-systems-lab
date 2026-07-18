# AI Systems Lab

Portfolio and learning repository for becoming a **Production / Enterprise AI Engineer**.

## Target

- interviews from Week 8, active applications from Week 6
- job target in 3–5 months
- one central system built end to end: Python → API → database → model → agent → evals → cloud → observability

## Central Project

[`projects/enterprise-ai-platform`](projects/enterprise-ai-platform) is the primary portfolio project. It starts as a tested FastAPI incident backend and grows through the 12-week roadmap into an auditable enterprise AI workflow.

Current implemented API:

```text
GET    /health
GET    /ready
POST   /incidents
GET    /incidents
GET    /incidents/{incident_id}
PATCH  /incidents/{incident_id}
```

The current persistence is deliberately in memory. PostgreSQL, Docker and Hugging Face are separate milestones; they are not presented as already implemented.

## Roadmap

| Week | Primary milestone | Career track |
|---:|---|---|
| 1 | Production Python and incident domain | Evidence inventory + interview notes |
| 2 | FastAPI incident backend + tests | CV baseline and STAR stories |
| 3 | PostgreSQL, SQLAlchemy and Alembic | LinkedIn/GitHub positioning |
| 4 | Docker and reproducible local runtime | CV/portfolio review |
| 5 | Hugging Face inference | Target-company list |
| 6 | Safe tool calling | First targeted applications |
| 7 | Stateful agent workflow | Mock interviews |
| 8 | Enterprise integration | Active applications |
| 9 | Evals and regression protection | Interview iteration |
| 10 | AWS deployment | Active applications |
| 11 | CI/CD and observability | System-design practice |
| 12 | Interview release | Interviews and follow-ups |

See [ROADMAP.md](ROADMAP.md) and [docs/month-01.md](docs/month-01.md).

## Actual Repository Structure

This tree documents what exists now; future folders are not advertised as completed work.

```text
ai-systems-lab/
├── projects/
│   └── enterprise-ai-platform/   # central Production/Enterprise project
├── 01-python-engineering/        # supporting Python notes
├── 02-pytorch-training-loop/     # supporting Production ML evidence
├── 03-opencv-yolo/               # supporting computer-vision evidence
├── 04-fastapi-inference/         # earlier API/vision experiment
├── 05-docker-linux-deployment/   # supporting Linux/container evidence
├── 06-jetson-edge-vision/        # supporting edge deployment evidence
├── 07-local-llm-runtime/         # supporting local-model evidence
├── 08-ai-systems-architecture/   # supporting architecture notes
├── docs/
│   ├── month-01.md
│   └── interview-notes/
├── AGENTS.md
├── ROADMAP.md
└── README.md
```

Legacy top-level notes (`python-core`, `pytorch`, `opencv`, `docker-linux`, `jetson`, `local-llm`, `networking-security`) are retained as historical learning references. They are not the current course sequence.

## Existing Environment

Use the owner's existing `lab-pt` environment. Do not recreate, relocate or commit `.venv`, `.venv-pt`, or any other environment. If a dependency is missing, activate `lab-pt` and install only the dependency required by the current milestone.

## Supporting Evidence

The PyTorch, OpenCV, Jetson, CUDA, Linux, networking, Docker and local-LLM labs remain valuable portfolio evidence. They demonstrate real-device constraints and systems debugging, but they no longer drive the roadmap. The central hiring story is production backend, agents, evals, cloud, MLOps and end-to-end ownership.

## Definition of Done

A milestone needs working code, tests, controlled failures, accurate documentation and an explanation the owner can give without reading the code. AI milestones also need a versioned eval set and quality/latency measurements. Production milestones also need secrets handling, health/readiness checks, observability and rollback notes.

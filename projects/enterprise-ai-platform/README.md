# Enterprise AI Platform

The central portfolio project: an auditable incident-diagnosis workflow built
with FastAPI, PostgreSQL, local Hugging Face inference and controlled tools.

## What the system does

```text
incident
  -> pinned local Hugging Face prediction
  -> deterministic confidence and tool policy
  -> allowlisted tool or human approval
  -> controlled execution
  -> PostgreSQL audit and workflow checkpoints
```

The model classifies an operational incident. It does **not** authorize an
action. The application applies a confidence threshold and tool metadata before
execution. Every durable step can be inspected, resumed or recovered.

This is currently a deterministic stateful workflow, not an autonomous LLM
planner. That distinction is intentional: the project first establishes safe,
testable production mechanics.

## Implemented API

```text
GET    /health
GET    /ready
POST   /incidents
GET    /incidents
GET    /incidents/{incident_id}
PATCH  /incidents/{incident_id}
POST   /incidents/{incident_id}/classify
POST   /incidents/{incident_id}/diagnose
POST   /workflows/{run_id}/resume
POST   /workflows/{run_id}/approve
POST   /workflows/{run_id}/retry
```

## Implemented production layers

- typed incident domain, service layer and controlled errors
- PostgreSQL repositories and Alembic migrations `0001` through `0011`
- CPU Docker image and Jetson Orin GPU deployment override
- pinned `cross-encoder/nli-MiniLM2-L6-H768` zero-shot classifier
- safetensors-only weights, disabled remote model code and persistent cache
- CPU/GPU runtime selection and lazy single-process model loading
- confidence guardrail (`0.60`) before tool execution
- typed tool schemas, allowlist, timeouts and safe retries
- persisted predictions, tool executions and versioned workflow checkpoints
- human approval for sensitive tools
- PostgreSQL advisory locks for concurrent workflow processing
- end-to-end idempotency keys for external tool calls
- linked retry runs for retryable model/tool failures

## Run with the existing environment

```bash
lab-pt
cd "$HOME/ai-systems-lab/projects/enterprise-ai-platform"
python -m pip install -e '.[dev,ai]'
export DATABASE_URL='postgresql+psycopg://enterprise_ai:enterprise_ai_dev@localhost:5432/enterprise_ai'
alembic upgrade head
pytest -q
uvicorn enterprise_ai_platform.api:app --reload
```

No new virtual environment is required or expected. Open
`http://127.0.0.1:8000/docs` for the live API contract.

## Docker Compose

Start the CPU API and PostgreSQL together:

```bash
docker compose up --build -d
```

Compose waits for PostgreSQL, applies migrations, runs the API as a non-root
user, persists database/model data and checks `/ready`.

Stop services without deleting the volumes:

```bash
docker compose down
```

## Jetson GPU deployment

The Jetson path is validated on Orin with JetPack 6.2.x and NVIDIA's
`25.06-py3-igpu` PyTorch container:

```bash
docker compose -f compose.yaml -f compose.jetson.yaml up --build -d
```

At load time, `torch.cuda.is_available()` selects `cuda:0`; the normal image
uses CPU. Platform images own their PyTorch installation so pip cannot replace
the NVIDIA Jetson build. Transformers is pinned to `4.57.6` for compatibility.

Observed on Orin after warm-up: roughly 70–100 ms per classification. Cold
startup also includes model loading and can take tens of seconds.

## Model configuration

```text
HF_MODEL_ID=cross-encoder/nli-MiniLM2-L6-H768
HF_MODEL_REVISION=b95119ce93d3e065de6214e38cd4a97b0f2f2c6d
```

Labels: `database`, `network`, `authentication`, `application` and
`infrastructure`. This Apache-2.0 English zero-shot model is a baseline, not a
model trained on project incidents.

The revision is pinned. Loading requires `model.safetensors`, disables remote
model code and never sends incident text to Hugging Face: weights are downloaded
to the cache, while inference executes locally inside the API container.

## Verification evidence

- local suite: 37 passed, 5 PostgreSQL tests skipped when `DATABASE_URL` is absent
- PostgreSQL-enabled suite: all tests are exercised by CI
- Jetson: CUDA detected as `Orin`; classification and diagnosis verified
- recovery drill: failed retryable run remained immutable; `/retry` created a
  new run linked by `parent_run_id` and completed through the policy path

## Current limitations and next milestone

- no authentication or RBAC yet; approval endpoints are not identity-protected
- only one real operational tool is implemented, and it is read-only
- no versioned evaluation suite or regression gate yet
- no AWS deployment, distributed worker queue or production telemetry yet
- `/ready` checks PostgreSQL but does not warm or evaluate the model
- inference is serialized per API process for a safe initial baseline

Next: Week 8 enterprise controls—authentication, roles, actor-aware approvals,
authorization audit events and prompt/tool-input defenses.

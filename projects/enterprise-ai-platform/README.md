# Enterprise AI Platform

The central portfolio project. The current release is a tested FastAPI incident backend with PostgreSQL persistence, Docker packaging and Hugging Face zero-shot incident classification.

## Current Architecture

```text
HTTP request → Pydantic schema → FastAPI route → IncidentService
                                               → Incident domain rules
                                               → repository
                                                   ├── in-memory
                                                   └── PostgreSQL

POST /incidents/{id}/classify
  → IncidentClassificationService
  → HuggingFaceIncidentClassifier (loaded once, pinned revision)
  → ModelPrediction
  → PostgreSQL
```

Normal API tests use a fake classifier. The real model is downloaded only when
the classification endpoint is called for the first time.

## Run with the existing environment

```bash
lab-pt
cd "$HOME/ai-systems-lab/projects/enterprise-ai-platform"
python -m pip install -e '.[dev,ai]'
uvicorn enterprise_ai_platform.api:app --reload
```

No new virtual environment is required or expected.

## Verify

```bash
pytest
```

Open `http://127.0.0.1:8000/docs` for the API contract.

Create an incident, then call:

```text
POST /incidents/{incident_id}/classify
```

The response contains the selected label, confidence score, model ID, pinned
revision and inference latency. The prediction is saved in PostgreSQL.

## PostgreSQL

With the local development database running:

```bash
export DATABASE_URL='postgresql+psycopg://enterprise_ai:enterprise_ai_dev@localhost:5432/enterprise_ai'
alembic upgrade head
pytest
uvicorn enterprise_ai_platform.api:app --reload
```

## Docker Compose

Start the API and PostgreSQL together:

```bash
docker compose up --build
```

Compose waits for PostgreSQL, applies Alembic migrations, starts the API as a
non-root user, persists the Hugging Face cache and checks `/ready`. The first
classification downloads the model; later calls reuse the loaded model and
cache. The image installs the CPU-only PyTorch wheel, so it does not pull CUDA
libraries into a CPU service. Stop the stack without deleting database or model
data:

```bash
docker compose down
```

## Run with GPU on Jetson

The Jetson deployment is validated for JetPack 6.2.x on Orin with NVIDIA's
`25.06-py3-igpu` PyTorch container. It keeps the normal CPU image unchanged and
adds the Jetson settings through a Compose override:

```bash
docker compose -f compose.yaml -f compose.jetson.yaml up --build -d
```

The NVIDIA runtime exposes the Orin GPU to the API container. At model load,
`torch.cuda.is_available()` selects `cuda:0`; on a machine without CUDA the same
Python code falls back to CPU. The first classification downloads the pinned
safetensors model into the persistent model cache.

PyTorch is intentionally installed by each platform image rather than by the
generic `ai` dependency group. This prevents pip from replacing NVIDIA's
Jetson-optimized CUDA build with an incompatible wheel.

Verify the runtime inside the API container:

```bash
docker compose -f compose.yaml -f compose.jetson.yaml exec api python3 -c \
  'import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))'
```

## Model configuration

Defaults:

```text
HF_MODEL_ID=cross-encoder/nli-MiniLM2-L6-H768
HF_MODEL_REVISION=b95119ce93d3e065de6214e38cd4a97b0f2f2c6d
```

The labels are `database`, `network`, `authentication`, `application` and
`infrastructure`. This Apache-2.0 licensed model is an English zero-shot
baseline, not a model trained on our incident data.

The revision is pinned for reproducibility. Model loading explicitly requires
`model.safetensors` and disables remote model code, so it does not fall back to
pickle-based `pytorch_model.bin` weights.

## Current Limitations

- no authentication or audit trail yet
- no agent or evaluation dataset yet
- `/ready` checks PostgreSQL but does not warm or evaluate the model
- CPU inference is serialized to keep the first production baseline safe

These limitations map directly to later roadmap milestones rather than being hidden.

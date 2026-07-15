# vision-inference-api

Milestone project for serving computer-vision inference through a small API.

## Goal

Build a minimal but professional inference service:

```text
image input -> preprocessing -> model inference -> structured response
```

Current stage: API skeleton with `/health` and `/predict` stub endpoint.

## Target stack

Python · FastAPI · Pydantic · OpenCV · YOLO · Docker · pytest

## Current structure

```text
vision-inference-api/
├── src/
│   └── vision_inference_api/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── test_health.py
│   └── test_predict.py
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── README.md
```

## Local run

From the repository root:

```bash
source .venv/bin/activate
uvicorn vision_inference_api.main:app --app-dir 04-fastapi-inference/vision-inference-api/src --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Predict stub:

```bash
printf "fake-image-bytes" > /tmp/fake.jpg
curl -X POST http://127.0.0.1:8000/predict \
  -F "file=@/tmp/fake.jpg;type=image/jpeg"
```

## Tests

From the repository root:

```bash
source .venv/bin/activate
pytest 04-fastapi-inference/vision-inference-api/tests
```

## Docker run

Build the image from the project directory context:

```bash
docker build -t vision-inference-api:dev 04-fastapi-inference/vision-inference-api
```

Run the container:

```bash
docker run --rm -p 8000:8000 vision-inference-api:dev
```

Then test from another terminal:

```bash
curl http://127.0.0.1:8000/health
printf "fake-image-bytes" > /tmp/fake.jpg
curl -X POST http://127.0.0.1:8000/predict \
  -F "file=@/tmp/fake.jpg;type=image/jpeg"
```

Stop the container with `Ctrl+C`.

## Acceptance criteria

- `/health` endpoint returns service status.
- `/predict` accepts an uploaded image and returns file metadata.
- Tests verify `/health` and `/predict`.
- README includes local and Docker run commands.

## Learning target

Understand how an AI model becomes a usable software service, not just a script.

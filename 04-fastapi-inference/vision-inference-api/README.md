# vision-inference-api

Milestone project for serving computer-vision inference through a small API.

## Goal

Build a minimal but professional inference service:

```text
image input -> preprocessing -> model inference -> structured response
```

## Target stack

Python · FastAPI · Pydantic · OpenCV · YOLO · Docker · pytest

## Planned structure

```text
vision-inference-api/
├── src/
│   └── vision_inference_api/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── model.py
│       └── schemas.py
├── tests/
├── samples/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Acceptance criteria

- `/health` endpoint returns service status.
- `/predict` accepts an image and returns structured predictions.
- Inference code is separated from API code.
- README includes run commands.
- Basic test verifies the health endpoint.

## Learning target

Understand how an AI model becomes a usable software service, not just a script.

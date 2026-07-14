# jetson-edge-vision-service

Milestone project for validating computer vision on real edge hardware.

## Goal

Build a Jetson-focused vision service:

```text
camera -> OpenCV capture -> inference placeholder/model -> FPS/logs -> service mode
```

## Target stack

NVIDIA Jetson · Jetson Linux · Python · OpenCV · CUDA/PyTorch checks · systemd · logs

## Planned structure

```text
jetson-edge-vision-service/
├── src/
│   └── jetson_edge_vision/
│       ├── __init__.py
│       ├── camera.py
│       ├── diagnostics.py
│       └── main.py
├── systemd/
├── tests/
├── requirements.txt
└── README.md
```

## Acceptance criteria

- Captures a frame from a camera on Jetson.
- Logs FPS or frame timing.
- Checks CUDA/PyTorch availability when installed.
- Can be prepared for systemd service mode.
- README includes Jetson run commands and troubleshooting notes.

## Learning target

Prove that AI code can move from laptop/lab to a real edge target with camera, GPU, logs, and runtime constraints.

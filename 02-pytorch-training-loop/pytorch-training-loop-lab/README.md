# pytorch-training-loop-lab

Milestone project for understanding the full PyTorch training cycle.

## Goal

Build a small, readable training pipeline:

```text
dataset -> dataloader -> model -> loss -> optimizer -> train/validate -> checkpoint
```

## Target stack

Python · PyTorch · Dataset · DataLoader · training loop · validation loop · metrics · checkpoints

## Planned structure

```text
pytorch-training-loop-lab/
├── src/
│   └── training_loop_lab/
│       ├── __init__.py
│       ├── dataset.py
│       ├── model.py
│       ├── train.py
│       └── evaluate.py
├── tests/
├── checkpoints/
├── requirements.txt
└── README.md
```

## Acceptance criteria

- A minimal model trains on a small dataset or generated data.
- Training and validation are separate.
- Loss and metrics are printed clearly.
- Checkpoint save/load is implemented.
- README explains how to run and what to observe.

## Learning target

Understand how models are trained, validated, saved, loaded, and checked for failure modes.

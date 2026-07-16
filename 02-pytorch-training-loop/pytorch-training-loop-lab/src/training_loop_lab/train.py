"""Training utilities for the PyTorch training-loop lab."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.utils.data import DataLoader

from training_loop_lab.metrics import accuracy_from_logits
from training_loop_lab.model import TinyClassifier


@dataclass(frozen=True)
class TrainResult:
    """Summary returned after a small training run."""

    avg_loss: float
    accuracy: float
    num_batches: int


def train_one_epoch(
    model: TinyClassifier,
    loader: DataLoader,
    loss_fn: nn.Module,
    optimizer: torch.optim.Optimizer,
) -> TrainResult:
    """Run one training epoch over all batches in a DataLoader."""
    model.train()

    total_loss = 0.0
    total_accuracy = 0.0
    num_batches = 0

    for batch_x, batch_target in loader:
        logits = model(batch_x)
        loss = loss_fn(logits, batch_target)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        total_accuracy += accuracy_from_logits(logits, batch_target)
        num_batches += 1

    return TrainResult(
        avg_loss=total_loss / num_batches,
        accuracy=total_accuracy / num_batches,
        num_batches=num_batches,
    )

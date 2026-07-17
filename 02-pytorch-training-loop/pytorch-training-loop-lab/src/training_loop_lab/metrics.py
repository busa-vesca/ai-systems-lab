"""Metrics for the PyTorch training-loop lab."""

from __future__ import annotations

import torch


def accuracy_from_logits(logits: torch.Tensor, target: torch.Tensor) -> float:
    """Compute classification accuracy from raw model logits.

    logits shape: [batch_size, num_classes]
    target shape: [batch_size]
    """
    correct, total = correct_predictions_from_logits(logits, target)
    return correct / total


def correct_predictions_from_logits(
    logits: torch.Tensor,
    target: torch.Tensor,
) -> tuple[int, int]:
    """Return the number of correct predictions and total examples."""
    predictions = logits.argmax(dim=1)
    correct = (predictions == target).sum().item()
    total = target.numel()
    return correct, total

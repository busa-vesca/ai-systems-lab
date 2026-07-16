"""Metrics for the PyTorch training-loop lab."""

from __future__ import annotations

import torch


def accuracy_from_logits(logits: torch.Tensor, target: torch.Tensor) -> float:
    """Compute classification accuracy from raw model logits.

    logits shape: [batch_size, num_classes]
    target shape: [batch_size]
    """
    predictions = logits.argmax(dim=1)
    correct = (predictions == target).sum().item()
    total = target.numel()
    return correct / total

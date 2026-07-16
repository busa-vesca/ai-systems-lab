"""Dataset helpers for the PyTorch training-loop lab."""

from __future__ import annotations

import torch
from torch.utils.data import DataLoader, TensorDataset


def make_fake_classification_data(
    num_samples: int = 100,
    input_dim: int = 4,
    num_classes: int = 2,
    seed: int = 42,
) -> TensorDataset:
    """Create a small synthetic classification dataset.

    This is intentionally fake data. The goal is to practice the mechanics of:
    Dataset -> DataLoader -> model -> loss -> optimizer.
    """
    generator = torch.Generator().manual_seed(seed)
    x = torch.randn(num_samples, input_dim, generator=generator)
    y = torch.randint(0, num_classes, (num_samples,), generator=generator)
    return TensorDataset(x, y)


def make_dataloader(
    dataset: TensorDataset,
    batch_size: int = 16,
    shuffle: bool = True,
) -> DataLoader:
    """Wrap a Dataset in a DataLoader so training can iterate over batches."""
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)

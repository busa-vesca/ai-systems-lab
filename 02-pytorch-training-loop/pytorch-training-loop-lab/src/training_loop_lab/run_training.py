"""Small runnable training script for the PyTorch training-loop lab."""

from __future__ import annotations

import torch
from torch import nn

from training_loop_lab.dataset import make_dataloader, make_fake_classification_data
from training_loop_lab.model import TinyClassifier
from training_loop_lab.train import train_one_epoch


def run_training(num_epochs: int = 5) -> None:
    """Run a small fake-data training experiment and print epoch metrics."""
    torch.manual_seed(42)

    dataset = make_fake_classification_data(
        num_samples=128,
        input_dim=4,
        num_classes=2,
    )
    loader = make_dataloader(dataset, batch_size=16, shuffle=True)

    model = TinyClassifier(input_dim=4, hidden_dim=8, num_classes=2)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    for epoch in range(num_epochs):
        result = train_one_epoch(model, loader, loss_fn, optimizer)
        print(
            f"epoch {epoch + 1}: "
            f"avg_loss={result.avg_loss:.6f}, "
            f"accuracy={result.accuracy:.3f}, "
            f"batches={result.num_batches}"
        )


if __name__ == "__main__":
    run_training()

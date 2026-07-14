import torch
from torch import nn


class TinyClassifier(nn.Module):
    """Small model for training-loop experiments."""

    def __init__(self, input_dim: int = 2, hidden_dim: int = 8, num_classes: int = 2) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

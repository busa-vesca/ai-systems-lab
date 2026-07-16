import torch

from training_loop_lab.metrics import accuracy_from_logits


def test_accuracy_from_logits() -> None:
    logits = torch.tensor([
        [3.0, 1.0],
        [0.2, 2.0],
        [1.5, 0.1],
    ])
    target = torch.tensor([0, 1, 1])

    accuracy = accuracy_from_logits(logits, target)

    assert accuracy == 2 / 3

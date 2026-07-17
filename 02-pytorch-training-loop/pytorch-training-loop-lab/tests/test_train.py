import pytest
import torch
from torch import nn
from torch.utils.data import TensorDataset

from training_loop_lab.dataset import make_dataloader, make_fake_classification_data
from training_loop_lab.model import TinyClassifier
from training_loop_lab.train import train_one_epoch


def test_train_one_epoch_returns_metrics() -> None:
    dataset = make_fake_classification_data(num_samples=32, input_dim=4, num_classes=2)
    loader = make_dataloader(dataset, batch_size=8, shuffle=False)
    model = TinyClassifier(input_dim=4)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    result = train_one_epoch(model, loader, loss_fn, optimizer)

    assert result.num_batches == 4
    assert result.avg_loss > 0
    assert 0.0 <= result.accuracy <= 1.0


def test_train_one_epoch_handles_uneven_final_batch() -> None:
    dataset = make_fake_classification_data(num_samples=10, input_dim=4, num_classes=2)
    loader = make_dataloader(dataset, batch_size=4, shuffle=False)
    model = TinyClassifier(input_dim=4)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    result = train_one_epoch(model, loader, loss_fn, optimizer)

    assert result.num_batches == 3
    assert result.avg_loss > 0
    assert 0.0 <= result.accuracy <= 1.0


def test_train_one_epoch_rejects_empty_dataloader() -> None:
    empty_x = torch.empty(0, 4)
    empty_target = torch.empty(0, dtype=torch.long)
    dataset = TensorDataset(empty_x, empty_target)
    loader = make_dataloader(dataset, batch_size=4, shuffle=False)
    model = TinyClassifier(input_dim=4)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    with pytest.raises(ValueError, match="DataLoader produced no batches"):
        train_one_epoch(model, loader, loss_fn, optimizer)

import torch
from torch import nn

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

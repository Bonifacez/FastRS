from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from fastrs.logging import get_logger

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = get_logger("fastrs.trainer")


class TrainingResult:
    def __init__(self) -> None:
        self.epochs: List[Dict[str, float]] = []
        self.best_loss: float = float("inf")
        self.total_time: float = 0.0

    def add_epoch(self, epoch: int, loss: float, **metrics: float) -> None:
        self.epochs.append({"epoch": epoch, "loss": loss, **metrics})
        if loss < self.best_loss:
            self.best_loss = loss


class Trainer:
    """PyTorch model trainer."""

    def __init__(
        self,
        model: Any,
        epochs: int = 10,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        device: Optional[str] = None,
    ) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed.")
        self.model = model
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._result: Optional[TrainingResult] = None

    def _get_optimizer(self, model: Any) -> Any:
        return optim.Adam(model.parameters(), lr=self.learning_rate)

    def _get_loss_fn(self) -> Any:
        return nn.BCELoss()

    def _batch_iter(
        self, X: Any, y: Any
    ) -> Iterator[Tuple[Any, Any]]:
        n = len(X)
        indices = torch.randperm(n)
        for start in range(0, n, self.batch_size):
            batch_idx = indices[start: start + self.batch_size]
            yield X[batch_idx], y[batch_idx]

    def train(
        self,
        X: Any,
        y: Any,
        save_path: Optional[Path] = None,
    ) -> TrainingResult:
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed.")

        nn_model = self.model.get_model().to(self.device)
        optimizer = self._get_optimizer(nn_model)
        loss_fn = self._get_loss_fn()

        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        y_t = torch.tensor(y, dtype=torch.float32).to(self.device)

        result = TrainingResult()
        start_time = time.time()

        nn_model.train()
        for epoch in range(1, self.epochs + 1):
            epoch_loss = 0.0
            num_batches = 0
            for X_batch, y_batch in self._batch_iter(X_t, y_t):
                optimizer.zero_grad()
                preds = nn_model(X_batch).squeeze(-1)
                loss = loss_fn(preds, y_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
                num_batches += 1

            avg_loss = epoch_loss / max(num_batches, 1)
            result.add_epoch(epoch, avg_loss)
            logger.info("training_epoch", epoch=epoch, loss=avg_loss)

        result.total_time = time.time() - start_time
        nn_model.eval()
        self._result = result

        if save_path:
            self.model.save(save_path)
            logger.info("model_saved", path=str(save_path))

        return result

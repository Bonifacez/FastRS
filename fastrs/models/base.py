"""Base class for ML models and PyTorch integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseModel(ABC):
    """Abstract model interface for training and inference."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def predict(self, inputs: Any) -> Any:
        """Run inference on *inputs*."""

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist model weights / artefacts to *path*."""

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model weights / artefacts from *path*."""


def _torch_available() -> bool:
    """Check if PyTorch is installed."""
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


class TorchModel(BaseModel):
    """Base class for PyTorch-based models.

    Subclass this and implement ``build_module()`` to return an ``nn.Module``.
    """

    def __init__(self) -> None:
        if not _torch_available():
            raise ImportError(
                "PyTorch is required for TorchModel. "
                "Install it with: pip install 'fastrs[torch]'"
            )
        import torch

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.module: torch.nn.Module | None = None

    @abstractmethod
    def build_module(self) -> Any:
        """Return an ``nn.Module`` instance."""

    def predict(self, inputs: Any) -> Any:
        import torch

        if self.module is None:
            raise RuntimeError("Model module not built. Call build_module() first.")
        self.module.eval()
        with torch.no_grad():
            return self.module(inputs)

    def save(self, path: str) -> None:
        import torch

        if self.module is None:
            raise RuntimeError("No module to save")
        torch.save(self.module.state_dict(), path)

    def load(self, path: str) -> None:
        import torch

        if self.module is None:
            raise RuntimeError("Build the module before loading weights")
        self.module.load_state_dict(torch.load(path, map_location=self.device, weights_only=True))
        self.module.to(self.device)

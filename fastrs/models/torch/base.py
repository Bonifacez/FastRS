from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class BaseTorchModel:
    """Base class for PyTorch models in FastRS."""

    name: str = "base_model"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed. Install with: pip install fastrs[torch]")
        self.config = config or {}
        self._model: Optional[nn.Module] = None

    def build(self) -> nn.Module:
        """Build and return the PyTorch model."""
        raise NotImplementedError

    def get_model(self) -> nn.Module:
        if self._model is None:
            self._model = self.build()
        return self._model

    def save(self, path: Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        model = self.get_model()
        torch.save(model.state_dict(), path / "weights.pt")
        with open(path / "config.json", "w") as f:
            json.dump({"name": self.name, "config": self.config}, f)

    def load(self, path: Path) -> None:
        path = Path(path)
        state_dict = torch.load(path / "weights.pt", map_location="cpu", weights_only=True)
        model = self.get_model()
        model.load_state_dict(state_dict)
        model.eval()


class SimpleMLP(BaseTorchModel):
    """Simple MLP model for ranking."""

    name = "simple_mlp"

    def __init__(self, input_dim: int = 64, hidden_dim: int = 128, output_dim: int = 1,
                 config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

    def build(self) -> Any:
        import torch.nn as nn
        return nn.Sequential(
            nn.Linear(self.input_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(self.hidden_dim, self.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(self.hidden_dim // 2, self.output_dim),
            nn.Sigmoid(),
        )

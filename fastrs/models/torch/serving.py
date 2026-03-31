from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from fastrs.logging import get_logger

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = get_logger("fastrs.serving")

_executor = ThreadPoolExecutor(max_workers=4)


class ModelServing:
    """Serving wrapper for PyTorch models with async support."""

    def __init__(self, model: Any, device: Optional[str] = None) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed.")
        self.model = model
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._nn_model = None

    def load(self, path: Optional[Path] = None) -> None:
        if path:
            self.model.load(path)
        self._nn_model = self.model.get_model().to(self.device)
        self._nn_model.eval()

    def _infer_sync(self, features: np.ndarray) -> np.ndarray:
        if self._nn_model is None:
            self._nn_model = self.model.get_model().to(self.device)
            self._nn_model.eval()
        with torch.no_grad():
            x = torch.tensor(features, dtype=torch.float32).to(self.device)
            out = self._nn_model(x)
            return out.cpu().numpy()

    async def infer(self, features: np.ndarray) -> np.ndarray:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._infer_sync, features)

    async def batch_infer(self, features_list: List[np.ndarray]) -> List[np.ndarray]:
        if not features_list:
            return []
        combined = np.vstack(features_list)
        result = await self.infer(combined)
        # Split back
        sizes = [len(f) for f in features_list]
        outputs = []
        idx = 0
        for size in sizes:
            outputs.append(result[idx: idx + size])
            idx += size
        return outputs

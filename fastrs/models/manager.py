"""Model manager — register, train, deploy, and manage ML models."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from fastrs.core.types import ModelInfo
from fastrs.log import get_logger
from fastrs.models.base import BaseModel

logger = get_logger(__name__)


class ModelManager:
    """Thread-safe manager for ML models.

    Supports registering, training, deploying, and removing models at runtime.
    """

    def __init__(self, model_dir: str = "models_store") -> None:
        self._lock = threading.RLock()
        self._models: dict[str, dict[str, Any]] = {}
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def register(self, name: str, model: BaseModel, *, version: str = "0.0.1") -> ModelInfo:
        """Register a model for management."""
        with self._lock:
            if name in self._models:
                raise ValueError(f"Model '{name}' already registered")
            info = ModelInfo(name=name, version=version, status="registered")
            self._models[name] = {"model": model, "info": info}
            logger.info("model_registered", name=name, version=version)
            return info

    def unregister(self, name: str) -> None:
        """Remove a model from management."""
        with self._lock:
            if name not in self._models:
                raise KeyError(f"Model '{name}' not found")
            del self._models[name]
            logger.info("model_unregistered", name=name)

    def get_model(self, name: str) -> BaseModel:
        """Return the model instance."""
        with self._lock:
            if name not in self._models:
                raise KeyError(f"Model '{name}' not found")
            return self._models[name]["model"]

    def get_info(self, name: str) -> ModelInfo:
        """Return model metadata."""
        with self._lock:
            if name not in self._models:
                raise KeyError(f"Model '{name}' not found")
            return self._models[name]["info"]

    def list_models(self) -> list[ModelInfo]:
        """List all managed models."""
        with self._lock:
            return [entry["info"] for entry in self._models.values()]

    def save_model(self, name: str) -> str:
        """Persist model to disk. Returns the saved path."""
        with self._lock:
            model = self.get_model(name)
            info = self.get_info(name)
            save_path = str(self.model_dir / f"{name}_v{info.version}.pt")
            model.save(save_path)
            info.path = save_path
            info.status = "saved"
            logger.info("model_saved", name=name, path=save_path)
            return save_path

    def load_model(self, name: str, path: str | None = None) -> None:
        """Load model weights from disk."""
        with self._lock:
            model = self.get_model(name)
            info = self.get_info(name)
            load_path = path or info.path
            if not load_path:
                raise ValueError(f"No path specified for model '{name}'")
            model.load(load_path)
            info.status = "loaded"
            logger.info("model_loaded", name=name, path=load_path)

    def set_status(self, name: str, status: str) -> None:
        """Update the status label for a model."""
        with self._lock:
            info = self.get_info(name)
            info.status = status

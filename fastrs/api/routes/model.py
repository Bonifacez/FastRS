from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

from fastrs.config import get_settings
from fastrs.logging import get_logger
from fastrs.models.schemas import ModelLoadRequest, ModelTrainRequest

router = APIRouter(prefix="/models", tags=["models"])
logger = get_logger("fastrs.routes.model")

# In-memory model registry
_loaded_models: Dict[str, Dict[str, Any]] = {}
_training_jobs: Dict[str, Dict[str, Any]] = {}


@router.get("", response_model=List[Dict[str, Any]], summary="List all loaded models")
async def list_models() -> List[Dict[str, Any]]:
    return list(_loaded_models.values())


@router.post("/load", response_model=Dict[str, Any], summary="Load a model from disk")
async def load_model(req: ModelLoadRequest) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.enable_torch:
        raise HTTPException(status_code=400, detail="PyTorch support is not enabled")

    try:
        from fastrs.models.torch.base import SimpleMLP
        from fastrs.models.torch.serving import ModelServing

        model_path = Path(req.model_path)
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model path '{req.model_path}' not found")

        base_model = SimpleMLP()
        serving = ModelServing(base_model)
        serving.load(model_path)

        _loaded_models[req.model_name] = {
            "name": req.model_name,
            "type": req.model_type,
            "path": req.model_path,
            "status": "loaded",
            "serving": serving,
        }
        logger.info("model_loaded", name=req.model_name, path=req.model_path)
        info = {k: v for k, v in _loaded_models[req.model_name].items() if k != "serving"}
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _train_background(job_id: str, req: ModelTrainRequest) -> None:
    settings = get_settings()
    try:
        import numpy as np
        from fastrs.models.torch.base import SimpleMLP
        from fastrs.models.torch.trainer import Trainer

        _training_jobs[job_id]["status"] = "running"

        # Generate synthetic data for demo
        rng = np.random.default_rng(42)
        X = rng.standard_normal((1000, 64)).astype(np.float32)
        y = (rng.random(1000) > 0.5).astype(np.float32)

        model = SimpleMLP(input_dim=64, hidden_dim=128, output_dim=1)
        trainer = Trainer(
            model=model,
            epochs=req.epochs,
            learning_rate=req.learning_rate,
            batch_size=req.batch_size,
        )

        save_path = settings.model_dir / req.model_name
        result = trainer.train(X, y, save_path=save_path)

        _training_jobs[job_id]["status"] = "completed"
        _training_jobs[job_id]["result"] = {
            "best_loss": result.best_loss,
            "total_time": result.total_time,
            "epochs": len(result.epochs),
        }
        logger.info("training_completed", job_id=job_id, model=req.model_name)
    except Exception as e:
        _training_jobs[job_id]["status"] = "failed"
        _training_jobs[job_id]["error"] = str(e)
        logger.error("training_failed", job_id=job_id, error=str(e))


@router.post("/train", response_model=Dict[str, Any], summary="Start model training")
async def train_model(req: ModelTrainRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.enable_torch:
        raise HTTPException(status_code=400, detail="PyTorch support is not enabled")

    import uuid
    job_id = str(uuid.uuid4())
    _training_jobs[job_id] = {
        "job_id": job_id,
        "model_name": req.model_name,
        "status": "queued",
    }
    background_tasks.add_task(_train_background, job_id, req)
    return _training_jobs[job_id]


@router.get("/train/{job_id}", response_model=Dict[str, Any], summary="Get training job status")
async def get_training_job(job_id: str) -> Dict[str, Any]:
    if job_id not in _training_jobs:
        raise HTTPException(status_code=404, detail=f"Training job '{job_id}' not found")
    return _training_jobs[job_id]


@router.delete("/{name}", summary="Unload a model")
async def remove_model(name: str) -> Dict[str, str]:
    if name not in _loaded_models:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")
    del _loaded_models[name]
    logger.info("model_unloaded", name=name)
    return {"status": "unloaded", "name": name}


@router.get("/{name}", response_model=Dict[str, Any], summary="Get model info")
async def get_model(name: str) -> Dict[str, Any]:
    if name not in _loaded_models:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")
    info = {k: v for k, v in _loaded_models[name].items() if k != "serving"}
    return info

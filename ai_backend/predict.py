from __future__ import annotations

import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from preprocess import build_goal_features_from_payload, build_success_features_from_payload


DEFAULT_GOAL_MODEL = Path(__file__).resolve().parent / "model_goal.pkl"
DEFAULT_SUCCESS_MODEL = Path(__file__).resolve().parent / "model_success.pkl"
DEFAULT_PLAN_INTENT_MODEL = Path(__file__).resolve().parent / "model_plan_intent.pkl"


def _load_pickle(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    with path.open("rb") as f:
        artifact = pickle.load(f)
    if not isinstance(artifact, dict) or "model" not in artifact:
        raise ValueError(f"Invalid model artifact format in: {path}")
    return artifact


@lru_cache(maxsize=2)
def load_goal_model(model_path: str | None = None) -> dict[str, Any]:
    return _load_pickle(Path(model_path) if model_path else DEFAULT_GOAL_MODEL)


@lru_cache(maxsize=2)
def load_success_model(model_path: str | None = None) -> dict[str, Any]:
    return _load_pickle(Path(model_path) if model_path else DEFAULT_SUCCESS_MODEL)


@lru_cache(maxsize=2)
def load_plan_intent_model(model_path: str | None = None) -> dict[str, Any]:
    return _load_pickle(Path(model_path) if model_path else DEFAULT_PLAN_INTENT_MODEL)


def _probability_map(classes: list[Any], probs: np.ndarray) -> dict[str, float]:
    return {str(label): float(prob) for label, prob in zip(classes, probs)}


def predict_goal(features_payload: dict[str, Any], model_path: str | None = None) -> dict[str, Any]:
    artifact = load_goal_model(model_path)
    model = artifact["model"]
    frame = build_goal_features_from_payload(features_payload)
    pred = model.predict(frame)[0]
    probabilities = {}
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(frame)[0]
        classes = list(model.classes_)
        probabilities = _probability_map(classes, probs)
    return {
        "predicted_goal": str(pred),
        "probabilities": probabilities,
        "model_name": artifact.get("model_name"),
        "metrics": artifact.get("metrics", {}),
    }


def predict_success(features_payload: dict[str, Any], model_path: str | None = None) -> dict[str, Any]:
    artifact = load_success_model(model_path)
    model = artifact["model"]
    frame = build_success_features_from_payload(features_payload)
    pred = int(model.predict(frame)[0])

    probability_success = None
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(frame)[0]
        classes = list(model.classes_)
        if 1 in classes:
            idx = classes.index(1)
            probability_success = float(probs[idx])

    return {
        "success_prediction": pred,
        "success_probability": probability_success,
        "model_name": artifact.get("model_name"),
        "metrics": artifact.get("metrics", {}),
    }


def predict_plan_intent(message: str, model_path: str | None = None) -> dict[str, Any]:
    artifact = load_plan_intent_model(model_path)
    model = artifact["model"]
    pred = model.predict([str(message or "")])[0]

    probabilities = {}
    confidence = None
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba([str(message or "")])[0]
        classes = list(model.classes_)
        probabilities = _probability_map(classes, probs)
        if pred in classes:
            idx = classes.index(pred)
            confidence = float(probs[idx])

    return {
        "predicted_intent": str(pred),
        "confidence": confidence,
        "probabilities": probabilities,
        "model_name": artifact.get("model_name"),
        "metrics": artifact.get("metrics", {}),
    }

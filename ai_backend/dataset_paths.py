from __future__ import annotations

import os
from pathlib import Path


DEFAULT_DATASET_CANDIDATES = [
    Path(r"D:\chatbot coach\dataset_"),
    Path(r"D:\chatbot coach\Dataset"),
    Path(__file__).resolve().parent / "datasets",
]


def resolve_dataset_root() -> Path:
    env_value = os.getenv("DATASET_ROOT", "").strip()
    if env_value:
        env_path = Path(env_value)
        if env_path.exists():
            return env_path

    for candidate in DEFAULT_DATASET_CANDIDATES:
        if candidate.exists():
            return candidate

    if env_value:
        return Path(env_value)
    return DEFAULT_DATASET_CANDIDATES[-1]


def resolve_derived_root() -> Path:
    derived_root = Path(__file__).resolve().parent / "data" / "derived"
    derived_root.mkdir(parents=True, exist_ok=True)
    return derived_root


__all__ = ["resolve_dataset_root", "resolve_derived_root"]

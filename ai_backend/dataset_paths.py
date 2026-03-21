from __future__ import annotations

import os
from pathlib import Path


DEFAULT_DATASET_CANDIDATES = [
    Path(__file__).resolve().parent / "datasets",
]


def _count_files(path: Path) -> int:
    try:
        return sum(1 for item in path.rglob("*") if item.is_file())
    except Exception:
        return 0


def resolve_dataset_root() -> Path:
    env_value = os.getenv("DATASET_ROOT", "").strip()
    if env_value:
        env_path = Path(env_value)
        if env_path.exists():
            return env_path

    existing = [candidate for candidate in DEFAULT_DATASET_CANDIDATES if candidate.exists()]
    if existing:
        existing.sort(key=_count_files, reverse=True)
        return existing[0]

    if env_value:
        return Path(env_value)
    return DEFAULT_DATASET_CANDIDATES[-1]


def resolve_derived_root() -> Path:
    derived_root = Path(__file__).resolve().parent / "data" / "derived"
    derived_root.mkdir(parents=True, exist_ok=True)
    return derived_root


__all__ = ["resolve_dataset_root", "resolve_derived_root"]

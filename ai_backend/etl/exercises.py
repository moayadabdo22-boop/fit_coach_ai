from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dataset_paths import resolve_dataset_root
from db import require_supabase
from .helpers import chunked


def _slug(text: str) -> str:
    return text.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")


def load_exercises(
    dataset_root: Path | None = None,
    limit: int = 5000,
    batch_size: int = 500,
) -> dict[str, Any]:
    sb = require_supabase()
    dataset_root = dataset_root or resolve_dataset_root()
    mega_path = dataset_root / "megaGymDataset.csv"
    boostcamp_path = dataset_root / "programs_detailed_boostcamp_kaggle.csv"

    rows = []
    if mega_path.exists():
        df = pd.read_csv(mega_path, nrows=limit)
        for idx, row in df.iterrows():
            rows.append({
                "source": "megaGym",
                "source_id": str(idx),
                "name": row.get("Title"),
                "description": row.get("Desc"),
                "difficulty": row.get("Level"),
                "muscle": row.get("BodyPart"),
                "equipment": row.get("Equipment"),
            })

    if boostcamp_path.exists():
        df = pd.read_csv(boostcamp_path, nrows=limit)
        for idx, row in df.iterrows():
            rows.append({
                "source": "boostcamp",
                "source_id": str(idx),
                "name": row.get("exercise_name"),
                "description": row.get("description"),
                "difficulty": row.get("level"),
                "muscle": row.get("goal") or row.get("day"),
                "equipment": row.get("equipment"),
            })

    # Prepare equipment and muscle groups
    equipment_names = sorted({r["equipment"] for r in rows if r.get("equipment")})
    muscle_names = sorted({r["muscle"] for r in rows if r.get("muscle")})

    for batch in chunked([
        {"code": _slug(name), "name": name} for name in equipment_names
    ], batch_size):
        sb.table("equipment").upsert(batch, on_conflict="code").execute()

    for batch in chunked([
        {"code": _slug(name), "name": name} for name in muscle_names
    ], batch_size):
        sb.table("muscle_groups").upsert(batch, on_conflict="code").execute()

    equipment_map = {
        r["name"]: r["id"]
        for r in sb.table("equipment").select("id,name").execute().data or []
    }
    muscle_map = {
        r["name"]: r["id"]
        for r in sb.table("muscle_groups").select("id,name").execute().data or []
    }

    exercise_rows = []
    for r in rows:
        if not r.get("name"):
            continue
        exercise_rows.append({
            "source": r.get("source"),
            "source_id": r.get("source_id"),
            "name": r.get("name"),
            "difficulty": r.get("difficulty"),
            "equipment_id": equipment_map.get(r.get("equipment")) if r.get("equipment") else None,
            "description": r.get("description"),
        })

    for batch in chunked(exercise_rows, batch_size):
        sb.table("exercises").upsert(batch, on_conflict="source,source_id").execute()

    exercise_lookup = {
        (r["source"], r["source_id"]): r["id"]
        for r in sb.table("exercises").select("id,source,source_id").execute().data or []
    }

    link_rows = []
    for r in rows:
        ex_id = exercise_lookup.get((r.get("source"), r.get("source_id")))
        muscle_id = muscle_map.get(r.get("muscle"))
        if ex_id and muscle_id:
            link_rows.append({
                "exercise_id": ex_id,
                "muscle_group_id": muscle_id,
                "is_primary": True,
            })

    for batch in chunked(link_rows, batch_size):
        sb.table("exercise_muscles").upsert(batch, on_conflict="exercise_id,muscle_group_id").execute()

    return {"exercises_loaded": len(exercise_rows), "links_loaded": len(link_rows)}


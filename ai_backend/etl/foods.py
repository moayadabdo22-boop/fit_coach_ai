from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dataset_paths import resolve_dataset_root
from db import require_supabase
from .helpers import chunked


MACRO_MAP = {
    "Protein": "protein_g",
    "Total lipid (fat)": "fat_g",
    "Carbohydrate, by difference": "carbs_g",
    "Energy": "calories",
    "Fiber, total dietary": "fiber_g",
    "Sugars, total including NLEA": "sugar_g",
    "Sodium, Na": "sodium_mg",
}


def load_usda_foods(
    dataset_root: Path | None = None,
    limit: int = 5000,
    batch_size: int = 500,
    include_food_nutrients: bool = False,
) -> dict[str, Any]:
    """
    Load USDA FoodData Central CSVs into Supabase.
    Uses a limited subset by default to avoid massive imports.
    """
    sb = require_supabase()
    dataset_root = dataset_root or resolve_dataset_root()
    foods_path = dataset_root / "food.csv"
    nutrients_path = dataset_root / "nutrient.csv"
    food_nutrients_path = dataset_root / "food_nutrient.csv"

    df_foods = pd.read_csv(foods_path, nrows=limit)
    df_nutrients = pd.read_csv(nutrients_path)

    # Insert nutrients catalog
    nutrient_rows = [
        {
            "code": str(row["id"]),
            "name": row["name"],
            "unit": row["unit_name"],
        }
        for _, row in df_nutrients.iterrows()
    ]
    for batch in chunked(nutrient_rows, batch_size):
        sb.table("nutrients").upsert(batch, on_conflict="code").execute()

    fdc_ids = df_foods["fdc_id"].astype(str).tolist()
    fdc_set = set(fdc_ids)
    nutrient_name_by_id = {str(r["id"]): r["name"] for _, r in df_nutrients.iterrows()}

    macro_by_fdc: dict[str, dict[str, Any]] = {}

    for chunk in pd.read_csv(food_nutrients_path, chunksize=200000):
        chunk["fdc_id"] = chunk["fdc_id"].astype(str)
        filtered = chunk[chunk["fdc_id"].isin(fdc_set)]
        for _, row in filtered.iterrows():
            nutrient_id = str(row["nutrient_id"])
            nutrient_name = nutrient_name_by_id.get(nutrient_id)
            if nutrient_name not in MACRO_MAP:
                continue
            fdc_id = str(row["fdc_id"])
            macro_by_fdc.setdefault(fdc_id, {})[MACRO_MAP[nutrient_name]] = float(row["amount"])
        if len(macro_by_fdc) >= len(fdc_ids):
            break

    food_rows = []
    for _, row in df_foods.iterrows():
        fdc_id = str(row["fdc_id"])
        macros = macro_by_fdc.get(fdc_id, {})
        food_rows.append({
            "source": "USDA",
            "source_id": fdc_id,
            "name": row["description"],
            "calories": macros.get("calories"),
            "protein_g": macros.get("protein_g"),
            "carbs_g": macros.get("carbs_g"),
            "fat_g": macros.get("fat_g"),
            "fiber_g": macros.get("fiber_g"),
            "sugar_g": macros.get("sugar_g"),
            "sodium_mg": macros.get("sodium_mg"),
        })

    for batch in chunked(food_rows, batch_size):
        sb.table("foods").upsert(batch, on_conflict="source,source_id").execute()

    if include_food_nutrients:
        nutrient_id_by_code = {str(r["id"]): str(r["id"]) for _, r in df_nutrients.iterrows()}
        food_id_map = {
            row["source_id"]: row["id"]
            for row in sb.table("foods").select("id,source_id").eq("source", "USDA").execute().data or []
        }

        for chunk in pd.read_csv(food_nutrients_path, chunksize=200000):
            chunk["fdc_id"] = chunk["fdc_id"].astype(str)
            filtered = chunk[chunk["fdc_id"].isin(fdc_set)]
            rows = []
            for _, row in filtered.iterrows():
                food_id = food_id_map.get(str(row["fdc_id"]))
                nutrient_id = nutrient_id_by_code.get(str(row["nutrient_id"]))
                if not food_id or not nutrient_id:
                    continue
                rows.append({
                    "food_id": food_id,
                    "nutrient_id": nutrient_id,
                    "amount": float(row["amount"]),
                })
            for batch in chunked(rows, batch_size):
                sb.table("food_nutrients").insert(batch).execute()

    return {"foods_loaded": len(food_rows), "nutrients_loaded": len(nutrient_rows)}


from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", (text or "").lower())


def _load_json(path: Path) -> list[dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_exercise_csv(path: Path, limit: int = 1000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Title") or row.get("Exercise") or "").strip()
            if not name:
                continue
            rows.append(
                {
                    "exercise": name,
                    "muscle": (row.get("BodyPart") or row.get("Body Part") or "").strip(),
                    "difficulty": (row.get("Level") or row.get("Difficulty") or "Beginner").strip(),
                    "equipment": (row.get("Equipment") or "Bodyweight").strip(),
                    "type": (row.get("Type") or "Strength").strip(),
                    "description": (row.get("Desc") or row.get("Description") or "").strip(),
                }
            )
            if len(rows) >= limit:
                break
    return rows


def _read_food_csv(path: Path, limit: int = 1500) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Food_Item") or row.get("Food") or row.get("name") or "").strip()
            if not name:
                continue
            rows.append(
                {
                    "name": name,
                    "category": (row.get("Category") or row.get("Group") or "").strip(),
                    "calories": int(_safe_float(row.get("Calories (kcal)"), _safe_float(row.get("Calories"), 0.0))),
                    "protein_g": _safe_float(row.get("Protein (g)"), _safe_float(row.get("Protein"), 0.0)),
                    "carbs_g": _safe_float(row.get("Carbohydrates (g)"), _safe_float(row.get("Carbs"), 0.0)),
                    "fat_g": _safe_float(row.get("Fat (g)"), _safe_float(row.get("Fat"), 0.0)),
                    "fiber_g": _safe_float(row.get("Fiber (g)"), _safe_float(row.get("Fiber"), 0.0)),
                    "sugars_g": _safe_float(row.get("Sugars (g)"), _safe_float(row.get("Sugars"), 0.0)),
                    "sodium_mg": _safe_float(row.get("Sodium (mg)"), _safe_float(row.get("Sodium"), 0.0)),
                    "cholesterol_mg": _safe_float(row.get("Cholesterol (mg)"), _safe_float(row.get("Cholesterol"), 0.0)),
                    "meal_type": (row.get("Meal_Type") or row.get("Meal Type") or "any").strip(),
                }
            )
            if len(rows) >= limit:
                break
    return rows


class DataCatalog:
    def __init__(self, dataset_root: Path, derived_root: Path) -> None:
        self.dataset_root = Path(dataset_root)
        self.derived_root = Path(derived_root)
        self.exercises: list[dict[str, Any]] = []
        self.foods: list[dict[str, Any]] = []
        self.diet_profiles: list[dict[str, Any]] = []
        self.fitness_profiles: list[dict[str, Any]] = []
        self.ready = False
        self._load()

    def _load(self) -> None:
        derived_exercises = self.derived_root / "exercises.json"
        derived_foods = self.derived_root / "foods.json"
        derived_diets = self.derived_root / "diet_profiles.json"
        derived_profiles = self.derived_root / "fitness_profiles.json"

        if derived_exercises.exists():
            self.exercises = _load_json(derived_exercises)
        else:
            raw_exercises = self.dataset_root / "megaGymDataset.csv"
            if raw_exercises.exists():
                self.exercises = _read_exercise_csv(raw_exercises)

        if derived_foods.exists():
            self.foods = _load_json(derived_foods)
        else:
            raw_foods = self.dataset_root / "daily_food_nutrition_dataset.csv"
            if raw_foods.exists():
                self.foods = _read_food_csv(raw_foods)

        if derived_diets.exists():
            self.diet_profiles = _load_json(derived_diets)
        if derived_profiles.exists():
            self.fitness_profiles = _load_json(derived_profiles)

        self.ready = bool(self.exercises or self.foods)

    def search_exercises(
        self,
        query: str,
        muscle: str | None = None,
        difficulty: str | None = None,
        equipment: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query_tokens = set(_tokenize(query))
        results: list[tuple[int, dict[str, Any]]] = []
        for item in self.exercises:
            text = " ".join(
                [
                    str(item.get("exercise", "")),
                    str(item.get("muscle", "")),
                    str(item.get("equipment", "")),
                    str(item.get("type", "")),
                ]
            ).lower()
            tokens = set(_tokenize(text))
            score = len(query_tokens.intersection(tokens))
            if muscle and muscle.lower() not in str(item.get("muscle", "")).lower():
                continue
            if difficulty and difficulty.lower() not in str(item.get("difficulty", "")).lower():
                continue
            if equipment and equipment.lower() not in str(item.get("equipment", "")).lower():
                continue
            if score > 0:
                results.append((score, item))

        results.sort(key=lambda x: x[0], reverse=True)
        if results:
            return [item for _, item in results[:limit]]
        return self.exercises[:limit]

    def search_foods(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query_tokens = set(_tokenize(query))
        results: list[tuple[int, dict[str, Any]]] = []
        for item in self.foods:
            text = " ".join([str(item.get("name", "")), str(item.get("category", ""))]).lower()
            tokens = set(_tokenize(text))
            score = len(query_tokens.intersection(tokens))
            if category and category.lower() not in str(item.get("category", "")).lower():
                continue
            if score > 0:
                results.append((score, item))
        results.sort(key=lambda x: x[0], reverse=True)
        if results:
            return [item for _, item in results[:limit]]
        return self.foods[:limit]

    def summary(self) -> dict[str, Any]:
        return {
            "dataset_root": str(self.dataset_root),
            "derived_root": str(self.derived_root),
            "exercise_count": len(self.exercises),
            "food_count": len(self.foods),
            "diet_profiles_count": len(self.diet_profiles),
            "fitness_profiles_count": len(self.fitness_profiles),
            "ready": self.ready,
        }


__all__ = ["DataCatalog"]

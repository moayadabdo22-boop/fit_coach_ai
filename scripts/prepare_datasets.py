from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

BASE_DIR = Path(__file__).resolve().parents[1]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _iter_rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def _estimate_injury_risk(level: str, equipment: str) -> str:
    level_key = (level or "").strip().lower()
    equipment_key = (equipment or "").strip().lower()
    if level_key == "advanced":
        return "high"
    if any(token in equipment_key for token in ("barbell", "machine", "cable")):
        return "medium"
    return "low"


def _estimate_calories_per_session(ex_type: str, weight_kg: float = 70.0, minutes: float = 6.0) -> int:
    met_map = {
        "strength": 6.0,
        "cardio": 8.0,
        "stretching": 3.0,
        "plyometrics": 7.0,
        "powerlifting": 6.5,
        "olympic weightlifting": 7.5,
        "strongman": 7.0,
    }
    met = met_map.get((ex_type or "").strip().lower(), 5.0)
    calories = met * weight_kg * (minutes / 60.0)
    return max(5, int(round(calories)))


def _beginner_alternative(name: str, equipment: str) -> str:
    eq = (equipment or "").strip().lower()
    if "barbell" in eq:
        return f"Bodyweight variation of {name}"
    if "cable" in eq:
        return f"Resistance band version of {name}"
    if "machine" in eq:
        return f"Dumbbell version of {name}"
    return f"Basic {name}"


def build_exercises(raw_path: Path, output_path: Path, limit: int | None = None) -> dict[str, Any]:
    rows = []
    for row in _iter_rows(raw_path):
        name = (row.get("Title") or row.get("Exercise") or "").strip()
        if not name:
            continue
        body_part = (row.get("BodyPart") or row.get("Body Part") or row.get("muscle") or "").strip()
        ex_type = (row.get("Type") or row.get("Exercise Type") or "Strength").strip()
        equipment = (row.get("Equipment") or row.get("equipment") or "Bodyweight").strip()
        level = (row.get("Level") or row.get("Difficulty") or "Beginner").strip()
        description = (row.get("Desc") or row.get("Description") or "").strip()

        rows.append(
            {
                "exercise": name,
                "muscle": body_part or "full body",
                "difficulty": level.title(),
                "equipment": equipment,
                "type": ex_type,
                "description": description,
                "calories_burned_est": _estimate_calories_per_session(ex_type),
                "injury_risk": _estimate_injury_risk(level, equipment),
                "gender_suitability": "all",
                "beginner_alternative": _beginner_alternative(name, equipment),
            }
        )
        if limit and len(rows) >= limit:
            break

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"records": len(rows), "source": str(raw_path)}


def _infer_allergens(name: str, category: str) -> list[str]:
    text = f"{name} {category}".lower()
    allergens = set()
    if any(token in text for token in ("milk", "cheese", "yogurt", "dairy", "butter")):
        allergens.add("dairy")
    if any(token in text for token in ("wheat", "bread", "pasta", "gluten", "barley", "rye")):
        allergens.add("gluten")
    if "egg" in text:
        allergens.add("eggs")
    if any(token in text for token in ("peanut", "almond", "cashew", "walnut", "nut")):
        allergens.add("nuts")
    if any(token in text for token in ("shrimp", "fish", "salmon", "tuna", "seafood")):
        allergens.add("seafood")
    if "soy" in text:
        allergens.add("soy")
    return sorted(allergens)


def _glycemic_index_bucket(carbs: float, sugars: float) -> tuple[str, int]:
    if carbs <= 0:
        return "low", 30
    ratio = sugars / carbs
    if ratio >= 0.5:
        return "high", 70
    if ratio >= 0.25:
        return "medium", 55
    return "low", 30


def _disease_flags(sodium_mg: float, sugars_g: float, cholesterol_mg: float, fat_g: float) -> list[str]:
    flags = set()
    if sugars_g >= 10.0:
        flags.add("diabetes")
    if sodium_mg >= 400.0:
        flags.add("hypertension")
    if cholesterol_mg >= 60.0 or fat_g >= 20.0:
        flags.add("heart_disease")
    return sorted(flags)


def build_foods(raw_path: Path, output_path: Path, limit: int | None = None) -> dict[str, Any]:
    rows = []
    for row in _iter_rows(raw_path):
        name = (row.get("Food_Item") or row.get("Food") or row.get("name") or "").strip()
        if not name:
            continue
        category = (row.get("Category") or row.get("Group") or "").strip()
        calories = _safe_int(row.get("Calories (kcal)"), _safe_int(row.get("Calories"), 0))
        protein = _safe_float(row.get("Protein (g)"), _safe_float(row.get("Protein"), 0.0))
        carbs = _safe_float(row.get("Carbohydrates (g)"), _safe_float(row.get("Carbs"), 0.0))
        fat = _safe_float(row.get("Fat (g)"), _safe_float(row.get("Fat"), 0.0))
        fiber = _safe_float(row.get("Fiber (g)"), _safe_float(row.get("Fiber"), 0.0))
        sugars = _safe_float(row.get("Sugars (g)"), _safe_float(row.get("Sugars"), 0.0))
        sodium = _safe_float(row.get("Sodium (mg)"), _safe_float(row.get("Sodium"), 0.0))
        cholesterol = _safe_float(row.get("Cholesterol (mg)"), _safe_float(row.get("Cholesterol"), 0.0))
        meal_type = (row.get("Meal_Type") or row.get("Meal Type") or "").strip()
        water_ml = _safe_int(row.get("Water_Intake (ml)"), _safe_int(row.get("Water Intake"), 0))

        gi_label, gi_value = _glycemic_index_bucket(carbs, sugars)
        allergens = _infer_allergens(name, category)
        disease_flags = _disease_flags(sodium, sugars, cholesterol, fat)

        rows.append(
            {
                "name": name,
                "category": category or "general",
                "calories": calories,
                "protein_g": protein,
                "carbs_g": carbs,
                "fat_g": fat,
                "fiber_g": fiber,
                "sugars_g": sugars,
                "sodium_mg": sodium,
                "cholesterol_mg": cholesterol,
                "meal_type": meal_type or "any",
                "water_ml": water_ml,
                "glycemic_index_label": gi_label,
                "glycemic_index_value": gi_value,
                "allergens": allergens,
                "disease_flags": disease_flags,
            }
        )
        if limit and len(rows) >= limit:
            break

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"records": len(rows), "source": str(raw_path)}


def build_diet_profiles(raw_path: Path, output_path: Path, limit: int | None = None) -> dict[str, Any]:
    disease_map: dict[str, dict[str, Any]] = {}
    for row in _iter_rows(raw_path):
        disease = (row.get("Disease_Type") or row.get("Disease") or "").strip()
        recommendation = (row.get("Diet_Recommendation") or row.get("Recommendation") or "").strip()
        cuisine = (row.get("Preferred_Cuisine") or row.get("Cuisine") or "").strip()
        if not disease:
            continue
        entry = disease_map.setdefault(
            disease.lower(),
            {"disease": disease, "recommendations": {}, "cuisines": set(), "count": 0},
        )
        if recommendation:
            entry["recommendations"][recommendation] = entry["recommendations"].get(recommendation, 0) + 1
        if cuisine:
            entry["cuisines"].add(cuisine)
        entry["count"] += 1
        if limit and entry["count"] >= limit:
            continue

    output = []
    for entry in disease_map.values():
        top_rec = ""
        if entry["recommendations"]:
            top_rec = max(entry["recommendations"].items(), key=lambda item: item[1])[0]
        output.append(
            {
                "disease": entry["disease"],
                "top_recommendation": top_rec,
                "cuisines": sorted(entry["cuisines"]),
                "samples": entry["count"],
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"records": len(output), "source": str(raw_path)}


def build_fitness_profiles(raw_path: Path, output_path: Path, limit: int | None = None) -> dict[str, Any]:
    profiles = []
    for row in _iter_rows(raw_path):
        profiles.append(
            {
                "id": row.get("ID"),
                "sex": row.get("Sex"),
                "age": _safe_int(row.get("Age")),
                "height_m": _safe_float(row.get("Height")),
                "weight_kg": _safe_float(row.get("Weight")),
                "bmi": _safe_float(row.get("BMI")),
                "level": row.get("Level"),
                "goal": row.get("Fitness Goal"),
                "fitness_type": row.get("Fitness Type"),
                "exercises": row.get("Exercises"),
                "equipment": row.get("Equipment"),
                "diet": row.get("Diet"),
                "recommendation": row.get("Recommendation"),
            }
        )
        if limit and len(profiles) >= limit:
            break

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"records": len(profiles), "source": str(raw_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare derived datasets for the AI fitness coach.")
    parser.add_argument("--dataset-root", type=Path, default=None, help="Path to raw dataset folder.")
    parser.add_argument("--output-root", type=Path, default=None, help="Path to write derived artifacts.")
    parser.add_argument("--limit-exercises", type=int, default=None)
    parser.add_argument("--limit-foods", type=int, default=None)
    parser.add_argument("--limit-profiles", type=int, default=None)
    args = parser.parse_args()

    dataset_root = args.dataset_root or (BASE_DIR / "dataset_")
    output_root = args.output_root or (BASE_DIR / "ai_backend" / "data" / "derived")

    output_root.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {"dataset_root": str(dataset_root), "outputs": {}}

    exercise_csv = dataset_root / "megaGymDataset.csv"
    if exercise_csv.exists():
        manifest["outputs"]["exercises"] = build_exercises(
            exercise_csv,
            output_root / "exercises.json",
            limit=args.limit_exercises,
        )

    food_csv = dataset_root / "daily_food_nutrition_dataset.csv"
    if food_csv.exists():
        manifest["outputs"]["foods"] = build_foods(
            food_csv,
            output_root / "foods.json",
            limit=args.limit_foods,
        )

    diet_csv = dataset_root / "diet_recommendations_dataset.csv"
    if diet_csv.exists():
        manifest["outputs"]["diet_profiles"] = build_diet_profiles(
            diet_csv,
            output_root / "diet_profiles.json",
        )

    fitness_csv = dataset_root / "fitness-recommendation-dataset.csv"
    if fitness_csv.exists():
        manifest["outputs"]["fitness_profiles"] = build_fitness_profiles(
            fitness_csv,
            output_root / "fitness_profiles.json",
            limit=args.limit_profiles,
        )

    meta_path = output_root / "catalog_meta.json"
    meta_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

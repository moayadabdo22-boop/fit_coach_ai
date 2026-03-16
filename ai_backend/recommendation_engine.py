from __future__ import annotations

import math
import random
import uuid
from datetime import datetime
from typing import Any

from data_catalog import DataCatalog
from health_rules import filter_exercises, filter_foods, build_restrictions


WEEK_DAYS = [
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
]


def _normalize_goal(value: str) -> str:
    key = (value or "").strip().lower()
    if key in {"muscle", "muscle_gain", "bulk", "gain"}:
        return "muscle_gain"
    if key in {"fat_loss", "weight_loss", "cut"}:
        return "fat_loss"
    if key in {"endurance", "cardio"}:
        return "endurance"
    return "general_fitness"


def _normalize_level(value: str) -> str:
    key = (value or "").strip().lower()
    if key in {"beginner", "novice"}:
        return "beginner"
    if key in {"advanced", "expert"}:
        return "advanced"
    return "intermediate"


def _equipment_filter(profile: dict[str, Any]) -> list[str]:
    pref = (profile.get("workout_preference") or profile.get("workoutPreference") or "").strip().lower()
    equipment = profile.get("available_equipment") or profile.get("equipment") or []
    if isinstance(equipment, str):
        equipment = [e.strip().lower() for e in equipment.split(",") if e.strip()]
    equipment = [str(e).lower() for e in equipment if str(e).strip()]
    if equipment:
        return equipment
    if pref == "home":
        return ["bodyweight", "bands", "dumbbell", "kettlebell"]
    return []


def _training_days(profile: dict[str, Any]) -> int:
    value = profile.get("training_days_per_week") or profile.get("trainingDaysPerWeek") or profile.get("days_per_week")
    if value is None:
        value = profile.get("workout_frequency") or 3
    try:
        days = int(value)
    except (TypeError, ValueError):
        days = 3
    return max(1, min(7, days))


def _session_duration(profile: dict[str, Any]) -> int:
    value = profile.get("session_duration") or profile.get("sessionDuration") or 45
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        minutes = 45
    return max(20, min(120, minutes))


def _rest_days(days_per_week: int) -> list[str]:
    rest_count = max(0, 7 - days_per_week)
    return [day for day, _ in WEEK_DAYS[-rest_count:]] if rest_count else []


def _split_for_goal(goal: str, days: int) -> list[str]:
    if goal == "muscle_gain":
        base = ["chest", "back", "legs", "shoulders", "arms", "core"]
    elif goal == "fat_loss":
        base = ["full body", "legs", "back", "core", "chest", "cardio"]
    elif goal == "endurance":
        base = ["cardio", "legs", "core", "cardio", "upper body"]
    else:
        base = ["full body", "legs", "back", "chest", "core"]
    return base[:days]


def _sets_reps(goal: str, level: str) -> tuple[str, str, int]:
    if goal == "fat_loss":
        sets = 3
        reps = "12-20"
        rest = 45
    elif goal == "muscle_gain":
        sets = 4
        reps = "6-12"
        rest = 90
    elif goal == "endurance":
        sets = 3
        reps = "15-25"
        rest = 40
    else:
        sets = 3
        reps = "8-12"
        rest = 75

    if level == "beginner":
        sets = max(2, sets - 1)
        rest = min(rest + 15, 120)
    if level == "advanced":
        sets = sets + 1
        rest = max(40, rest - 10)
    return str(sets), reps, rest


def _estimate_calories(goal: str, duration_min: int, weight_kg: float) -> int:
    base_met = 6.0 if goal == "muscle_gain" else 7.0 if goal == "fat_loss" else 5.0
    calories = base_met * weight_kg * (duration_min / 60.0)
    return max(120, int(round(calories)))


def _rng_from_profile(profile: dict[str, Any], salt: str) -> random.Random:
    seed = profile.get("plan_seed")
    if not seed:
        user_id = profile.get("user_id") or profile.get("id") or ""
        goal = _normalize_goal(profile.get("goal"))
        seed = f"{user_id}-{goal}-{salt}"
    return random.Random(str(seed))


class WorkoutPlanGenerator:
    def __init__(self, catalog: DataCatalog):
        self.catalog = catalog

    def generate_plan_options(self, profile: dict[str, Any], count: int = 3) -> list[dict[str, Any]]:
        goal = _normalize_goal(profile.get("goal"))
        level = _normalize_level(profile.get("fitness_level"))
        days_per_week = _training_days(profile)
        duration = _session_duration(profile)
        weight_kg = float(profile.get("weight", 70.0) or 70.0)
        rest_days = _rest_days(days_per_week)

        focus_cycle = _split_for_goal(goal, days_per_week)
        equipment_filter = _equipment_filter(profile)

        base_rng = _rng_from_profile(profile, "workout")
        options: list[dict[str, Any]] = []
        for option_index in range(max(1, count)):
            rng = random.Random(f"{base_rng.random()}-{option_index}")
            plan_days: list[dict[str, Any]] = []
            focus_index = 0
            for day_en, day_ar in WEEK_DAYS:
                if day_en in rest_days:
                    plan_days.append({"day": day_en, "dayAr": day_ar, "focus": "Rest", "exercises": []})
                    continue

                focus = focus_cycle[focus_index % len(focus_cycle)]
                focus_index += 1

                exercises = self.catalog.search_exercises(
                    query=focus,
                    muscle=focus if focus != "full body" else None,
                    difficulty=level,
                    equipment=None,
                    limit=6,
                )
                if equipment_filter:
                    exercises = [
                        ex
                        for ex in exercises
                        if any(eq in str(ex.get("equipment", "")).lower() for eq in equipment_filter)
                    ] or exercises

                exercises = filter_exercises(exercises, profile)
                rng.shuffle(exercises)
                sets, reps, rest_seconds = _sets_reps(goal, level)
                day_payload = []
                for ex in exercises[:5]:
                    day_payload.append(
                        {
                            "name": ex.get("exercise"),
                            "nameAr": ex.get("exercise"),
                            "sets": sets,
                            "reps": reps,
                            "rest_seconds": rest_seconds,
                            "notes": ex.get("description", ""),
                            "equipment": ex.get("equipment", ""),
                            "injury_risk": ex.get("injury_risk", "low"),
                        }
                    )
                plan_days.append({"day": day_en, "dayAr": day_ar, "focus": focus, "exercises": day_payload})

            calories_est = _estimate_calories(goal, duration, weight_kg)
            options.append(
                {
                    "id": f"workout_{uuid.uuid4().hex[:10]}",
                    "type": "workout",
                    "title": f"{goal.replace('_', ' ').title()} Plan {option_index + 1}",
                    "title_ar": f"{goal.replace('_', ' ').title()} Plan {option_index + 1}",
                    "goal": goal,
                    "fitness_level": level,
                    "rest_days": rest_days,
                    "duration_days": 7,
                    "session_duration_minutes": duration,
                    "estimated_calories_per_session": calories_est,
                    "days": plan_days,
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "dataset_catalog",
                }
            )
        return options


def _bmr(profile: dict[str, Any]) -> float:
    weight = float(profile.get("weight", 70.0) or 70.0)
    height = float(profile.get("height", 170.0) or 170.0)
    age = float(profile.get("age", 25.0) or 25.0)
    gender = str(profile.get("gender", "male")).lower()
    if gender.startswith("f"):
        return 10 * weight + 6.25 * height - 5 * age - 161
    return 10 * weight + 6.25 * height - 5 * age + 5


def _activity_factor(days_per_week: int) -> float:
    if days_per_week <= 1:
        return 1.2
    if days_per_week <= 3:
        return 1.375
    if days_per_week <= 5:
        return 1.55
    return 1.725


def _macro_split(goal: str, restrictions: dict[str, Any]) -> dict[str, float]:
    protein = 0.3
    carbs = 0.45
    fat = 0.25

    if goal == "fat_loss":
        protein, carbs, fat = 0.32, 0.38, 0.30
    elif goal == "muscle_gain":
        protein, carbs, fat = 0.30, 0.50, 0.20
    elif goal == "endurance":
        protein, carbs, fat = 0.25, 0.55, 0.20

    diseases = restrictions.get("diseases", [])
    if "diabetes" in diseases:
        carbs = max(0.30, carbs - 0.10)
        fat = min(0.35, fat + 0.05)
        protein = min(0.35, protein + 0.05)

    total = protein + carbs + fat
    return {"protein_pct": protein / total * 100, "carbs_pct": carbs / total * 100, "fat_pct": fat / total * 100}


def _target_calories(profile: dict[str, Any]) -> int:
    if profile.get("target_calories"):
        return int(profile.get("target_calories"))

    goal = _normalize_goal(profile.get("goal"))
    days_per_week = _training_days(profile)
    maintenance = _bmr(profile) * _activity_factor(days_per_week)
    if goal == "muscle_gain":
        maintenance *= 1.1
    elif goal == "fat_loss":
        maintenance *= 0.85
    return max(1200, int(round(maintenance)))


class NutritionPlanGenerator:
    def __init__(self, catalog: DataCatalog):
        self.catalog = catalog

    def generate_plan_options(self, profile: dict[str, Any], count: int = 3) -> list[dict[str, Any]]:
        goal = _normalize_goal(profile.get("goal"))
        daily_calories = _target_calories(profile)
        meals_per_day = int(profile.get("meals_per_day") or 3)
        meals_per_day = max(2, min(6, meals_per_day))

        restrictions = build_restrictions(profile)
        macro = _macro_split(goal, restrictions)
        calories_per_meal = max(150, int(round(daily_calories / meals_per_day)))

        foods = filter_foods(self.catalog.foods, profile)
        foods_by_meal = {}
        for item in foods:
            meal_type = str(item.get("meal_type", "any")).lower()
            foods_by_meal.setdefault(meal_type, []).append(item)

        base_rng = _rng_from_profile(profile, "nutrition")

        options: list[dict[str, Any]] = []
        for option_index in range(max(1, count)):
            rng = random.Random(f"{base_rng.random()}-{option_index}")
            days_payload = []
            for day_en, day_ar in WEEK_DAYS:
                meals = []
                for meal_index in range(meals_per_day):
                    bucket = "any"
                    if meal_index == 0:
                        bucket = "breakfast"
                    elif meal_index == meals_per_day - 1:
                        bucket = "dinner"
                    foods_bucket = foods_by_meal.get(bucket) or foods_by_meal.get("any") or foods
                    if not foods_bucket:
                        foods_bucket = foods

                    if foods_bucket:
                        rng.shuffle(foods_bucket)
                    selected = rng.choice(foods_bucket) if foods_bucket else {}
                    meal_calories = int(selected.get("calories", calories_per_meal) or calories_per_meal)
                    meals.append(
                        {
                            "name": selected.get("name", f"Meal {meal_index + 1}"),
                            "nameAr": selected.get("name", f"Meal {meal_index + 1}"),
                            "description": selected.get("category", ""),
                            "descriptionAr": selected.get("category", ""),
                            "calories": str(meal_calories),
                            "protein": str(int(round(float(selected.get("protein_g", 0.0))))),
                            "carbs": str(int(round(float(selected.get("carbs_g", 0.0))))),
                            "fat": str(int(round(float(selected.get("fat_g", 0.0))))),
                            "time": f"meal_{meal_index + 1}",
                        }
                    )
                days_payload.append({"day": day_en, "dayAr": day_ar, "meals": meals})

            hydration_ml = int(round(float(profile.get("weight", 70.0) or 70.0) * 35.0))
            options.append(
                {
                    "id": f"nutrition_{uuid.uuid4().hex[:10]}",
                    "type": "nutrition",
                    "title": f"{goal.replace('_', ' ').title()} Nutrition {option_index + 1}",
                    "title_ar": f"{goal.replace('_', ' ').title()} Nutrition {option_index + 1}",
                    "goal": goal,
                    "daily_calories": daily_calories,
                    "meals_per_day": meals_per_day,
                    "macro_split": macro,
                    "hydration_ml": hydration_ml,
                    "days": days_payload,
                    "forbidden_foods": restrictions.get("allergies", []),
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "dataset_catalog",
                }
            )

        return options


class RecoveryOptimizer:
    def recommend(self, profile: dict[str, Any], tracking: dict[str, Any] | None = None) -> dict[str, Any]:
        tracking = tracking or {}
        sleep_hours = float(tracking.get("avg_sleep_hours", 0.0) or 0.0)
        if sleep_hours <= 0:
            sleep_hours = 7.0
        readiness = "low" if sleep_hours < 6.5 else "moderate" if sleep_hours < 7.5 else "high"
        adjust = -10 if readiness == "low" else 0
        return {
            "readiness": readiness,
            "recommended_sleep_hours": 7.5,
            "suggested_intensity_adjustment_pct": adjust,
            "notes": "Increase hydration and reduce volume if readiness is low.",
        }


class RecommendationEngine:
    def __init__(self, catalog: DataCatalog):
        self.catalog = catalog
        self.workout = WorkoutPlanGenerator(catalog)
        self.nutrition = NutritionPlanGenerator(catalog)
        self.recovery = RecoveryOptimizer()


__all__ = ["RecommendationEngine"]

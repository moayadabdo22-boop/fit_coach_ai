from __future__ import annotations

from typing import Any, Dict, List

from nlp_utils import normalize_text

INJURY_KEYWORDS = {
    "knee": {"squat", "lunge", "leg", "jump", "run"},
    "back": {"deadlift", "row", "good morning", "hinge"},
    "shoulder": {"overhead", "press", "snatch", "clean", "shoulder"},
}

ALLERGEN_KEYWORDS = {
    "peanut": {"peanut", "nuts"},
    "milk": {"milk", "dairy", "cheese", "yogurt"},
    "egg": {"egg"},
    "wheat": {"wheat", "bread", "gluten"},
    "shellfish": {"shrimp", "crab", "lobster"},
}


def _tokenize(text: str) -> str:
    return normalize_text(text or "")


def filter_workout_plan(plan: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    injuries = _tokenize(profile.get("injuries") or profile.get("chronicConditions") or "")
    if not injuries:
        return plan
    warnings: List[str] = []
    blocked_keywords: set[str] = set()
    for injury, risky in INJURY_KEYWORDS.items():
        if injury in injuries:
            blocked_keywords |= set(risky)
            warnings.append(f"Avoid high stress on {injury}.")

    if not blocked_keywords:
        return plan

    cleaned_days = []
    for day in plan.get("days", []):
        exercises = day.get("exercises", [])
        filtered = []
        for ex in exercises:
            name = _tokenize(ex.get("name") or "")
            if any(risk in name for risk in blocked_keywords):
                continue
            filtered.append(ex)
        day = {**day, "exercises": filtered}
        cleaned_days.append(day)

    return {
        **plan,
        "days": cleaned_days,
        "safety_warnings": warnings,
    }


def filter_nutrition_plan(plan: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    allergies = _tokenize(profile.get("allergies") or "")
    if not allergies:
        return plan
    warnings: List[str] = []
    blocked_keywords: set[str] = set()
    for allergen, risky in ALLERGEN_KEYWORDS.items():
        if allergen in allergies:
            blocked_keywords |= set(risky)
            warnings.append(f"Avoid {allergen} due to allergy.")

    if not blocked_keywords:
        return plan

    cleaned_days = []
    for day in plan.get("days", []):
        meals = day.get("meals", [])
        filtered_meals = []
        for meal in meals:
            ingredients = " ".join(meal.get("ingredients") or [])
            if any(risk in _tokenize(ingredients) for risk in blocked_keywords):
                continue
            filtered_meals.append(meal)
        day = {**day, "meals": filtered_meals}
        cleaned_days.append(day)

    return {
        **plan,
        "days": cleaned_days,
        "safety_warnings": warnings,
    }


def detect_overtraining(profile: Dict[str, Any], tracking_summary: Dict[str, Any] | None) -> bool:
    days_per_week = profile.get("training_days_per_week") or profile.get("trainingDaysPerWeek") or 0
    try:
        days_per_week = int(days_per_week)
    except Exception:
        days_per_week = 0
    if days_per_week >= 6:
        return True
    tracking_summary = tracking_summary or {}
    fatigue = _tokenize(tracking_summary.get("fatigue") or "")
    return "high" in fatigue or "tired" in fatigue

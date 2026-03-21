from __future__ import annotations

from typing import Any


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [v.strip() for v in value.split(",")]
        return [p.lower() for p in parts if p]
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if str(v).strip()]
    return []


def _has_any(text: str, tokens: list[str]) -> bool:
    text_norm = (text or "").lower()
    return any(token in text_norm for token in tokens)


def build_restrictions(profile: dict[str, Any]) -> dict[str, Any]:
    allergies = _normalize_list(profile.get("allergies"))
    diseases = _normalize_list(profile.get("chronic_diseases"))
    dietary_prefs_raw = _normalize_list(profile.get("dietary_preferences"))
    dietary_prefs: list[str] = []
    for pref in dietary_prefs_raw:
        if "vegan" in pref or ("نباتي" in pref and ("صرف" in pref or "صارم" in pref)):
            dietary_prefs.append("vegan")
        elif "vegetarian" in pref or "نباتي" in pref:
            dietary_prefs.append("vegetarian")
        if "halal" in pref or "حلال" in pref:
            dietary_prefs.append("halal")
        if "keto" in pref or "كيتو" in pref:
            dietary_prefs.append("keto")
        if "gluten" in pref or "جلوتين" in pref or "غلوتين" in pref:
            dietary_prefs.append("gluten_free")
        if "lactose" in pref or "لاكتوز" in pref or "dairy" in pref:
            dietary_prefs.append("lactose_free")
        if pref not in dietary_prefs:
            dietary_prefs.append(pref)

    restrictions = {
        "allergies": allergies,
        "diseases": diseases,
        "dietary_preferences": dietary_prefs,
    }
    return restrictions


def filter_foods(food_items: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    restrictions = build_restrictions(profile)
    allergies = restrictions["allergies"]
    diseases = restrictions["diseases"]
    dietary_prefs = restrictions["dietary_preferences"]

    filtered: list[dict[str, Any]] = []
    for item in food_items:
        name = str(item.get("name", ""))
        category = str(item.get("category", ""))
        allergens = [str(a).lower() for a in item.get("allergens", [])]

        if any(a in allergens or _has_any(name, [a]) for a in allergies):
            continue

        if "lactose" in allergies or "dairy" in allergies:
            if _has_any(name, ["milk", "cheese", "yogurt", "dairy", "cream"]):
                continue

        if "gluten" in allergies:
            if _has_any(name, ["wheat", "bread", "pasta", "barley", "rye"]):
                continue

        if "vegan" in dietary_prefs:
            if _has_any(name, ["egg", "milk", "cheese", "yogurt", "meat", "chicken", "fish", "beef", "pork"]):
                continue

        if "vegetarian" in dietary_prefs:
            if _has_any(name, ["meat", "chicken", "fish", "beef", "turkey", "lamb"]):
                continue

        if "halal" in dietary_prefs:
            if _has_any(name, ["pork", "bacon", "ham", "wine", "beer", "alcohol"]):
                continue

        if "gluten_free" in dietary_prefs:
            if _has_any(name, ["wheat", "bread", "pasta", "barley", "rye"]):
                continue

        if "lactose_free" in dietary_prefs:
            if _has_any(name, ["milk", "cheese", "yogurt", "dairy", "cream"]):
                continue

        if "keto" in dietary_prefs:
            if _has_any(name, ["bread", "rice", "pasta", "potato", "oats", "cereal", "sugar"]):
                continue

        sugars = float(item.get("sugars_g", 0.0) or 0.0)
        carbs = float(item.get("carbs_g", 0.0) or 0.0)
        sodium = float(item.get("sodium_mg", 0.0) or 0.0)
        cholesterol = float(item.get("cholesterol_mg", 0.0) or 0.0)
        fat = float(item.get("fat_g", 0.0) or 0.0)

        if "diabetes" in diseases and (sugars > 10.0 or carbs > 45.0):
            continue
        if "hypertension" in diseases and sodium > 400.0:
            continue
        if "heart disease" in diseases or "heart_disease" in diseases:
            if cholesterol > 60.0 or fat > 20.0:
                continue

        filtered.append(item)

    return filtered


def filter_exercises(exercises: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    injuries = _normalize_list(profile.get("injuries"))
    if not injuries:
        return exercises

    filtered: list[dict[str, Any]] = []
    for item in exercises:
        muscle = str(item.get("muscle", "")).lower()
        if "knee" in injuries and "leg" in muscle:
            continue
        if "shoulder" in injuries and "shoulder" in muscle:
            continue
        if "back" in injuries and "back" in muscle:
            continue
        filtered.append(item)

    return filtered


__all__ = ["build_restrictions", "filter_foods", "filter_exercises"]

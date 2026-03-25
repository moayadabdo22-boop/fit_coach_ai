from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db import get_supabase_client
from .deps import get_user_id
from recommendation_engine import RecommendationEngine
from data_catalog import DataCatalog
from dataset_paths import resolve_dataset_root, resolve_derived_root


router = APIRouter(prefix="/api/v1", tags=["plans"])


class WorkoutPlanRequest(BaseModel):
    profile: dict[str, Any]
    count: int = 1
    save: bool = False


class NutritionPlanRequest(BaseModel):
    profile: dict[str, Any]
    count: int = 1
    save: bool = False


def _require_client():
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase is not configured on the backend.")
    return client


def _get_recommender() -> RecommendationEngine:
    dataset_root = resolve_dataset_root()
    derived_root = resolve_derived_root()
    catalog = DataCatalog(dataset_root, derived_root)
    return RecommendationEngine(catalog)


def _ensure_exercise(sb, name: str, equipment: str | None = None, difficulty: str | None = None) -> str:
    existing = sb.table("exercises").select("id").ilike("name", name).execute().data
    if existing:
        return existing[0]["id"]
    payload = {"name": name, "equipment_id": None, "difficulty": difficulty}
    if equipment:
        eq = sb.table("equipment").select("id").ilike("name", equipment).execute().data
        if eq:
            payload["equipment_id"] = eq[0]["id"]
        else:
            new_eq = sb.table("equipment").insert({"name": equipment, "code": equipment.lower().replace(" ", "_")}).execute().data
            if new_eq:
                payload["equipment_id"] = new_eq[0]["id"]
    created = sb.table("exercises").insert(payload).execute().data
    if not created:
        raise HTTPException(status_code=500, detail=f"Failed to create exercise: {name}")
    return created[0]["id"]


def _ensure_food(sb, name: str) -> str:
    existing = sb.table("foods").select("id").ilike("name", name).execute().data
    if existing:
        return existing[0]["id"]
    created = sb.table("foods").insert({"name": name}).execute().data
    if not created:
        raise HTTPException(status_code=500, detail=f"Failed to create food: {name}")
    return created[0]["id"]


@router.post("/workout-plans/generate")
def generate_workout_plan(payload: WorkoutPlanRequest, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    recommender = _get_recommender()
    profile = {**payload.profile, "user_id": user_id}
    options = recommender.workout.generate_plan_options(profile, count=payload.count)
    if not options:
        raise HTTPException(status_code=400, detail="Unable to generate workout plan options.")
    return {"count": len(options), "options": options}


@router.post("/workout-plans/{plan_id}/approve")
def approve_workout_plan(plan_id: str, plan: dict[str, Any], user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    title = plan.get("title") or "AI Workout Plan"
    record = sb.table("workout_plans").insert({
        "user_id": user_id,
        "title": title,
        "is_active": True,
    }).execute().data
    if not record:
        raise HTTPException(status_code=500, detail="Failed to save workout plan.")

    workout_plan_id = record[0]["id"]
    for day_idx, day in enumerate(plan.get("days", [])):
        day_rec = sb.table("workout_days").insert({
            "workout_plan_id": workout_plan_id,
            "day_of_week": day_idx % 7,
            "name": day.get("day") or f"Day {day_idx + 1}",
        }).execute().data
        if not day_rec:
            continue
        day_id = day_rec[0]["id"]
        for item in day.get("exercises", []):
            ex_id = _ensure_exercise(
                sb,
                item.get("name") or "Exercise",
                equipment=item.get("equipment"),
                difficulty=item.get("difficulty"),
            )
            sb.table("workout_items").insert({
                "workout_day_id": day_id,
                "exercise_id": ex_id,
                "sets": item.get("sets"),
                "reps": item.get("reps"),
                "duration_min": item.get("duration_min"),
                "intensity": item.get("intensity"),
                "notes": item.get("notes"),
            }).execute()

    return {"saved": True, "plan_id": workout_plan_id}


@router.post("/meal-plans/generate")
def generate_meal_plan(payload: NutritionPlanRequest, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    recommender = _get_recommender()
    profile = {**payload.profile, "user_id": user_id}
    options = recommender.nutrition.generate_plan_options(profile, count=payload.count)
    if not options:
        raise HTTPException(status_code=400, detail="Unable to generate meal plan options.")
    return {"count": len(options), "options": options}


@router.post("/meal-plans/{plan_id}/approve")
def approve_meal_plan(plan_id: str, plan: dict[str, Any], user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    title = plan.get("title") or "AI Meal Plan"
    record = sb.table("meal_plans").insert({
        "user_id": user_id,
        "title": title,
        "daily_calories": plan.get("daily_calories"),
        "macro_distribution": plan.get("macros"),
        "is_active": True,
    }).execute().data
    if not record:
        raise HTTPException(status_code=500, detail="Failed to save meal plan.")

    meal_plan_id = record[0]["id"]
    for day_idx, day in enumerate(plan.get("days", [])):
        for meal in day.get("meals", []):
            meal_rec = sb.table("meals").insert({
                "meal_plan_id": meal_plan_id,
                "day_of_week": day_idx % 7,
                "meal_time": meal.get("meal_time"),
                "name": meal.get("name"),
                "notes": meal.get("description"),
            }).execute().data
            if not meal_rec:
                continue
            meal_id = meal_rec[0]["id"]
            ingredients = meal.get("ingredients") or []
            for ing in ingredients:
                food_id = _ensure_food(sb, ing)
                sb.table("meal_items").insert({
                    "meal_id": meal_id,
                    "food_id": food_id,
                    "servings": 1,
                }).execute()

    return {"saved": True, "plan_id": meal_plan_id}


@router.get("/workout-plans")
def list_workout_plans(user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    rows = sb.table("workout_plans").select("*").eq("user_id", user_id).execute().data or []
    return {"items": rows}


@router.get("/meal-plans")
def list_meal_plans(user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    rows = sb.table("meal_plans").select("*").eq("user_id", user_id).execute().data or []
    return {"items": rows}


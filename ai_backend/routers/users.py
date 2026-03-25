from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db import get_supabase_client
from .deps import get_user_id


router = APIRouter(prefix="/api/v1", tags=["users"])


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    gender: str | None = Field(default=None, pattern="^(male|female|other)$")
    birth_date: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    fitness_level: str | None = Field(default=None, pattern="^(beginner|intermediate|advanced)$")
    goal_primary: str | None = None
    locale: str | None = None
    timezone: str | None = None


class PreferencesUpdate(BaseModel):
    diet_style: str | None = None
    favorite_foods: list[str] | None = None
    disliked_foods: list[str] | None = None
    workout_time: str | None = None
    equipment_available: list[str] | None = None
    avoid_equipment: list[str] | None = None


class GoalUpdateItem(BaseModel):
    goal_code: str
    priority: int = 1


class GoalsUpdate(BaseModel):
    goals: list[GoalUpdateItem] = Field(default_factory=list)


class ConditionUpdateItem(BaseModel):
    condition_code: str
    severity: str | None = None
    notes: str | None = None


class ConditionsUpdate(BaseModel):
    conditions: list[ConditionUpdateItem] = Field(default_factory=list)


class AllergyUpdateItem(BaseModel):
    allergen_code: str
    severity: str | None = None


class AllergiesUpdate(BaseModel):
    allergies: list[AllergyUpdateItem] = Field(default_factory=list)


def _require_client():
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase is not configured on the backend.")
    return client


@router.get("/users/me")
def get_me(user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    profile = sb.table("user_profiles").select("*").eq("user_id", user_id).execute().data
    preferences = sb.table("user_preferences").select("*").eq("user_id", user_id).execute().data
    goals = sb.table("user_goals").select("*").eq("user_id", user_id).execute().data
    conditions = sb.table("user_conditions").select("*").eq("user_id", user_id).execute().data
    allergies = sb.table("user_allergies").select("*").eq("user_id", user_id).execute().data
    return {
        "profile": (profile[0] if profile else None),
        "preferences": (preferences[0] if preferences else None),
        "goals": goals or [],
        "conditions": conditions or [],
        "allergies": allergies or [],
    }


@router.put("/users/me/profile")
def update_profile(payload: ProfileUpdate, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    data = payload.dict(exclude_none=True)
    data["user_id"] = user_id
    result = sb.table("user_profiles").upsert(data, on_conflict="user_id").execute()
    return {"profile": (result.data[0] if result.data else data)}


@router.put("/users/me/preferences")
def update_preferences(payload: PreferencesUpdate, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    data = payload.dict(exclude_none=True)
    data["user_id"] = user_id
    result = sb.table("user_preferences").upsert(data, on_conflict="user_id").execute()
    return {"preferences": (result.data[0] if result.data else data)}


@router.put("/users/me/goals")
def update_goals(payload: GoalsUpdate, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    goal_codes = [g.goal_code for g in payload.goals]
    if not goal_codes:
        sb.table("user_goals").delete().eq("user_id", user_id).execute()
        return {"goals": []}

    existing = sb.table("goals").select("id,code").in_("code", goal_codes).execute().data or []
    code_to_id = {g["code"]: g["id"] for g in existing}

    rows = [
        {"user_id": user_id, "goal_id": code_to_id[g.goal_code], "priority": g.priority}
        for g in payload.goals
        if g.goal_code in code_to_id
    ]

    sb.table("user_goals").delete().eq("user_id", user_id).execute()
    if rows:
        sb.table("user_goals").insert(rows).execute()

    return {"goals": rows}


@router.put("/users/me/conditions")
def update_conditions(payload: ConditionsUpdate, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    condition_codes = [c.condition_code for c in payload.conditions]
    if not condition_codes:
        sb.table("user_conditions").delete().eq("user_id", user_id).execute()
        return {"conditions": []}

    existing = sb.table("health_conditions").select("id,code").in_("code", condition_codes).execute().data or []
    code_to_id = {c["code"]: c["id"] for c in existing}

    rows = [
        {
            "user_id": user_id,
            "condition_id": code_to_id[c.condition_code],
            "severity": c.severity,
            "notes": c.notes,
        }
        for c in payload.conditions
        if c.condition_code in code_to_id
    ]

    sb.table("user_conditions").delete().eq("user_id", user_id).execute()
    if rows:
        sb.table("user_conditions").insert(rows).execute()

    return {"conditions": rows}


@router.put("/users/me/allergies")
def update_allergies(payload: AllergiesUpdate, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    sb = _require_client()
    allergen_codes = [a.allergen_code for a in payload.allergies]
    if not allergen_codes:
        sb.table("user_allergies").delete().eq("user_id", user_id).execute()
        return {"allergies": []}

    existing = sb.table("allergens").select("id,code").in_("code", allergen_codes).execute().data or []
    code_to_id = {a["code"]: a["id"] for a in existing}

    rows = [
        {
            "user_id": user_id,
            "allergen_id": code_to_id[a.allergen_code],
            "severity": a.severity,
        }
        for a in payload.allergies
        if a.allergen_code in code_to_id
    ]

    sb.table("user_allergies").delete().eq("user_id", user_id).execute()
    if rows:
        sb.table("user_allergies").insert(rows).execute()

    return {"allergies": rows}


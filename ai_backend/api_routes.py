from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data_catalog import DataCatalog
from health_rules import build_restrictions, filter_foods
from progress_engine import ProgressEngine
from recommendation_engine import RecommendationEngine
from storage import LocalJsonStore


class ProfileRequest(BaseModel):
    profile: dict[str, Any]


class PlanRequest(BaseModel):
    profile: dict[str, Any]
    count: int = 3


class ProgressRequest(BaseModel):
    tracking: list[dict[str, Any]]
    goal_weight: float | None = None


def build_api_router(
    catalog: DataCatalog,
    recommender: RecommendationEngine,
    progress_engine: ProgressEngine,
    store: LocalJsonStore,
) -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.get("/profile/{user_id}")
    def get_profile(user_id: str) -> dict[str, Any]:
        profile = store.get_profile(user_id) or {}
        return {"user_id": user_id, "profile": profile}

    @router.put("/profile/{user_id}")
    def put_profile(user_id: str, req: ProfileRequest) -> dict[str, Any]:
        updated = store.upsert_profile(user_id, req.profile)
        return {"user_id": user_id, "profile": updated}

    @router.post("/plans/workout")
    def workout_plan(req: PlanRequest) -> dict[str, Any]:
        options = recommender.workout.generate_plan_options(req.profile, count=req.count)
        if not options:
            raise HTTPException(status_code=400, detail="Unable to generate workout plan options.")
        user_id = req.profile.get("user_id")
        if user_id:
            store.add_plan(str(user_id), "workout", options[0])
        return {"count": len(options), "options": options}

    @router.post("/plans/nutrition")
    def nutrition_plan(req: PlanRequest) -> dict[str, Any]:
        options = recommender.nutrition.generate_plan_options(req.profile, count=req.count)
        if not options:
            raise HTTPException(status_code=400, detail="Unable to generate nutrition plan options.")
        user_id = req.profile.get("user_id")
        if user_id:
            store.add_plan(str(user_id), "nutrition", options[0])
        return {"count": len(options), "options": options}

    @router.post("/constraints/summary")
    def constraints_summary(req: ProfileRequest) -> dict[str, Any]:
        restrictions = build_restrictions(req.profile)
        return {"restrictions": restrictions}

    @router.post("/constraints/filter-foods")
    def constraints_filter_foods(req: ProfileRequest, limit: int = 50) -> dict[str, Any]:
        filtered = filter_foods(catalog.foods, req.profile)
        return {"count": len(filtered), "foods": filtered[:limit]}

    @router.post("/progress/analyze")
    def progress_analyze(req: ProgressRequest) -> dict[str, Any]:
        summary = progress_engine.analyze(req.tracking, goal_weight=req.goal_weight)
        return {"summary": summary.__dict__}

    @router.post("/recovery/recommendation")
    def recovery_recommendation(req: ProfileRequest) -> dict[str, Any]:
        result = recommender.recovery.recommend(req.profile)
        return {"recovery": result}

    @router.get("/catalog/summary")
    def catalog_summary() -> dict[str, Any]:
        return {"summary": catalog.summary()}

    return router


__all__ = ["build_api_router"]

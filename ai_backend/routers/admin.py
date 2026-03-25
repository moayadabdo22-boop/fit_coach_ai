from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from etl.foods import load_usda_foods
from etl.exercises import load_exercises


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/etl/foods")
def etl_foods(background_tasks: BackgroundTasks, limit: int = 5000, include_food_nutrients: bool = False):
    try:
        background_tasks.add_task(load_usda_foods, limit=limit, include_food_nutrients=include_food_nutrients)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"started": True, "job": "foods_etl"}


@router.post("/etl/exercises")
def etl_exercises(background_tasks: BackgroundTasks, limit: int = 5000):
    try:
        background_tasks.add_task(load_exercises, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"started": True, "job": "exercises_etl"}


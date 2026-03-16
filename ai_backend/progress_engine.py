from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np


def _parse_date(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


@dataclass
class ProgressSummary:
    weight_change: float | None
    avg_calories_burned: float | None
    avg_steps: float | None
    avg_sleep_hours: float | None
    adherence_score: float | None
    plateau_detected: bool
    trend_per_week: float | None
    projected_weeks_to_goal: float | None


class ProgressEngine:
    def analyze(self, tracking: list[dict[str, Any]], goal_weight: float | None = None) -> ProgressSummary:
        if not tracking:
            return ProgressSummary(None, None, None, None, None, False, None, None)

        records = []
        for item in tracking:
            date = _parse_date(item.get("date") or item.get("ActivityDate"))
            weight = item.get("weight_kg") or item.get("Weight") or item.get("weight")
            calories = item.get("calories_burned") or item.get("Calories")
            steps = item.get("steps") or item.get("TotalSteps")
            sleep = item.get("sleep_hours") or item.get("SleepHours")
            workouts = item.get("workouts_completed")
            planned = item.get("planned_workouts")
            records.append(
                {
                    "date": date,
                    "weight": float(weight) if weight is not None and weight != "" else None,
                    "calories": float(calories) if calories is not None and calories != "" else None,
                    "steps": float(steps) if steps is not None and steps != "" else None,
                    "sleep": float(sleep) if sleep is not None and sleep != "" else None,
                    "workouts": float(workouts) if workouts is not None and workouts != "" else None,
                    "planned": float(planned) if planned is not None and planned != "" else None,
                }
            )

        records = [r for r in records if r["date"] is not None]
        records.sort(key=lambda r: r["date"])
        if not records:
            return ProgressSummary(None, None, None, None, None, False, None, None)

        weights = [r["weight"] for r in records if r["weight"] is not None]
        weight_change = weights[-1] - weights[0] if len(weights) >= 2 else None

        avg_calories = np.mean([r["calories"] for r in records if r["calories"] is not None]) if records else None
        avg_steps = np.mean([r["steps"] for r in records if r["steps"] is not None]) if records else None
        avg_sleep = np.mean([r["sleep"] for r in records if r["sleep"] is not None]) if records else None

        adherence_values = []
        for r in records:
            if r["planned"] and r["planned"] > 0 and r["workouts"] is not None:
                adherence_values.append(min(1.0, r["workouts"] / r["planned"]))
        adherence = float(np.mean(adherence_values)) if adherence_values else None

        trend_per_week = None
        plateau = False
        projected = None
        if len(weights) >= 4:
            days = [(r["date"] - records[0]["date"]).days for r in records if r["weight"] is not None]
            weight_vals = [r["weight"] for r in records if r["weight"] is not None]
            if len(days) >= 2:
                coeffs = np.polyfit(days, weight_vals, 1)
                trend_per_day = coeffs[0]
                trend_per_week = trend_per_day * 7.0
                plateau = abs(trend_per_week) < 0.1
                if goal_weight is not None and trend_per_week != 0:
                    remaining = goal_weight - weight_vals[-1]
                    projected = abs(remaining / trend_per_week)

        return ProgressSummary(
            weight_change=weight_change,
            avg_calories_burned=float(avg_calories) if avg_calories is not None else None,
            avg_steps=float(avg_steps) if avg_steps is not None else None,
            avg_sleep_hours=float(avg_sleep) if avg_sleep is not None else None,
            adherence_score=adherence,
            plateau_detected=plateau,
            trend_per_week=trend_per_week,
            projected_weeks_to_goal=projected,
        )


__all__ = ["ProgressEngine", "ProgressSummary"]

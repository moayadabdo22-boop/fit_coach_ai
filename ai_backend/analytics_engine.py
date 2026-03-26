from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from nlp_utils import repair_mojibake


@dataclass
class ProgressStats:
    workouts_per_week: int | None = None
    streak_days: int | None = None
    calories_burned_avg: int | None = None
    weight_trend: float | None = None
    adherence: float | None = None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def compute_stats(tracking_summary: Dict[str, Any] | None) -> ProgressStats:
    tracking_summary = tracking_summary or {}
    weekly = tracking_summary.get("weekly_stats") if isinstance(tracking_summary.get("weekly_stats"), dict) else {}
    monthly = tracking_summary.get("monthly_stats") if isinstance(tracking_summary.get("monthly_stats"), dict) else {}

    workouts = _to_int(weekly.get("workout_days") or weekly.get("completed_workouts") or weekly.get("sessions"))
    streak = _to_int(tracking_summary.get("streak_days") or tracking_summary.get("current_streak") or tracking_summary.get("streak"))
    calories = _to_int(weekly.get("calories_burned") or weekly.get("avg_calories_burned") or monthly.get("avg_calories_burned"))
    adherence = _to_float(weekly.get("adherence") or tracking_summary.get("adherence"))
    weight_trend = _to_float(monthly.get("weight_trend") or tracking_summary.get("weight_trend"))

    return ProgressStats(
        workouts_per_week=workouts,
        streak_days=streak,
        calories_burned_avg=calories,
        weight_trend=weight_trend,
        adherence=adherence,
    )


def generate_insights(stats: ProgressStats, language: str = "en") -> List[str]:
    insights: List[str] = []
    if stats.workouts_per_week is not None:
        if stats.workouts_per_week < 2:
            insights.append("Your consistency dropped this week." if language == "en" else "التزامك هذا الأسبوع أقل من المعتاد.")
        elif stats.workouts_per_week >= 4:
            insights.append("Great consistency this week." if language == "en" else "التزام ممتاز هذا الأسبوع.")
    if stats.streak_days is not None and stats.streak_days >= 5:
        insights.append("Nice streak — keep it going." if language == "en" else "سلسلة ممتازة — كمل عليها.")
    if stats.calories_burned_avg is not None and stats.calories_burned_avg < 150:
        insights.append("Try to add light movement to raise daily burn." if language == "en" else "جرّب تضيف حركة خفيفة لرفع الحرق اليومي.")
    if stats.weight_trend is not None:
        if stats.weight_trend < 0:
            insights.append("Your weight trend is moving down." if language == "en" else "الوزن عم ينزل بشكل ملحوظ.")
        elif stats.weight_trend > 0:
            insights.append("Your weight trend is moving up." if language == "en" else "الوزن عم يزيد بشكل ملحوظ.")

    return [repair_mojibake(line) for line in insights if line]


def dashboard_summary(stats: ProgressStats) -> dict[str, Any]:
    return {
        "workouts_per_week": stats.workouts_per_week,
        "streak_days": stats.streak_days,
        "calories_burned_avg": stats.calories_burned_avg,
        "weight_trend": stats.weight_trend,
        "adherence": stats.adherence,
    }

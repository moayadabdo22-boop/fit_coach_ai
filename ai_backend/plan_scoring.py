from __future__ import annotations

from typing import Any

from nlp_utils import normalize_text


def _normalize(value: Any) -> str:
    return normalize_text(str(value or ""))


def _goal_match(plan_goal: str, user_goal: str) -> float:
    if not user_goal:
        return 0.4
    pg = _normalize(plan_goal)
    ug = _normalize(user_goal)
    if ug and ug in pg:
        return 1.0
    if any(token in pg for token in ug.split()):
        return 0.7
    return 0.2


def _level_score(plan_level: str, user_level: str) -> float:
    levels = {"beginner": 1, "intermediate": 2, "advanced": 3}
    pl = _normalize(plan_level)
    ul = _normalize(user_level)
    plan_value = 2
    for key, value in levels.items():
        if key in pl:
            plan_value = value
            break
    user_value = levels.get(ul, 2)
    diff = abs(plan_value - user_value)
    return 1.0 if diff == 0 else 0.6 if diff == 1 else 0.3


def _equipment_score(plan_equipment: str, user_equipment: str, location: str) -> float:
    if not plan_equipment and not user_equipment:
        return 0.6
    pe = _normalize(plan_equipment)
    ue = _normalize(user_equipment)
    if location and _normalize(location) in {"home", "gym"}:
        if "gym" in pe and "home" in _normalize(location):
            return 0.2
    if ue and ue in pe:
        return 1.0
    if any(token in pe for token in ue.split()):
        return 0.7
    return 0.4 if not ue else 0.2


def _preference_score(plan_text: str, prefs: str) -> float:
    if not prefs:
        return 0.5
    pt = _normalize(plan_text)
    pr = _normalize(prefs)
    if pr and pr in pt:
        return 1.0
    if any(token in pt for token in pr.split()):
        return 0.7
    return 0.3


def score_plan(plan: dict[str, Any], profile: dict[str, Any], feedback_penalty: float = 0.0) -> float:
    user_goal = profile.get("goal") or profile.get("goal_label") or ""
    user_level = profile.get("fitness_level") or profile.get("fitnessLevel") or "intermediate"
    user_equipment = profile.get("equipment") or profile.get("available_equipment") or ""
    location = profile.get("location") or ""
    user_prefs = profile.get("dietary_preferences") or profile.get("dietaryPreferences") or ""

    plan_goal = plan.get("goal") or plan.get("target_goal") or plan.get("plan_goal") or ""
    plan_level = plan.get("level") or plan.get("difficulty") or ""
    plan_equipment = plan.get("equipment") or plan.get("required_equipment") or ""
    plan_text = " ".join(
        str(plan.get(k) or "") for k in ("program_name", "title", "description", "plan_name")
    )

    goal_match = _goal_match(str(plan_goal), str(user_goal))
    level_match = _level_score(str(plan_level), str(user_level))
    equipment_match = _equipment_score(str(plan_equipment), str(user_equipment), str(location))
    preference_match = _preference_score(plan_text, str(user_prefs))

    score = (
        goal_match * 0.4
        + level_match * 0.3
        + equipment_match * 0.2
        + preference_match * 0.1
    )
    score = max(0.0, min(1.0, score - feedback_penalty))
    return score


def rank_plans(
    plans: list[dict[str, Any]],
    profile: dict[str, Any],
    feedback_penalties: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    feedback_penalties = feedback_penalties or {}
    scored = []
    for plan in plans:
        plan_id = str(plan.get("id") or plan.get("plan_id") or "")
        penalty = feedback_penalties.get(plan_id, 0.0)
        scored.append((score_plan(plan, profile, penalty), plan))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [plan for _score, plan in scored]

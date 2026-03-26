from __future__ import annotations

from datetime import datetime
from typing import Any

from db import get_supabase_client


def record_plan_feedback(
    user_id: str,
    plan_id: str,
    plan_type: str,
    difficulty: int | None = None,
    satisfaction: int | None = None,
    adherence: float | None = None,
    notes: str | None = None,
) -> dict[str, Any] | None:
    sb = get_supabase_client()
    if not sb:
        return None
    payload = {
        "user_id": user_id,
        "plan_id": plan_id,
        "plan_type": plan_type,
        "difficulty": difficulty,
        "satisfaction": satisfaction,
        "adherence": adherence,
        "notes": notes,
        "created_at": datetime.utcnow().isoformat(),
    }
    try:
        resp = sb.table("plan_feedback").insert(payload).execute()
        rows = resp.data or []
        return rows[0] if rows else payload
    except Exception:
        return None


def get_feedback_summary(user_id: str) -> dict[str, float]:
    sb = get_supabase_client()
    if not sb:
        return {}
    try:
        rows = sb.table("plan_feedback").select("*").eq("user_id", user_id).execute().data or []
    except Exception:
        return {}
    penalties: dict[str, float] = {}
    for row in rows:
        plan_id = str(row.get("plan_id") or "")
        satisfaction = row.get("satisfaction")
        adherence = row.get("adherence")
        penalty = 0.0
        if satisfaction is not None and satisfaction <= 2:
            penalty += 0.25
        if adherence is not None and adherence < 0.5:
            penalty += 0.2
        if penalty > 0:
            penalties[plan_id] = min(0.6, penalties.get(plan_id, 0.0) + penalty)
    return penalties

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from db import get_supabase_client


def save_memory(
    user_id: str,
    key: str,
    value: Any,
    importance_score: float = 0.5,
) -> dict[str, Any] | None:
    sb = get_supabase_client()
    if not sb:
        return None
    payload = {
        "user_id": user_id,
        "key": key,
        "value": value,
        "importance_score": float(importance_score),
        "created_at": datetime.utcnow().isoformat(),
    }
    try:
        resp = sb.table("coach_memory").upsert(payload, on_conflict="user_id,key").execute()
        rows = resp.data or []
        return rows[0] if rows else payload
    except Exception:
        return None


def retrieve_memory(
    user_id: str,
    limit: int = 50,
    min_importance: float = 0.0,
) -> list[dict[str, Any]]:
    sb = get_supabase_client()
    if not sb:
        return []
    try:
        resp = (
            sb.table("coach_memory")
            .select("*")
            .eq("user_id", user_id)
            .gte("importance_score", min_importance)
            .order("importance_score", desc=True)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def summarize_memory(items: Iterable[dict[str, Any]]) -> str:
    lines = []
    for item in items:
        key = item.get("key")
        value = item.get("value")
        if value is None:
            continue
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def get_coach_memory(user_id: str) -> dict[str, Any] | None:
    items = retrieve_memory(user_id, limit=50)
    if not items:
        return None
    merged: dict[str, Any] = {"user_id": user_id}
    for item in items:
        merged[item.get("key")] = item.get("value")
    merged["items"] = items
    return merged


def upsert_coach_memory(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    if not updates:
        return get_coach_memory(user_id)
    for key, value in updates.items():
        if value is None:
            continue
        importance = 0.6 if key in {"goals", "goal", "preferences"} else 0.5
        save_memory(user_id, key, value, importance_score=importance)
    return get_coach_memory(user_id)

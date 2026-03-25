from __future__ import annotations

from datetime import datetime
from typing import Any

from db import get_supabase_client


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged.get(key) or {}, value)
        else:
            merged[key] = value
    return merged


def get_coach_memory(user_id: str) -> dict[str, Any] | None:
    sb = get_supabase_client()
    if not sb:
        return None
    try:
        resp = sb.table("coach_memory").select("*").eq("user_id", user_id).execute()
        rows = resp.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def upsert_coach_memory(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase_client()
    if not sb:
        return None
    existing = get_coach_memory(user_id) or {}
    base = {k: v for k, v in existing.items() if k not in {"id", "created_at"}}
    merged = _deep_merge(base, updates)
    merged["user_id"] = user_id
    merged["updated_at"] = datetime.utcnow().isoformat()
    try:
        resp = sb.table("coach_memory").upsert(merged, on_conflict="user_id").execute()
        rows = resp.data or []
        return rows[0] if rows else merged
    except Exception:
        return None


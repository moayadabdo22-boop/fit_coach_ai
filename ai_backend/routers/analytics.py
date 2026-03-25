from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_supabase_client
from .deps import get_user_id


router = APIRouter(prefix="/api/v1", tags=["analytics"])


def _require_client():
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase is not configured on the backend.")
    return client


@router.get("/progress/logs")
def get_progress_logs(
    user_id: str = Depends(get_user_id),
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    sb = _require_client()
    query = sb.table("user_progress_logs").select("*").eq("user_id", user_id)
    if from_date:
        query = query.gte("log_date", from_date)
    if to_date:
        query = query.lte("log_date", to_date)
    rows = query.execute().data or []
    return {"items": rows}


@router.get("/analytics/summary")
def analytics_summary(
    user_id: str = Depends(get_user_id),
    range: str = Query(default="weekly", pattern="^(weekly|monthly)$"),
) -> dict[str, Any]:
    sb = _require_client()
    days = 7 if range == "weekly" else 30
    since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
    rows = (
        sb.table("user_progress_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("log_date", since)
        .execute()
        .data
        or []
    )

    weights = [r.get("weight_kg") for r in rows if r.get("weight_kg") is not None]
    adherence = len(rows) / max(days, 1)
    trend = None
    if len(weights) >= 2:
        trend = weights[-1] - weights[0]

    return {
        "range": range,
        "logs": len(rows),
        "adherence_score": round(adherence * 100, 2),
        "weight_trend": trend,
    }


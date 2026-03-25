from __future__ import annotations

from fastapi import Header, HTTPException, Query


def get_user_id(
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
    user_id: str | None = Query(default=None),
) -> str:
    uid = x_user_id or user_id
    if not uid:
        raise HTTPException(status_code=401, detail="Missing user_id. Provide x-user-id header or user_id query param.")
    return uid


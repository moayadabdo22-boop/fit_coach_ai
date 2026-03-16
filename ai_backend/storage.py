from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class LocalJsonStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {"profiles": {}, "plans": [], "tracking": {}}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self._data = {"profiles": {}, "plans": [], "tracking": {}}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self._data.get("profiles", {}).get(user_id)

    def upsert_profile(self, user_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        profiles = self._data.setdefault("profiles", {})
        merged = {**profiles.get(user_id, {}), **profile}
        merged["updated_at"] = datetime.utcnow().isoformat()
        profiles[user_id] = merged
        self._save()
        return merged

    def add_plan(self, user_id: str, plan_type: str, plan: dict[str, Any]) -> dict[str, Any]:
        plans = self._data.setdefault("plans", [])
        record = {
            "user_id": user_id,
            "plan_type": plan_type,
            "plan": plan,
            "created_at": datetime.utcnow().isoformat(),
        }
        plans.append(record)
        self._save()
        return record

    def get_plans(self, user_id: str, plan_type: str | None = None) -> list[dict[str, Any]]:
        plans = self._data.get("plans", [])
        results = [p for p in plans if p.get("user_id") == user_id]
        if plan_type:
            results = [p for p in results if p.get("plan_type") == plan_type]
        return results

    def log_tracking(self, user_id: str, entry: dict[str, Any]) -> dict[str, Any]:
        tracking = self._data.setdefault("tracking", {})
        items = tracking.setdefault(user_id, [])
        record = {**entry}
        record["logged_at"] = datetime.utcnow().isoformat()
        items.append(record)
        self._save()
        return record

    def get_tracking(self, user_id: str, days: int | None = None) -> list[dict[str, Any]]:
        items = self._data.get("tracking", {}).get(user_id, [])
        if not days:
            return items
        cutoff = datetime.utcnow() - timedelta(days=int(days))
        results = []
        for item in items:
            date_str = item.get("date")
            try:
                date = datetime.strptime(str(date_str), "%Y-%m-%d")
            except Exception:
                results.append(item)
                continue
            if date >= cutoff:
                results.append(item)
        return results


def get_local_store() -> LocalJsonStore:
    return LocalJsonStore(Path(__file__).resolve().parent / "data" / "local_store.json")


__all__ = ["LocalJsonStore", "get_local_store"]

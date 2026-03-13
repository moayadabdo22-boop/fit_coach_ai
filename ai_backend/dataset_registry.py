from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _safe_read_csv_header(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            return [str(h).strip() for h in header if str(h).strip()]
    except Exception:
        return []


def _safe_read_csv_sample(path: Path, max_rows: int = 2) -> list[str]:
    samples: list[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for _ in range(max_rows):
                row = next(reader, None)
                if row is None:
                    break
                text = " | ".join([str(cell).strip() for cell in row if str(cell).strip()][:8]).strip()
                if text:
                    samples.append(text[:280])
    except Exception:
        return []
    return samples


def _safe_read_json_keys(path: Path) -> list[str]:
    try:
        if path.stat().st_size > 20 * 1024 * 1024:
            return []
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            obj = json.load(f)
        if isinstance(obj, dict):
            return [str(k) for k in list(obj.keys())[:25]]
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            return [str(k) for k in list(obj[0].keys())[:25]]
    except Exception:
        return []
    return []


def _infer_tags(path: Path, header: list[str]) -> list[str]:
    path_text = str(path).lower()
    header_text = " ".join(header).lower()
    combined = f"{path_text} {header_text}"
    tags: list[str] = []

    if any(k in combined for k in ("nutrition", "food", "meal", "calorie", "macro", "protein", "carb", "fat")):
        tags.append("nutrition")
    if any(k in combined for k in ("workout", "exercise", "gym", "muscle", "sets", "reps", "body part")):
        tags.append("workout")
    if any(k in combined for k in ("attendance", "adherence", "success", "check_in", "visit_date")):
        tags.append("plan_success")
    if any(k in combined for k in ("weight", "bmi", "bodyfat", "body fat", "height", "progress")):
        tags.append("body_progress")
    if any(k in combined for k in ("conversation", "intent", "chat", "response")):
        tags.append("conversation")
    if any(k in combined for k in ("program", "plan", "schedule")):
        tags.append("plans")

    if not tags:
        tags.append("misc")
    return sorted(set(tags))


class DatasetRegistry:
    def __init__(self, dataset_root: Path, index_output_path: Path):
        self.dataset_root = Path(dataset_root)
        self.index_output_path = Path(index_output_path)
        self.index: dict[str, Any] = {"generated_at": "", "dataset_root": str(self.dataset_root), "entries": []}

    def build_index(self, force_rebuild: bool = False) -> dict[str, Any]:
        if not force_rebuild and self.index_output_path.exists():
            try:
                with self.index_output_path.open("r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict) and isinstance(loaded.get("entries"), list):
                    self.index = loaded
                    return self.index
            except Exception:
                pass

        if not self.dataset_root.exists():
            self.index = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "dataset_root": str(self.dataset_root),
                "entries": [],
            }
            return self.index

        entries: list[dict[str, Any]] = []
        for file_path in sorted([p for p in self.dataset_root.rglob("*") if p.is_file()]):
            ext = file_path.suffix.lower()
            rel_path = str(file_path.relative_to(self.dataset_root))
            parts = [part for part in Path(rel_path).parts]
            category = parts[0] if parts else "root"

            header: list[str] = []
            sample: list[str] = []
            json_keys: list[str] = []

            if ext == ".csv":
                header = _safe_read_csv_header(file_path)
                sample = _safe_read_csv_sample(file_path, max_rows=2)
            elif ext == ".json":
                json_keys = _safe_read_json_keys(file_path)
                header = json_keys[:]

            tags = _infer_tags(Path(rel_path), header)
            entries.append(
                {
                    "relative_path": rel_path,
                    "absolute_path": str(file_path),
                    "category": category,
                    "extension": ext or "",
                    "size_bytes": int(file_path.stat().st_size),
                    "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "header": header[:30],
                    "sample": sample[:2],
                    "json_keys": json_keys[:30],
                    "tags": tags,
                }
            )

        self.index = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_root": str(self.dataset_root),
            "entries": entries,
        }
        self.index_output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.index_output_path.open("w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
        return self.index

    def summary(self) -> dict[str, Any]:
        entries = self.index.get("entries", [])
        ext_counter = Counter()
        cat_counter = Counter()
        tag_counter = Counter()
        total_size = 0
        for item in entries:
            ext_counter[item.get("extension", "")] += 1
            cat_counter[item.get("category", "")] += 1
            for tag in item.get("tags", []):
                tag_counter[tag] += 1
            total_size += int(item.get("size_bytes", 0) or 0)
        return {
            "dataset_root": self.index.get("dataset_root"),
            "generated_at": self.index.get("generated_at"),
            "files_count": len(entries),
            "total_size_bytes": total_size,
            "by_extension": dict(ext_counter),
            "by_category": dict(cat_counter),
            "by_tag": dict(tag_counter),
        }

    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        q = (query or "").strip().lower()
        if not q:
            return []
        query_tokens = [t for t in q.replace("_", " ").replace("-", " ").split(" ") if t]

        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self.index.get("entries", []):
            blob = " ".join(
                [
                    str(item.get("relative_path", "")),
                    " ".join(item.get("header", [])),
                    " ".join(item.get("json_keys", [])),
                    " ".join(item.get("tags", [])),
                    " ".join(item.get("sample", [])),
                ]
            ).lower()
            score = 0.0
            for tok in query_tokens:
                if tok in blob:
                    score += 1.0
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, item in scored[: max(1, top_k)]:
            slim = {
                "score": score,
                "relative_path": item.get("relative_path"),
                "category": item.get("category"),
                "extension": item.get("extension"),
                "size_bytes": item.get("size_bytes"),
                "tags": item.get("tags", []),
                "header": item.get("header", [])[:20],
            }
            results.append(slim)
        return results

    def tagged_files(self, tag: str) -> list[dict[str, Any]]:
        target = (tag or "").strip().lower()
        if not target:
            return []
        matches = []
        for item in self.index.get("entries", []):
            tags = [str(t).lower() for t in item.get("tags", [])]
            if target in tags:
                matches.append(item)
        return matches

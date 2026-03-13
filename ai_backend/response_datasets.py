from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from nlp_utils import fuzzy_contains_any, repair_mojibake_deep


def _safe_load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except Exception:
        return default
    return repair_mojibake_deep(parsed)


class ResponseDatasets:
    """Loads week-2 response/program datasets and provides lookup helpers."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.workout_programs: List[Dict[str, Any]] = []
        self.nutrition_programs: List[Dict[str, Any]] = []
        self.intents: Dict[str, Dict[str, Any]] = {}
        self.intent_patterns: Dict[str, set[str]] = {}

        self._load()

    def _load(self) -> None:
        self.workout_programs = _safe_load_json(
            self.base_dir / "workout_programs.json",
            [],
        )
        self.nutrition_programs = _safe_load_json(
            self.base_dir / "nutrition_programs.json",
            [],
        )
        intents_payload = _safe_load_json(
            self.base_dir / "conversation_intents.json",
            {"intents": []},
        )
        intents_list = intents_payload.get("intents", []) if isinstance(intents_payload, dict) else []
        for item in intents_list:
            if not isinstance(item, dict):
                continue
            tag = str(item.get("tag", "")).strip()
            if not tag:
                continue
            self.intents[tag] = item
            patterns = item.get("patterns", [])
            pattern_set = {str(p).strip() for p in patterns if str(p).strip()}
            self.intent_patterns[tag] = pattern_set

    def get_intent(self, tag: str) -> Optional[Dict[str, Any]]:
        return self.intents.get(tag)

    def matches_intent(self, text: str, tag: str) -> bool:
        patterns = self.intent_patterns.get(tag, set())
        if not patterns:
            return False
        return fuzzy_contains_any(text, patterns)

    def pick_response(self, tag: str, language: str, seed: str = "") -> Optional[str]:
        intent = self.get_intent(tag)
        if not intent:
            return None
        responses = intent.get("responses", [])
        if not isinstance(responses, list) or not responses:
            return None

        def _is_arabic_text(value: Any) -> bool:
            return isinstance(value, str) and bool(re.search(r"[\u0600-\u06FF]", value))

        filtered = responses
        if language in {"ar", "ar_fusha", "ar_jordanian"}:
            arabic_only = [item for item in responses if _is_arabic_text(item)]
            if arabic_only:
                filtered = arabic_only
        elif language == "en":
            english_like = [item for item in responses if not _is_arabic_text(item)]
            if english_like:
                filtered = english_like

        idx = abs(hash(f"{tag}|{seed or 'default'}")) % len(filtered)
        selected = filtered[idx]
        if isinstance(selected, str):
            return selected
        if isinstance(selected, dict):
            if language == "en":
                return selected.get("en") or selected.get("ar") or selected.get("text")
            return selected.get("ar") or selected.get("en") or selected.get("text")
        return None

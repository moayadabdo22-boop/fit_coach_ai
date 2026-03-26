from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nlp_utils import normalize_text


@dataclass
class RouteDecision:
    response_type: str
    mode: str
    scores: dict[str, float]


class IntelligentRouter:
    def __init__(self) -> None:
        pass

    def _dataset_confidence(self, dataset_match: bool) -> float:
        return 0.9 if dataset_match else 0.2

    def _complexity_score(self, message: str) -> float:
        text = normalize_text(message)
        if not text:
            return 0.0
        length_score = min(1.0, len(text.split()) / 20)
        multi_intent = 0.2 if ("?" in message or " و " in message) else 0.0
        return min(1.0, length_score + multi_intent)

    def _context_need(self, profile: dict[str, Any]) -> float:
        if not profile:
            return 0.6
        missing = 0
        for field in ("goal", "fitness_level", "training_days_per_week"):
            if not profile.get(field) and not profile.get(field.replace("_", "")):
                missing += 1
        return min(1.0, 0.3 + 0.2 * missing)

    def _mode(self, message: str) -> str:
        text = normalize_text(message)
        if any(token in text for token in ["plan", "program", "خطة", "برنامج", "تمارين", "تغذية"]):
            return "PLAN_MODE"
        if any(token in text for token in ["progress", "streak", "analytics", "تقدم", "احصاء", "تحليل"]):
            return "ANALYTICS_MODE"
        if any(token in text for token in ["motivate", "encourage", "تحفيز", "مشجع"]):
            return "MOTIVATION_MODE"
        return "CHAT_MODE"

    def route(self, message: str, profile: dict[str, Any], dataset_match: bool) -> RouteDecision:
        dataset_conf = self._dataset_confidence(dataset_match)
        complexity = self._complexity_score(message)
        context_need = self._context_need(profile)
        mode = self._mode(message)

        if dataset_conf > 0.75 and complexity < 0.45 and context_need < 0.6:
            response_type = "dataset"
        elif dataset_conf > 0.6 and (complexity >= 0.45 or context_need >= 0.6):
            response_type = "hybrid"
        else:
            response_type = "llm"

        return RouteDecision(
            response_type=response_type,
            mode=mode,
            scores={
                "dataset_confidence": dataset_conf,
                "complexity": complexity,
                "context_need": context_need,
            },
        )

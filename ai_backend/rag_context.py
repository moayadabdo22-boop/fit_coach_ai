from __future__ import annotations

from typing import Any

from data_catalog import DataCatalog


EXERCISE_HINTS = {
    "exercise",
    "workout",
    "train",
    "muscle",
    "strength",
    "lift",
    "cardio",
}

FOOD_HINTS = {
    "food",
    "meal",
    "nutrition",
    "calorie",
    "protein",
    "carb",
    "fat",
    "diet",
}


def _contains_any(text: str, tokens: set[str]) -> bool:
    lower = (text or "").lower()
    return any(token in lower for token in tokens)


class RagContextBuilder:
    def __init__(self, catalog: DataCatalog):
        self.catalog = catalog

    def build(self, user_message: str, profile: dict[str, Any] | None = None, top_k: int = 3) -> str:
        profile = profile or {}
        lines: list[str] = []

        if _contains_any(user_message, EXERCISE_HINTS):
            exercises = self.catalog.search_exercises(user_message, limit=top_k)
            if exercises:
                lines.append("Exercise catalog matches:")
                for ex in exercises[:top_k]:
                    lines.append(
                        f"- {ex.get('exercise')} ({ex.get('muscle')}, {ex.get('equipment')}, {ex.get('difficulty')})"
                    )

        if _contains_any(user_message, FOOD_HINTS):
            foods = self.catalog.search_foods(user_message, limit=top_k)
            if foods:
                lines.append("Nutrition catalog matches:")
                for food in foods[:top_k]:
                    lines.append(
                        f"- {food.get('name')} ({food.get('calories')} kcal, P{food.get('protein_g')} C{food.get('carbs_g')} F{food.get('fat_g')})"
                    )

        return "\n".join(lines).strip()


__all__ = ["RagContextBuilder"]

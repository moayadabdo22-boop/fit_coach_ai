from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from utils_logger import log_error


class AIEngine:
    """Exercise retrieval engine with fast lexical search and optional semantic mode."""

    def __init__(self, data_path: str | Path, enable_semantic: bool = False):
        self.data_path = Path(data_path)
        self.exercises = self._load_exercises()
        self.enable_semantic = enable_semantic

        self._semantic_ready = False
        self._model: Any = None
        self._corpus_embeddings: np.ndarray | None = None
        self._corpus_texts = [self._to_text(ex) for ex in self.exercises]

        if self.enable_semantic:
            self._try_init_semantic()

    def _load_exercises(self) -> list[dict[str, Any]]:
        with self.data_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _to_text(exercise: dict[str, Any]) -> str:
        parts = [
            str(exercise.get("exercise", "")),
            str(exercise.get("muscle", "")),
            str(exercise.get("difficulty", "")),
            str(exercise.get("equipment", "")),
            str(exercise.get("description", "")),
        ]
        injury_safe = exercise.get("injury_safe")
        if isinstance(injury_safe, list):
            parts.extend(str(item) for item in injury_safe)
        return " ".join(p for p in parts if p).lower()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9\u0600-\u06FF]+", text.lower())

    @staticmethod
    def _score_lexical(query_tokens: set[str], exercise_text: str) -> int:
        if not query_tokens:
            return 0
        tokens = set(AIEngine._tokenize(exercise_text))
        return len(query_tokens.intersection(tokens))

    def _try_init_semantic(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = self._model.encode(
                self._corpus_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            self._corpus_embeddings = embeddings.astype(np.float32)
            self._semantic_ready = True
        except Exception as exc:
            self._semantic_ready = False
            self._model = None
            self._corpus_embeddings = None
            log_error("AI_ENGINE_SEMANTIC_INIT_FAILED", None, exc, {"fallback": "lexical_only"})

    def _search_semantic(self, query: str, top_k: int) -> list[dict[str, Any]]:
        if not self._semantic_ready or self._model is None or self._corpus_embeddings is None:
            return []

        query_vec = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0].astype(np.float32)
        scores = np.dot(self._corpus_embeddings, query_vec)
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [self.exercises[i] for i in ranked_indices if 0 <= i < len(self.exercises)]

    def _search_lexical(self, query: str, top_k: int) -> list[dict[str, Any]]:
        query_tokens = set(self._tokenize(query))
        scored: list[tuple[int, dict[str, Any]]] = []
        for idx, exercise_text in enumerate(self._corpus_texts):
            score = self._score_lexical(query_tokens, exercise_text)
            if score > 0:
                scored.append((score, self.exercises[idx]))

        scored.sort(key=lambda item: item[0], reverse=True)
        if scored:
            return [item[1] for item in scored[:top_k]]

        # Fallback: return first items when query is too broad.
        return self.exercises[:top_k]

    def search_exercises(self, user_message: str, top_k: int = 3) -> list[dict[str, Any]]:
        if self._semantic_ready:
            semantic_results = self._search_semantic(user_message, top_k)
            if semantic_results:
                return semantic_results
        return self._search_lexical(user_message, top_k)


__all__ = ["AIEngine"]

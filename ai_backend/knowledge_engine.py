from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from nlp_utils import normalize_text, tokenize
from utils_logger import log_error


HEADING_RE = re.compile(r"(?:اسم\s*الطعام|الطعاماسم)", re.IGNORECASE)
BULLET_CHARS = ("\u2022", "•", "")


class KnowledgeEngine:
    """Lightweight lexical retrieval over local nutrition knowledge text."""

    def __init__(
        self,
        data_path: str | Path,
        chunk_chars: int = 520,
        overlap_chars: int = 90,
    ) -> None:
        self.data_path = Path(data_path)
        self.chunk_chars = max(240, int(chunk_chars))
        self.overlap_chars = max(0, int(overlap_chars))
        self.ready = False
        self.source_name = self.data_path.name
        self._chunks: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            text = self.data_path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            self.ready = False
            self._chunks = []
            log_error(
                "KNOWLEDGE_ENGINE_LOAD_FAILED",
                None,
                exc,
                {"path": str(self.data_path)},
            )
            return

        if not text:
            self.ready = False
            self._chunks = []
            return

        self._chunks = self._build_chunks(text)
        self.ready = bool(self._chunks)

    @staticmethod
    def _clean_line(line: str) -> str:
        cleaned = line.strip()
        if not cleaned:
            return ""
        for bullet in BULLET_CHARS:
            cleaned = cleaned.replace(bullet, " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _split_sections(self, text: str) -> list[str]:
        lines = text.splitlines()
        sections: list[str] = []
        current: list[str] = []

        for raw_line in lines:
            line = self._clean_line(raw_line)
            if not line:
                continue

            if HEADING_RE.search(line) and current:
                sections.append(" ".join(current).strip())
                current = [line]
            else:
                current.append(line)

        if current:
            sections.append(" ".join(current).strip())

        return [section for section in sections if section]

    def _chunk_section(self, section_text: str) -> list[str]:
        section = re.sub(r"\s+", " ", section_text).strip()
        if not section:
            return []
        if len(section) <= self.chunk_chars:
            return [section]

        chunks: list[str] = []
        start = 0
        section_len = len(section)
        while start < section_len:
            end = min(section_len, start + self.chunk_chars)
            piece = section[start:end].strip()
            if piece:
                chunks.append(piece)
            if end >= section_len:
                break
            start = max(0, end - self.overlap_chars)
        return chunks

    def _build_chunks(self, text: str) -> list[dict[str, Any]]:
        sections = self._split_sections(text)
        if not sections:
            sections = [text]

        chunks: list[dict[str, Any]] = []
        for section in sections:
            for piece in self._chunk_section(section):
                piece_norm = normalize_text(piece)
                if not piece_norm:
                    continue
                chunks.append(
                    {
                        "text": piece,
                        "normalized": piece_norm,
                        "tokens": set(tokenize(piece)),
                    }
                )

        return chunks

    def search(self, query: str, top_k: int = 3, max_chars: int = 420) -> list[dict[str, Any]]:
        if not self.ready or not self._chunks:
            return []

        query_norm = normalize_text(query or "")
        if not query_norm:
            return []

        query_tokens = set(tokenize(query_norm))
        if not query_tokens:
            return []

        scored: list[tuple[int, dict[str, Any]]] = []
        for chunk in self._chunks:
            overlap = len(query_tokens.intersection(chunk["tokens"]))
            if overlap <= 0:
                continue
            phrase_bonus = 2 if query_norm in chunk["normalized"] else 0
            scored.append((overlap + phrase_bonus, chunk))

        if not scored:
            return []

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, chunk in scored[: max(1, top_k)]:
            text = chunk["text"]
            if len(text) > max_chars:
                text = f"{text[:max_chars].rstrip()}..."
            results.append(
                {
                    "score": score,
                    "text": text,
                    "source": self.source_name,
                }
            )
        return results


__all__ = ["KnowledgeEngine"]

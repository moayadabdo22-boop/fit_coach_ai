from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency at runtime
    SentenceTransformer = None


@dataclass
class RagDocument:
    doc_id: str
    text: str
    source: str
    metadata: dict


def _chunk_text(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]
    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + max_chars)
        chunk = cleaned[start:end]
        chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def _safe_read_json(path: Path) -> list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _build_workout_docs(path: Path) -> List[RagDocument]:
    rows = _safe_read_json(path)
    docs: List[RagDocument] = []
    for row in rows:
        program_name = row.get("program_name") or row.get("title") or "Workout Program"
        goal = row.get("goal") or ""
        level = row.get("level") or ""
        location = row.get("location") or ""
        description = row.get("description") or ""
        schedule = row.get("weekly_schedule") or []
        schedule_text = " | ".join(
            f"{d.get('day')}: {d.get('focus')}" for d in schedule if isinstance(d, dict)
        )
        text = (
            f"{program_name}\nGoal: {goal}\nLevel: {level}\nLocation: {location}\n"
            f"{description}\nSchedule: {schedule_text}"
        )
        docs.append(
            RagDocument(
                doc_id=row.get("id") or f"workout_{len(docs)}",
                text=text.strip(),
                source="workout_programs",
                metadata=row,
            )
        )
    return docs


def _build_nutrition_docs(path: Path) -> List[RagDocument]:
    rows = _safe_read_json(path)
    docs: List[RagDocument] = []
    for row in rows:
        program_name = row.get("plan_name") or row.get("title") or "Nutrition Plan"
        goal = row.get("goal") or ""
        calories = row.get("daily_calories") or row.get("calories") or ""
        meals_per_day = row.get("meals_per_day") or row.get("meals") or ""
        description = row.get("description") or ""
        text = (
            f"{program_name}\nGoal: {goal}\nCalories: {calories}\nMeals/Day: {meals_per_day}\n{description}"
        )
        docs.append(
            RagDocument(
                doc_id=row.get("id") or f"nutrition_{len(docs)}",
                text=text.strip(),
                source="nutrition_programs",
                metadata=row,
            )
        )
    return docs


def _build_kb_docs(path: Path) -> List[RagDocument]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    chunks = _chunk_text(text)
    docs = [
        RagDocument(
            doc_id=f"kb_{idx}",
            text=chunk,
            source="knowledge_base",
            metadata={"chunk_index": idx},
        )
        for idx, chunk in enumerate(chunks)
    ]
    return docs


class FaissRagIndex:
    def __init__(self, model_name: str, index_dir: Path) -> None:
        self.model_name = model_name
        self.index_dir = index_dir
        self.index: Optional["faiss.Index"] = None
        self.docs: List[RagDocument] = []
        self.model = SentenceTransformer(model_name) if SentenceTransformer else None

    @property
    def ready(self) -> bool:
        return self.index is not None and self.model is not None and len(self.docs) > 0

    def _index_path(self) -> Path:
        return self.index_dir / "rag.index"

    def _meta_path(self) -> Path:
        return self.index_dir / "rag.meta.json"

    def build(self, documents: Iterable[RagDocument]) -> None:
        if not faiss or not self.model:
            raise RuntimeError("FAISS or SentenceTransformer not available.")
        docs = [doc for doc in documents if doc.text]
        if not docs:
            self.index = None
            self.docs = []
            return
        embeddings = self.model.encode([d.text for d in docs], normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype="float32")
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        self.index = index
        self.docs = docs

        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self._index_path()))
        meta_payload = [
            {
                "doc_id": d.doc_id,
                "text": d.text,
                "source": d.source,
                "metadata": d.metadata,
            }
            for d in docs
        ]
        self._meta_path().write_text(json.dumps(meta_payload, ensure_ascii=False), encoding="utf-8")

    def load(self) -> bool:
        if not faiss or not self.model:
            return False
        index_path = self._index_path()
        meta_path = self._meta_path()
        if not index_path.exists() or not meta_path.exists():
            return False
        try:
            self.index = faiss.read_index(str(index_path))
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.docs = [
                RagDocument(
                    doc_id=item.get("doc_id"),
                    text=item.get("text", ""),
                    source=item.get("source", ""),
                    metadata=item.get("metadata", {}),
                )
                for item in meta
            ]
            return True
        except Exception:
            self.index = None
            self.docs = []
            return False

    def query(self, text: str, top_k: int = 4) -> List[dict]:
        if not self.ready or not text:
            return []
        emb = self.model.encode([text], normalize_embeddings=True)
        emb = np.array(emb, dtype="float32")
        scores, indices = self.index.search(emb, top_k)
        results: List[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.docs):
                continue
            doc = self.docs[idx]
            results.append(
                {
                    "score": float(score),
                    "doc_id": doc.doc_id,
                    "source": doc.source,
                    "text": doc.text,
                    "metadata": doc.metadata,
                }
            )
        return results


class RagService:
    def __init__(self, index: FaissRagIndex) -> None:
        self.index = index

    @classmethod
    def build_default(
        cls,
        dataset_dir: Path,
        knowledge_path: Optional[Path],
        index_dir: Path,
        model_name: Optional[str] = None,
        force_rebuild: bool = False,
    ) -> "RagService":
        model_name = model_name or os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        index = FaissRagIndex(model_name, index_dir)
        loaded = False if force_rebuild else index.load()
        if not loaded:
            workout_path = dataset_dir / "workout_programs.json"
            nutrition_path = dataset_dir / "nutrition_programs.json"
            docs: List[RagDocument] = []
            if workout_path.exists():
                docs.extend(_build_workout_docs(workout_path))
            if nutrition_path.exists():
                docs.extend(_build_nutrition_docs(nutrition_path))
            if knowledge_path:
                docs.extend(_build_kb_docs(knowledge_path))
            index.build(docs)
        return cls(index)

    def query(self, text: str, top_k: int = 4) -> List[dict]:
        return self.index.query(text, top_k=top_k)

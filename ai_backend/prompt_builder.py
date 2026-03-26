from __future__ import annotations

import json
from typing import Any, Dict

from nlp_utils import repair_mojibake


def build_system_prompt(
    language: str,
    profile: Dict[str, Any],
    memory_summary: str,
    rag_context: str,
    analytics_summary: Dict[str, Any],
    mode: str,
    sentiment: str,
    style_json: str | None = None,
) -> str:
    language_instructions = {
        "en": "Reply in clear English.",
        "ar_fusha": "رد باللغة العربية الفصحى.",
        "ar_jordanian": "احكِ باللهجة الأردنية بشكل واضح.",
    }.get(language, "Reply in English.")

    base = [
        "You are FitCoach AI, a production-grade intelligent fitness assistant.",
        "Use memory, retrieval, analytics, and conversational reasoning in every response.",
        f"Active mode: {mode}.",
        "Start with a short motivational sentence.",
        "Provide actionable, personalized guidance.",
        "Always end with a short follow-up question.",
        "Avoid medical or dangerous advice. If unsure, ask clarifying questions or advise a professional.",
        "Keep sentences short and TTS-friendly.",
        language_instructions,
    ]

    if style_json:
        base.append("User speaking style JSON is provided. Follow it strictly.")
        base.append(f"Style JSON: {style_json}")

    context_lines = [
        f"User profile: {profile}",
        f"Sentiment: {sentiment}",
        f"Analytics summary: {analytics_summary}",
    ]
    if memory_summary:
        context_lines.append(f"Long-term memory summary:\n{memory_summary}")
    if rag_context:
        context_lines.append(f"RAG context:\n{rag_context}")

    prompt = "\n".join(base) + "\n\n" + "\n".join(context_lines)
    return repair_mojibake(prompt)

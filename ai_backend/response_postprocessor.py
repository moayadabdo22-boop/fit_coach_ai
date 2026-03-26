from __future__ import annotations

from typing import Any

from nlp_utils import normalize_text, repair_mojibake


def _motivational_opening(language: str) -> str:
    return {
        "en": "Great effort!",
        "ar_fusha": "أحسنت!",
        "ar_jordanian": "شغل ممتاز!",
    }.get(language, "Great effort!")


def _followup_question(language: str) -> str:
    return {
        "en": "Want me to adjust anything?",
        "ar_fusha": "هل تريد أن أعدل شيئًا؟",
        "ar_jordanian": "بدك أعدّل إشي؟",
    }.get(language, "Want me to adjust anything?")


def _personalize_hint(profile: dict[str, Any], language: str) -> str:
    goal = profile.get("goal")
    if not goal:
        return ""
    if language.startswith("ar"):
        return f"هذا مناسب لهدفك: {goal}."
    return f"This matches your goal: {goal}."


def post_process_response(reply: str, language: str, profile: dict[str, Any]) -> str:
    text = repair_mojibake(reply or "").strip()
    if not text:
        return text

    # If this is an out-of-scope redirection, return as-is
    redirection_markers = [
        "دوري هنا يركّز على اللياقة",
        "دوري هنا يركز على اللياقة",
        "focused only on fitness",
        "specialized only in fitness",
    ]
    if any(marker in text for marker in redirection_markers):
        return text

    # Ensure motivational opening
    normalized = normalize_text(text)
    if not normalized.startswith(normalize_text(_motivational_opening(language)).split()[0]):
        text = f"{_motivational_opening(language)}\n{text}"

    # Ensure personalization
    personalization = _personalize_hint(profile, language)
    if personalization and normalize_text(personalization).split()[0] not in normalize_text(text):
        text = f"{text}\n{personalization}"

    # Ensure follow-up question
    if not text.strip().endswith("?") and not text.strip().endswith("؟"):
        text = f"{text}\n{_followup_question(language)}"
    return text

from __future__ import annotations

from typing import Any

from nlp_utils import normalize_text, repair_mojibake


GOAL_LABELS = {
    "muscle_gain": {
        "en": "muscle gain",
        "ar_fusha": "زيادة الكتلة العضلية",
        "ar_jordanian": "زيادة العضل",
    },
    "fat_loss": {
        "en": "fat loss",
        "ar_fusha": "خسارة الدهون",
        "ar_jordanian": "تنزيل الدهون",
    },
    "weight_loss": {
        "en": "fat loss",
        "ar_fusha": "خسارة الدهون",
        "ar_jordanian": "تنزيل الدهون",
    },
    "general_fitness": {
        "en": "general fitness",
        "ar_fusha": "اللياقة العامة",
        "ar_jordanian": "لياقة عامة",
    },
}


def _motivational_opening(language: str) -> str:
    return {
        "en": "Great effort!",
        "ar_fusha": "أحسنت!",
        "ar_jordanian": "شغل ممتاز!",
    }.get(language, "Great effort!")


def _followup_question(language: str) -> str:
    return {
        "en": "Want me to adjust anything?",
        "ar_fusha": "هل تريد أن أعدّل شيئًا؟",
        "ar_jordanian": "بدك أعدّل إشي؟",
    }.get(language, "Want me to adjust anything?")


def _goal_label(goal_value: str, language: str) -> str:
    goal_key = str(goal_value or "").strip().lower()
    if goal_key in GOAL_LABELS:
        return GOAL_LABELS[goal_key].get(language, GOAL_LABELS[goal_key]["en"])
    return goal_key


def _personalize_hint(profile: dict[str, Any], language: str) -> str:
    goal_label = _goal_label(str(profile.get("goal") or ""), language)
    if not goal_label:
        return ""
    if language.startswith("ar"):
        return f"هذا مناسب لهدفك: {goal_label}."
    return f"This matches your goal: {goal_label}."


def post_process_response(reply: str, language: str, profile: dict[str, Any]) -> str:
    text = repair_mojibake(reply or "").strip()
    if not text:
        return text

    # Keep in-domain redirection unchanged.
    redirection_markers = [
        "دوري هنا يركّز على اللياقة",
        "دوري هنا يركز على اللياقة",
        "focused only on fitness",
        "specialized only in fitness",
    ]
    if any(marker in text for marker in redirection_markers):
        return text

    normalized = normalize_text(text)
    opening_token = normalize_text(_motivational_opening(language)).split()[0]
    if opening_token and not normalized.startswith(opening_token):
        text = f"{_motivational_opening(language)}\n{text}"

    personalization = _personalize_hint(profile, language)
    if personalization and normalize_text(personalization) not in normalize_text(text):
        text = f"{text}\n{personalization}"

    if not text.strip().endswith("?") and not text.strip().endswith("؟"):
        text = f"{text}\n{_followup_question(language)}"

    # Remove accidental consecutive duplicate lines.
    deduped_lines: list[str] = []
    previous_norm = ""
    for line in text.splitlines():
        current = line.strip()
        if not current:
            continue
        current_norm = normalize_text(current)
        if current_norm and current_norm == previous_norm:
            continue
        deduped_lines.append(current)
        previous_norm = current_norm
    return "\n".join(deduped_lines).strip()

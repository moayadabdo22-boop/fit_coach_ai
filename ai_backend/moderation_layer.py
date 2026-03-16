from __future__ import annotations

import re
from typing import Callable

from nlp_utils import fuzzy_token_match, normalize_text, tokenize
from utils_logger import log_event


BAD_WORDS_EN = {
    "fuck",
    "fucker",
    "fucking",
    "shit",
    "bullshit",
    "bitch",
    "bastard",
    "asshole",
    "motherfucker",
    "retard",
    "idiot",
    "moron",
    "dumbass",
    "stupid",
    "crap",
    "son of a bitch",
}

BAD_WORDS_AR = {
    "زباله",
    "وسخ",
    "خرا",
    "كلب",
    "حمار",
    "تافه",
    "غبي",
    "سافل",
    "حقير",
    "قذر",
    "ملعون",
    "ابن كلب",
    "يلعن",
}

# Patterns run on compact normalized text (spaces removed).
BAD_PATTERNS = [
    re.compile(r"f\W*u\W*c\W*k", re.IGNORECASE),
    re.compile(r"s\W*h\W*i\W*t", re.IGNORECASE),
    re.compile(r"b\W*i\W*t\W*c\W*h", re.IGNORECASE),
]


class ModerationLayer:
    """Arabic + English profanity detection and masking."""

    def __init__(self):
        self.bad_words = {normalize_text(w) for w in (BAD_WORDS_EN | BAD_WORDS_AR)}

    def _contains_bad_word(self, text: str) -> bool:
        normalized = normalize_text(text)
        if not normalized:
            return False

        compact = re.sub(r"\s+", "", normalized)
        for pattern in BAD_PATTERNS:
            if pattern.search(compact):
                return True

        tokens = tokenize(normalized)
        if not tokens:
            return False

        for token in tokens:
            if token in self.bad_words:
                return True

        # Fuzzy match to catch small spelling variations.
        for token in tokens:
            for candidate in self.bad_words:
                if fuzzy_token_match(token, candidate):
                    return True

        # Phrase checks after normalization.
        for candidate in self.bad_words:
            if " " in candidate and candidate in normalized:
                return True

        return False

    def _mask_text(self, text: str) -> str:
        masked = text
        for bad in sorted((BAD_WORDS_EN | BAD_WORDS_AR), key=len, reverse=True):
            if not bad:
                continue
            pattern = re.compile(re.escape(bad), re.IGNORECASE)
            masked = pattern.sub(lambda m: "*" * len(m.group()), masked)
        for pattern in BAD_PATTERNS:
            masked = pattern.sub(lambda m: "*" * len(m.group()), masked)
        return masked

    def filter_content(self, text: str, language: str = "en") -> tuple[str, bool]:
        contains_toxicity = self._contains_bad_word(text)
        if contains_toxicity:
            log_event(
                "CONTENT_MODERATION",
                None,
                {"result": "contains_bad_words", "language": language, "text": text[:120]},
            )
            return self._mask_text(text), True
        return text, False

    def is_safe_response(self, text: str, user_language: str = "en") -> bool:
        _filtered, has_bad_words = self.filter_content(text, user_language)
        if has_bad_words:
            log_event("UNSAFE_RESPONSE", None, {"reason": "contains_bad_words", "text": text[:120]})
            return False
        return True

    def get_safe_fallback(self, language: str = "en") -> str:
        fallbacks = {
            "en": (
                "I can help you best when the conversation stays respectful. "
                "Let's focus on your workouts, nutrition, and progress."
            ),
            "ar_fusha": (
                "أستطيع مساعدتك بشكل أفضل عندما يكون الحوار محترمًا. "
                "دعنا نركز على التمارين والتغذية والتقدم."
            ),
            "ar_jordanian": (
                "بقدر أساعدك أحسن لما يكون الحوار محترم. "
                "خلينا نركز على التمارين والأكل والمتابعة."
            ),
        }
        return fallbacks.get(language, fallbacks["en"])


def add_moderation_to_pipeline(moderation: ModerationLayer) -> Callable:
    def apply_moderation(response: str, language: str = "en") -> str:
        filtered, _ = moderation.filter_content(response, language)
        return filtered

    return apply_moderation

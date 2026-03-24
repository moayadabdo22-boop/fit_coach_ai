from __future__ import annotations

import re
from typing import Optional

import numpy as np
from typing import Any

from nlp_utils import fuzzy_contains_any, normalize_text, repair_mojibake
from utils_logger import log_error, log_event


DOMAIN_TOPICS = [
    # English fitness and nutrition
    "fitness workout exercise training strength cardio mobility flexibility",
    "muscle building hypertrophy growth recovery sets reps progressive overload",
    "weight loss fat loss cutting calories body composition",
    "nutrition meal plan protein carbs fats hydration micronutrients",
    "injury prevention rehab warmup cooldown posture pain-safe training",
    "sports performance endurance stamina speed athletic training",
    # Arabic fitness and nutrition
    "Ø±ÙŠØ§Ø¶Ø© ØªÙ…Ø§Ø±ÙŠÙ† ØªØ¯Ø±ÙŠØ¨ Ù„ÙŠØ§Ù‚Ø© Ø¨Ø¯Ù†ÙŠØ© ÙƒØ§Ø±Ø¯ÙŠÙˆ Ù‚ÙˆØ© Ù…Ø±ÙˆÙ†Ø©",
    "Ø¨Ù†Ø§Ø¡ Ø¹Ø¶Ù„ ØªØ¶Ø®ÙŠÙ… ØªÙ…Ø§Ø±ÙŠÙ† Ù…Ù‚Ø§ÙˆÙ…Ø© ØªÙƒØ±Ø§Ø±Ø§Øª Ù…Ø¬Ù…ÙˆØ¹Ø§Øª",
    "Ø®Ø³Ø§Ø±Ø© ÙˆØ²Ù† ØªÙ†Ø´ÙŠÙ Ø­Ø±Ù‚ Ø¯Ù‡ÙˆÙ† Ø³Ø¹Ø±Ø§Øª",
    "ØªØºØ°ÙŠØ© ÙˆØ¬Ø¨Ø§Øª Ø¨Ø±ÙˆØªÙŠÙ† ÙƒØ±Ø¨ÙˆÙ‡ÙŠØ¯Ø±Ø§Øª Ø¯Ù‡ÙˆÙ† Ø³Ø¹Ø±Ø§Øª",
    "ÙˆÙ‚Ø§ÙŠØ© Ø§ØµØ§Ø¨Ø§Øª Ø§Ø­Ù…Ø§Ø¡ ØªØ¨Ø±ÙŠØ¯ Ø§Ø³ØªØ´ÙØ§Ø¡ ØªØ£Ù‡ÙŠÙ„",
]

DOMAIN_KEYWORDS = {
    "en": {
        "fitness",
        "workout",
        "exercise",
        "training",
        "gym",
        "squat",
        "deadlift",
        "bench",
        "bench press",
        "pull up",
        "push up",
        "stretch",
        "warmup",
        "cooldown",
        "cardio",
        "strength",
        "hypertrophy",
        "muscle",
        "fat loss",
        "weight loss",
        "cutting",
        "bulking",
        "meal plan",
        "nutrition",
        "calories",
        "protein",
        "carbs",
        "fats",
        "reps",
        "sets",
        "recovery",
        "injury",
        "mobility",
        "endurance",
        "supplement",
    },
    "ar": {
        "Ø±ÙŠØ§Ø¶Ø©",
        "ØªÙ…Ø±ÙŠÙ†",
        "ØªÙ…Ø§Ø±ÙŠÙ†",
        "Ø§ØªÙ…Ø±Ù†",
        "ØªØ¯Ø±ÙŠØ¨",
        "Ù„ÙŠØ§Ù‚Ø©",
        "Ø¹Ø¶Ù„",
        "Ø¹Ø¶Ù„Ø§Øª",
        "ØµØ¯Ø±",
        "Ø¸Ù‡Ø±",
        "Ø§ÙƒØªØ§Ù",
        "ÙƒØªÙ",
        "Ø°Ø±Ø§Ø¹",
        "Ø¨Ø§ÙŠ",
        "ØªØ±Ø§ÙŠ",
        "Ø§Ø±Ø¬Ù„",
        "Ø³Ø§Ù‚",
        "Ø¨Ø·Ù†",
        "ÙƒØ§Ø±Ø¯ÙŠÙˆ",
        "ØªÙ†Ø´ÙŠÙ",
        "ØªØ¶Ø®ÙŠÙ…",
        "Ø®Ø³Ø§Ø±Ø© ÙˆØ²Ù†",
        "Ø­Ø±Ù‚ Ø¯Ù‡ÙˆÙ†",
        "Ø¨Ø±ÙˆØªÙŠÙ†",
        "Ø³Ø¹Ø±Ø§Øª",
        "ÙˆØ¬Ø¨Ø§Øª",
        "ØªØºØ°ÙŠØ©",
        "Ø§ÙƒÙ„ ØµØ­ÙŠ",
        "Ø­Ù…ÙŠØ©",
        "Ø¯Ø§ÙŠØª",
        "Ù…ÙƒÙ…Ù„Ø§Øª",
        "Ø§ØµØ§Ø¨Ø©",
        "Ø§Ø³ØªØ´ÙØ§Ø¡",
        "Ù…Ø±ÙˆÙ†Ø©",
        "ØªØ­Ù…Ù„",
        "Ù†ÙˆÙ…",
        "Ù…Ø§Ø¡",
        "Ø³ÙƒØ±",
        "Ø³ÙƒØ±ÙŠ",
    },
}

OFF_DOMAIN_KEYWORDS = {
    "en": {
        "politics",
        "election",
        "president",
        "religion",
        "finance",
        "investment",
        "stock",
        "crypto",
        "movie",
        "celebrity",
        "news",
        "weather",
        "programming",
        "coding",
        "javascript",
        "python code",
        "travel",
        "dating",
        "relationship",
        "bookstore",
        "sell books",
    },
    "ar": {
        "Ø³ÙŠØ§Ø³Ø©",
        "Ø§Ù†ØªØ®Ø§Ø¨Ø§Øª",
        "Ø±Ø¦ÙŠØ³ Ø¯ÙˆÙ„Ø©",
        "Ø¯ÙŠÙ†",
        "Ø§Ø³ØªØ«Ù…Ø§Ø±",
        "Ø§Ø³Ù‡Ù…",
        "Ø¹Ù…Ù„Ø§Øª Ø±Ù‚Ù…ÙŠØ©",
        "ÙÙŠÙ„Ù…",
        "Ù…Ø´Ø§Ù‡ÙŠØ±",
        "Ø§Ø®Ø¨Ø§Ø± Ø³ÙŠØ§Ø³ÙŠØ©",
        "Ø·Ù‚Ø³",
        "Ø¨Ø±Ù…Ø¬Ø©",
        "Ø¨Ø§ÙŠØ«ÙˆÙ†",
        "ÙƒÙˆØ¯",
        "Ø³ÙØ±",
        "Ø¹Ù„Ø§Ù‚Ø©",
        "Ø²ÙˆØ§Ø¬",
        "Ø¨ÙŠØ¹ ÙƒØªØ¨",
        "Ù…ÙƒØªØ¨Ø©",
    },
}

OFF_DOMAIN_PATTERNS = {
    "en": (
        re.compile(r"\bcapital of\b", re.IGNORECASE),
        re.compile(r"\bwho is the president\b", re.IGNORECASE),
    ),
    "ar": (
        re.compile(r"Ù…Ø§\s+Ø¹Ø§ØµÙ…Ø©"),
        re.compile(r"(Ù…ÙŠÙ†|Ù…Ù†)\s+Ù‡Ùˆ\s+Ø§Ù„Ø±Ø¦ÙŠØ³"),
    ),
}

OFF_DOMAIN_BOOK_KEYWORDS = {
    "en": {"book", "books", "sell books", "buy books", "bookstore"},
    "ar": {
        "ÙƒØªØ§Ø¨",
        "ÙƒØªØ¨",
        "Ù…ÙƒØªØ¨Ù‡",
        "Ù…ÙƒØªØ¨Ø©",
        "ØªØ¨ÙŠØ¹ ÙƒØªØ¨",
        "Ø¨ÙŠØ¹ ÙƒØªØ¨",
        "ØªØ´ØªØ±ÙŠ ÙƒØªØ¨",
    },
}

OFF_DOMAIN_PROGRAMMING_KEYWORDS = {
    "en": {"python", "programming", "coding", "javascript", "java", "c++", "typescript", "debug"},
    "ar": {
        "Ø¨Ø§ÙŠØ«ÙˆÙ†",
        "Ø¨Ø±Ù…Ø¬Ù‡",
        "Ø¨Ø±Ù…Ø¬Ø©",
        "ÙƒÙˆØ¯",
        "Ø¬Ø§ÙØ§Ø³ÙƒØ±Ø¨Øª",
        "ØªØµØ­ÙŠØ­",
        "Ø¯ÙŠØ¨Ø§Øº",
    },
}


class DomainRouter:
    """Fitness-only domain guard with lexical + semantic routing."""

    def __init__(self, threshold: float = 0.42, enable_semantic: bool = False):
        self.threshold = threshold
        self.model: Optional[Any] = None
        self.domain_embeddings: Optional[np.ndarray] = None
        self.enable_semantic = enable_semantic

        if self.enable_semantic:
            try:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.domain_embeddings = self.model.encode(
                    DOMAIN_TOPICS,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
            except Exception as exc:
                self.model = None
                self.domain_embeddings = None
                log_error("DOMAIN_ROUTER_INIT_FAILED", None, exc, {"fallback": "lexical_only"})

    @staticmethod
    def _lang_bucket(language: str) -> str:
        return "ar" if str(language).startswith("ar") else "en"

    @staticmethod
    def _contains_any(query_text: str, keywords: set[str]) -> bool:
        return fuzzy_contains_any(query_text, keywords)

    def is_in_domain(self, query: str, language: str = "en") -> tuple[bool, float]:
        """Return (in_domain, confidence_score)."""
        lang_key = self._lang_bucket(language)
        query_lower = normalize_text(repair_mojibake(query or ""))

        has_domain_keyword = self._contains_any(query_lower, DOMAIN_KEYWORDS[lang_key])
        has_off_keyword = self._contains_any(query_lower, OFF_DOMAIN_KEYWORDS[lang_key])
        has_off_pattern = any(pattern.search(query_lower) for pattern in OFF_DOMAIN_PATTERNS[lang_key])

        if has_off_pattern or (has_off_keyword and not has_domain_keyword):
            log_event(
                "DOMAIN_CHECK",
                None,
                {
                    "query": query[:120],
                    "language": language,
                    "result": "off_domain_lexical",
                },
            )
            return False, 0.0

        if has_domain_keyword and not has_off_keyword:
            log_event(
                "DOMAIN_CHECK",
                None,
                {
                    "query": query[:120],
                    "language": language,
                    "result": "in_domain_lexical",
                },
            )
            return True, 1.0

        if self.model is None or self.domain_embeddings is None:
            log_event(
                "DOMAIN_CHECK",
                None,
                {
                    "query": query[:120],
                    "language": language,
                    "result": "off_domain_no_semantic",
                },
            )
            return False, 0.0

        query_vec = self.model.encode(
            [query_lower],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        scores = np.dot(self.domain_embeddings, query_vec)
        max_score = float(np.max(scores))

        threshold = 0.60 if (has_domain_keyword and has_off_keyword) else self.threshold
        in_domain = max_score >= threshold

        log_event(
            "DOMAIN_CHECK",
            None,
            {
                "query": query[:120],
                "language": language,
                "score": max_score,
                "threshold": threshold,
                "result": "in_domain" if in_domain else "off_domain",
            },
        )
        return in_domain, max_score

    def get_out_of_domain_response(self, language: str = "en", query: str = "") -> str:
        lang_key = self._lang_bucket(language)
        normalized_query = normalize_text(repair_mojibake(query or ""))

        alt_lang_key = "ar" if lang_key == "en" else "en"
        is_books = self._contains_any(normalized_query, OFF_DOMAIN_BOOK_KEYWORDS[lang_key]) or self._contains_any(
            normalized_query, OFF_DOMAIN_BOOK_KEYWORDS[alt_lang_key]
        )
        is_programming = self._contains_any(
            normalized_query, OFF_DOMAIN_PROGRAMMING_KEYWORDS[lang_key]
        ) or self._contains_any(normalized_query, OFF_DOMAIN_PROGRAMMING_KEYWORDS[alt_lang_key])

        detected_keyword = ""
        candidate_keywords = (
            set(OFF_DOMAIN_PROGRAMMING_KEYWORDS[lang_key])
            | set(OFF_DOMAIN_BOOK_KEYWORDS[lang_key])
            | set(OFF_DOMAIN_KEYWORDS[lang_key])
            | set(OFF_DOMAIN_PROGRAMMING_KEYWORDS[alt_lang_key])
            | set(OFF_DOMAIN_BOOK_KEYWORDS[alt_lang_key])
            | set(OFF_DOMAIN_KEYWORDS[alt_lang_key])
        )
        for keyword in sorted(candidate_keywords, key=len, reverse=True):
            keyword_norm = normalize_text(repair_mojibake(keyword))
            if keyword_norm and keyword_norm in normalized_query:
                detected_keyword = repair_mojibake(keyword)
                break

        if language == "en":
            if is_books:
                keyword_text = f"'{detected_keyword}' " if detected_keyword else ""
                return repair_mojibake(
                    f"{keyword_text}is outside my specialization. "
                    "I do not sell books. "
                    "I am an AI coach specialized only in fitness, training, and nutrition."
                )
            if is_programming:
                keyword_text = f"'{detected_keyword}' " if detected_keyword else ""
                return repair_mojibake(
                    f"{keyword_text}is outside my specialization (programming). "
                    "Please ask a programming-focused chatbot. "
                    "I specialize in fitness, training, and nutrition."
                )
            if detected_keyword:
                return repair_mojibake(
                    f"'{detected_keyword}' is outside my specialization. "
                    "I focus only on fitness, training, and nutrition."
                )
            return repair_mojibake(
                "This is outside my specialization. "
                "I focus only on fitness, training, and nutrition."
            )

        if language == "ar_fusha":
            if is_books:
                keyword_text = f"'{detected_keyword}' " if detected_keyword else ""
                return repair_mojibake(
                    f"{keyword_text}خارج نطاق تخصصي. "
                    "أنا لا أبيع الكتب. "
                    "أنا مدرب ذكاء اصطناعي متخصص فقط في اللياقة والتدريب والتغذية."
                )
            if is_programming:
                keyword_text = f"'{detected_keyword}' " if detected_keyword else ""
                return repair_mojibake(
                    f"{keyword_text}خارج نطاق تخصصي (برمجة). "
                    "اسأل روبوتاً متخصصاً بالبرمجة، "
                    "وأنا متخصص في اللياقة والتدريب والتغذية."
                )
            if detected_keyword:
                return repair_mojibake(
                    f"'{detected_keyword}' خارج نطاق تخصصي. "
                    "أنا أركز فقط على اللياقة والتدريب والتغذية."
                )
            return repair_mojibake("هذا خارج نطاق تخصصي. أنا أركز فقط على اللياقة والتدريب والتغذية.")

        if is_books:
            keyword_text = f"'{detected_keyword}' " if detected_keyword else ""
            return repair_mojibake(
                f"{keyword_text}برا تخصصي. "
                "أنا ما ببيع كتب. "
                "أنا كوتش ذكاء اصطناعي متخصص بس بالتمارين والتغذية."
            )
        if is_programming:
            keyword_text = f"'{detected_keyword}' " if detected_keyword else ""
            return repair_mojibake(
                f"{keyword_text}برا تخصصي (برمجة). "
                "اسأل بوت برمجة، وأنا تخصصي اللياقة والتدريب والتغذية."
            )
        if detected_keyword:
            return repair_mojibake(
                f"'{detected_keyword}' برا تخصصي. "
                "أنا بساعدك بس باللياقة والتدريب والتغذية."
            )
        return repair_mojibake("هاد خارج تخصصي. أنا بساعدك بس باللياقة والتدريب والتغذية.")

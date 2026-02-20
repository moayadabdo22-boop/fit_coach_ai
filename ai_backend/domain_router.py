from __future__ import annotations

import re
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

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
    "رياضة تمارين تدريب لياقة بدنية كارديو قوة مرونة",
    "بناء عضل تضخيم تمارين مقاومة تكرارات مجموعات",
    "خسارة وزن تنشيف حرق دهون سعرات",
    "تغذية وجبات بروتين كربوهيدرات دهون سعرات",
    "وقاية اصابات احماء تبريد استشفاء تأهيل",
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
        "رياضة",
        "تمرين",
        "تمارين",
        "اتمرن",
        "تدريب",
        "لياقة",
        "عضل",
        "عضلات",
        "صدر",
        "ظهر",
        "اكتاف",
        "كتف",
        "ذراع",
        "باي",
        "تراي",
        "ارجل",
        "ساق",
        "بطن",
        "كارديو",
        "تنشيف",
        "تضخيم",
        "خسارة وزن",
        "حرق دهون",
        "بروتين",
        "سعرات",
        "وجبات",
        "تغذية",
        "اكل صحي",
        "حمية",
        "دايت",
        "مكملات",
        "اصابة",
        "استشفاء",
        "مرونة",
        "تحمل",
        "نوم",
        "ماء",
        "سكر",
        "سكري",
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
        "سياسة",
        "انتخابات",
        "رئيس دولة",
        "دين",
        "استثمار",
        "اسهم",
        "عملات رقمية",
        "فيلم",
        "مشاهير",
        "اخبار سياسية",
        "طقس",
        "برمجة",
        "بايثون",
        "كود",
        "سفر",
        "علاقة",
        "زواج",
        "بيع كتب",
        "مكتبة",
    },
}

OFF_DOMAIN_PATTERNS = {
    "en": (
        re.compile(r"\bcapital of\b", re.IGNORECASE),
        re.compile(r"\bwho is the president\b", re.IGNORECASE),
    ),
    "ar": (
        re.compile(r"ما\s+عاصمة"),
        re.compile(r"(مين|من)\s+هو\s+الرئيس"),
    ),
}

OFF_DOMAIN_BOOK_KEYWORDS = {
    "en": {"book", "books", "sell books", "buy books", "bookstore"},
    "ar": {
        "كتاب",
        "كتب",
        "مكتبه",
        "مكتبة",
        "تبيع كتب",
        "بيع كتب",
        "تشتري كتب",
    },
}

OFF_DOMAIN_PROGRAMMING_KEYWORDS = {
    "en": {"python", "programming", "coding", "javascript", "java", "c++", "typescript", "debug"},
    "ar": {
        "بايثون",
        "برمجه",
        "برمجة",
        "كود",
        "جافاسكربت",
        "تصحيح",
        "ديباغ",
    },
}


class DomainRouter:
    """Fitness-only domain guard with lexical + semantic routing."""

    def __init__(self, threshold: float = 0.42, enable_semantic: bool = False):
        self.threshold = threshold
        self.model: Optional[SentenceTransformer] = None
        self.domain_embeddings: Optional[np.ndarray] = None
        self.enable_semantic = enable_semantic

        if self.enable_semantic:
            try:
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

        is_books = self._contains_any(normalized_query, OFF_DOMAIN_BOOK_KEYWORDS[lang_key])
        is_programming = self._contains_any(normalized_query, OFF_DOMAIN_PROGRAMMING_KEYWORDS[lang_key])

        if language == "en":
            if is_books:
                return (
                    "No, I do not sell books. "
                    "I am an AI coach specialized only in fitness, training, and nutrition."
                )
            if is_programming:
                return (
                    "Programming (including Python) is outside my specialization. "
                    "Please ask a programming-focused chatbot. "
                    "I specialize in fitness, training, and nutrition."
                )
            return (
                "This is outside my specialization. "
                "I focus only on fitness, training, and nutrition."
            )

        if language == "ar_fusha":
            if is_books:
                return (
                    "لا، أنا لا أبيع الكتب. "
                    "أنا مدرب ذكاء اصطناعي متخصص فقط في اللياقة والتدريب والتغذية."
                )
            if is_programming:
                return (
                    "البرمجة أو بايثون ليست ضمن تخصصي. "
                    "اسأل روبوتًا متخصصًا بالبرمجة، "
                    "أما أنا فمتخصص في اللياقة والتدريب والتغذية."
                )
            return "هذا خارج نطاق تخصصي. أنا أركز فقط على اللياقة والتدريب والتغذية."

        if is_books:
            return "لا، أنا ما ببيع كتب. أنا كوتش ذكاء اصطناعي متخصص بس بالتمارين والتغذية."
        if is_programming:
            return "البايثون والبرمجة مش تخصصي. اسأل بوت برمجة، وأنا تخصصي اللياقة والتدريب والتغذية."
        return "هاد خارج تخصصي. أنا بساعدك بس باللياقة والتدريب والتغذية."

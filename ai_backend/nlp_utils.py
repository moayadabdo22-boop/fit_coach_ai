from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from nltk.metrics.distance import edit_distance


ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")
NON_WORD_RE = re.compile(r"[^a-z0-9\u0600-\u06FF\s]+")
WHITESPACE_RE = re.compile(r"\s+")
REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")
MOJIBAKE_MARKERS = ("Ø", "Ù", "Ã", "Â", "Ð", "â", "ï»¿")

LEET_MAP = str.maketrans(
    {
        "@": "a",
        "$": "s",
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "!": "i",
    }
)


def repair_mojibake(text: str) -> str:
    """Repair common UTF-8/latin-1 (or cp1252) mojibake sequences."""
    if not text:
        return ""

    candidate = str(text)
    if not any(marker in candidate for marker in MOJIBAKE_MARKERS):
        return candidate

    def _score(value: str) -> int:
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", value))
        marker_chars = sum(value.count(marker) for marker in MOJIBAKE_MARKERS)
        replacement_chars = value.count("\ufffd")
        return (arabic_chars * 3) - (marker_chars * 2) - (replacement_chars * 2)

    for _ in range(2):
        if not any(marker in candidate for marker in MOJIBAKE_MARKERS):
            break

        current_score = _score(candidate)
        best_candidate = candidate
        best_score = current_score

        for source_encoding in ("latin-1", "cp1252"):
            for encode_errors in ("strict", "replace"):
                for utf8_errors in ("strict", "replace"):
                    try:
                        trial = candidate.encode(source_encoding, errors=encode_errors).decode("utf-8", errors=utf8_errors)
                    except Exception:
                        continue
                    trial_score = _score(trial)
                    if trial_score > best_score:
                        best_candidate = trial
                        best_score = trial_score

        if best_candidate == candidate:
            break
        candidate = best_candidate

    return candidate


def repair_mojibake_deep(value: Any) -> Any:
    """Recursively repair mojibake text inside nested payloads."""
    if isinstance(value, str):
        return repair_mojibake(value)
    if isinstance(value, list):
        return [repair_mojibake_deep(v) for v in value]
    if isinstance(value, tuple):
        return tuple(repair_mojibake_deep(v) for v in value)
    if isinstance(value, dict):
        return {k: repair_mojibake_deep(v) for k, v in value.items()}
    return value


def normalize_text(text: str) -> str:
    if not text:
        return ""

    t = repair_mojibake(text).lower().translate(LEET_MAP)
    t = ARABIC_DIACRITICS_RE.sub("", t)
    t = t.replace("\u0640", "")  # tatweel

    # Normalize Arabic letter variants.
    t = (
        t.replace("\u0623", "\u0627")
        .replace("\u0625", "\u0627")
        .replace("\u0622", "\u0627")
        .replace("\u0649", "\u064a")
        .replace("\u0624", "\u0648")
        .replace("\u0626", "\u064a")
        .replace("\u0629", "\u0647")
    )

    t = REPEATED_CHAR_RE.sub(r"\1\1", t)
    t = NON_WORD_RE.sub(" ", t)
    t = WHITESPACE_RE.sub(" ", t).strip()
    return t


@lru_cache(maxsize=4096)
def _tokenize_cached(normalized_text: str) -> tuple[str, ...]:
    if not normalized_text:
        return ()
    return tuple(re.findall(r"[a-z0-9\u0600-\u06FF]+", normalized_text))


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return list(_tokenize_cached(normalized))


def _allowed_distance(token_len: int) -> int:
    if token_len <= 3:
        return 0
    if token_len <= 6:
        return 1
    if token_len <= 10:
        return 2
    return 3


def fuzzy_token_match(token: str, candidate: str) -> bool:
    if not token or not candidate:
        return False
    if token == candidate:
        return True

    max_dist = _allowed_distance(len(candidate))
    # Speed gate to avoid expensive edit distance on very different lengths.
    if abs(len(token) - len(candidate)) > max_dist:
        return False
    return edit_distance(token, candidate) <= max_dist


def fuzzy_contains_any(text: str, keywords: set[str]) -> bool:
    if not keywords:
        return False

    normalized_text = normalize_text(text)
    if not normalized_text:
        return False

    # Fast exact phrase check first.
    for keyword in keywords:
        keyword_norm = normalize_text(keyword)
        if keyword_norm and keyword_norm in normalized_text:
            return True

    text_tokens = set(_tokenize_cached(normalized_text))
    if not text_tokens:
        return False

    # Fuzzy token matching for misspellings (single-token keywords).
    token_keywords = [normalize_text(k) for k in keywords if " " not in normalize_text(k)]
    for tk in text_tokens:
        for kw in token_keywords:
            if kw and fuzzy_token_match(tk, kw):
                return True

    # Fuzzy phrase matching: all phrase tokens should be approximately present.
    phrase_keywords = [normalize_text(k) for k in keywords if " " in normalize_text(k)]
    for phrase in phrase_keywords:
        phrase_tokens = [pt for pt in phrase.split(" ") if pt]
        if not phrase_tokens:
            continue
        matched_all = True
        for phrase_token in phrase_tokens:
            if not any(fuzzy_token_match(tk, phrase_token) for tk in text_tokens):
                matched_all = False
                break
        if matched_all:
            return True
    return False


def extract_first_int(text: str) -> int | None:
    match = re.search(r"\d+", text or "")
    if not match:
        return None
    try:
        return int(match.group())
    except ValueError:
        return None

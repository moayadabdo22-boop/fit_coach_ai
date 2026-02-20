from __future__ import annotations

import re
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from ai_engine import AIEngine
from domain_router import DomainRouter
from knowledge_engine import KnowledgeEngine
from llm_client import LLMClient
from memory_system import MemorySystem
from moderation_layer import ModerationLayer
from nlp_utils import (
    extract_first_int,
    fuzzy_contains_any,
    normalize_text,
    repair_mojibake as nlp_repair_mojibake,
    repair_mojibake_deep,
)


app = FastAPI(title="AI Fitness Coach Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    language: Optional[str] = "en"
    stream: Optional[bool] = False
    user_profile: Optional[Dict[str, Any]] = None
    tracking_summary: Optional[Dict[str, Any]] = None
    recent_messages: Optional[list[Dict[str, Any]]] = None
    plan_snapshot: Optional[Dict[str, Any]] = None


def _repair_mojibake(text: str) -> str:
    return nlp_repair_mojibake(text)


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    language: str
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    @field_validator("reply", mode="before")
    @classmethod
    def _normalize_reply_text(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        return _repair_mojibake(value)

    @field_validator("data", mode="before")
    @classmethod
    def _normalize_data_payload(cls, value: Any) -> Any:
        return repair_mojibake_deep(value)


class PlanActionRequest(BaseModel):
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


ROUTER = DomainRouter(threshold=0.42, enable_semantic=False)
MODERATION = ModerationLayer()
LLM = LLMClient()
AI_ENGINE = AIEngine(Path(__file__).resolve().parent / "exercises.json")
NUTRITION_KB = KnowledgeEngine(Path(__file__).resolve().parent / "knowledge" / "dataforproject.txt")

MEMORY_SESSIONS: Dict[str, MemorySystem] = {}
PENDING_PLANS: Dict[str, Dict[str, Any]] = {}
USER_STATE: Dict[str, Dict[str, Any]] = {}

WEEK_DAYS = [
    ("Saturday", "السبت"),
    ("Sunday", "الأحد"),
    ("Monday", "الاثنين"),
    ("Tuesday", "الثلاثاء"),
    ("Wednesday", "الأربعاء"),
    ("Thursday", "الخميس"),
    ("Friday", "الجمعة"),
]

GREETING_KEYWORDS = {
    "hi",
    "hello",
    "hey",
    "Ù…Ø±Ø­Ø¨Ø§",
    "Ø§Ù‡Ù„Ø§",
    "Ù‡Ù„Ø§",
    "Ø§Ù„Ø³Ù„Ø§Ù… Ø¹Ù„ÙŠÙƒÙ…",
}

NAME_KEYWORDS = {"name", "Ø§Ø³Ù…Ùƒ", "Ø´Ùˆ Ø§Ø³Ù…Ùƒ", "Ù…ÙŠÙ† Ø§Ù†Øª"}
HOW_ARE_YOU_KEYWORDS = {"how are you", "ÙƒÙŠÙÙƒ", "Ø´Ù„ÙˆÙ†Ùƒ", "ÙƒÙŠÙ Ø­Ø§Ù„Ùƒ"}
WORKOUT_PLAN_KEYWORDS = {
    "workout plan",
    "training plan",
    "program",
    "Ø®Ø·Ø© ØªÙ…Ø§Ø±ÙŠÙ†",
    "Ø¨Ø±Ù†Ø§Ù…Ø¬ ØªÙ…Ø§Ø±ÙŠÙ†",
    "Ø¬Ø¯ÙˆÙ„ ØªÙ…Ø§Ø±ÙŠÙ†",
}
NUTRITION_PLAN_KEYWORDS = {
    "nutrition plan",
    "meal plan",
    "diet plan",
    "Ø®Ø·Ø© ØºØ°Ø§Ø¦ÙŠØ©",
    "Ø®Ø·Ø© ØªØºØ°ÙŠØ©",
    "Ø¬Ø¯ÙˆÙ„ ÙˆØ¬Ø¨Ø§Øª",
}
NUTRITION_KB_KEYWORDS = {
    "nutrition",
    "diet",
    "meal",
    "food",
    "foods",
    "ingredient",
    "calories",
    "protein",
    "carbs",
    "fat",
    "allergy",
    "allergies",
    "diabetes",
    "blood pressure",
    "cholesterol",
    "heart disease",
    "تغذية",
    "غذاء",
    "اكل",
    "وجبة",
    "وجبات",
    "سعرات",
    "بروتين",
    "كارب",
    "دهون",
    "حساسية",
    "سكري",
    "ضغط",
    "كوليسترول",
    "قلب",
    "خطة غذائية",
    "دايت",
}
PROGRESS_KEYWORDS = {"progress", "tracking", "adherence", "Ø§Ù„Ø§Ù„ØªØ²Ø§Ù…", "Ø§Ù„ØªÙ‚Ø¯Ù…", "Ø§Ù†Ø¬Ø§Ø²"}
APPROVE_KEYWORDS = {"approve", "yes", "ÙˆØ§ÙÙ‚", "Ø§Ø¹ØªÙ…Ø¯", "Ù…ÙˆØ§ÙÙ‚"}
REJECT_KEYWORDS = {"reject", "no", "Ø±ÙØ¶", "Ù„Ø§", "ØºÙŠØ± Ø§Ù„Ø®Ø·Ø©", "Ø¨Ø¯Ù„ Ø§Ù„Ø®Ø·Ø©"}
JORDANIAN_HINTS = {"Ø´Ùˆ", "Ø¨Ø¯Ùƒ", "Ù‡Ù„Ø§", "Ù„Ø³Ø§", "Ù…Ø´", "ÙƒØªÙŠØ±", "Ù…Ù†ÙŠØ­", "ØªÙ…Ø§Ù…"}


PLAN_CHOICE_KEYWORDS = {
    "choose",
    "option",
    "pick",
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "Ø§Ø®ØªØ§Ø±",
    "Ø®ÙŠØ§Ø±",
    "Ø§ÙˆÙ„",
    "Ø«Ø§Ù†ÙŠ",
    "Ø«Ø§Ù„Ø«",
    "Ø±Ø§Ø¨Ø¹",
    "Ø®Ø§Ù…Ø³",
}
PLAN_REFRESH_KEYWORDS = {"more options", "another options", "Ø®ÙŠØ§Ø±Ø§Øª Ø§ÙƒØ«Ø±", "Ø®ÙŠØ§Ø±Ø§Øª Ø£Ø®Ø±Ù‰", "ØºÙŠØ±Ù‡Ù…"}
APPROVE_KEYWORDS = APPROVE_KEYWORDS | {"accept", "okay", "ok", "Ù…Ø§Ø´ÙŠ"}
REJECT_KEYWORDS = REJECT_KEYWORDS | {"decline", "cancel"}
WORKOUT_PLAN_KEYWORDS = WORKOUT_PLAN_KEYWORDS | {"workout", "training", "routine", "ØªÙ…Ø§Ø±ÙŠÙ†", "Ø¨Ø±Ù†Ø§Ù…Ø¬"}
NUTRITION_PLAN_KEYWORDS = NUTRITION_PLAN_KEYWORDS | {"nutrition", "diet", "meal", "ØªØºØ°ÙŠØ©", "ÙˆØ¬Ø¨Ø§Øª"}


THANKS_KEYWORDS = {
    "thanks",
    "thank you",
    "thx",
    "good job",
    "nice",
    "awesome",
    "great",
    "well done",
    "\u0634\u0643\u0631\u0627",
    "\u064a\u0633\u0644\u0645\u0648",
    "\u064a\u0639\u0637\u064a\u0643 \u0627\u0644\u0639\u0627\u0641\u064a\u0629",
    "\u0627\u062d\u0633\u0646\u062a",
    "\u0623\u062d\u0633\u0646\u062a",
}
WHO_AM_I_KEYWORDS = {
    "who am i",
    "tell me about me",
    "my info",
    "my profile",
    "\u0645\u064a\u0646 \u0627\u0646\u0627",
    "\u0645\u064a\u0646 \u0623\u0646\u0627",
    "\u0639\u0631\u0641\u0646\u064a",
    "\u0645\u0639\u0644\u0648\u0645\u0627\u062a\u064a",
    "\u0645\u0644\u0641\u064a",
}
ASK_MY_AGE_KEYWORDS = {"my age", "how old am i", "\u0643\u0645 \u0639\u0645\u0631\u064a", "\u0639\u0645\u0631\u064a"}
ASK_MY_HEIGHT_KEYWORDS = {"my height", "how tall am i", "\u0637\u0648\u0644\u064a", "\u0643\u0645 \u0637\u0648\u0644\u064a"}
ASK_MY_WEIGHT_KEYWORDS = {"my weight", "how much do i weigh", "\u0648\u0632\u0646\u064a", "\u0643\u0645 \u0648\u0632\u0646\u064a"}
ASK_MY_GOAL_KEYWORDS = {"my goal", "what is my goal", "\u0647\u062f\u0641\u064a", "\u0634\u0648 \u0647\u062f\u0641\u064a", "\u0645\u0627 \u0647\u062f\u0641\u064a"}

PROGRESS_CONCERN_KEYWORDS = {
    "no progress",
    "no change",
    "not improving",
    "plateau",
    "stuck",
    "\u0645\u0627 \u0641\u064a \u0641\u0631\u0642",
    "\u0645\u0641\u064a\u0634 \u0641\u0631\u0642",
    "\u0645\u0627 \u062a\u063a\u064a\u0631 \u062c\u0633\u0645\u064a",
    "\u062c\u0633\u0645\u064a \u0645\u0627 \u062a\u063a\u064a\u0631",
    "\u062b\u0627\u0628\u062a",
    "\u0645\u0627 \u0639\u0645 \u0628\u0646\u0632\u0644",
    "\u0645\u0627 \u0639\u0645 \u0628\u0632\u064a\u062f",
}
TROUBLESHOOT_KEYWORDS = {
    "exercise wrong",
    "wrong form",
    "bad form",
    "pain during exercise",
    "injury",
    "hurts",
    "movement is wrong",
    "\u0627\u0644\u062a\u0645\u0631\u064a\u0646 \u063a\u0644\u0637",
    "\u062d\u0631\u0643\u062a\u064a \u063a\u0644\u0637",
    "\u0628\u0648\u062c\u0639\u0646\u064a",
    "\u064a\u0648\u062c\u0639\u0646\u064a",
    "\u0627\u0635\u0627\u0628\u0629",
    "\u0625\u0635\u0627\u0628\u0629",
    "\u0623\u0644\u0645",
    "\u0648\u062c\u0639",
}
PLAN_STATUS_KEYWORDS = {
    "active plan",
    "current plan",
    "\u0647\u0644 \u0639\u0646\u062f\u064a \u062e\u0637\u0629",
    "\u0634\u0648 \u062e\u0637\u062a\u064a",
    "\u0645\u0627 \u0647\u064a \u062e\u0637\u062a\u064a",
    "\u062e\u0637\u062a\u064a \u0627\u0644\u062d\u0627\u0644\u064a\u0629",
}

# Add robust Arabic forms to avoid encoding-related misses.
GREETING_KEYWORDS = GREETING_KEYWORDS | {
    "\u0645\u0631\u062d\u0628\u0627",
    "\u0627\u0647\u0644\u0627",
    "\u0647\u0644\u0627",
    "\u0627\u0644\u0633\u0644\u0627\u0645 \u0639\u0644\u064a\u0643\u0645",
}
NAME_KEYWORDS = NAME_KEYWORDS | {
    "\u0627\u0633\u0645\u0643",
    "\u0634\u0648 \u0627\u0633\u0645\u0643",
    "\u0645\u064a\u0646 \u0627\u0646\u062a",
}
HOW_ARE_YOU_KEYWORDS = HOW_ARE_YOU_KEYWORDS | {
    "\u0643\u064a\u0641\u0643",
    "\u0634\u0644\u0648\u0646\u0643",
    "\u0643\u064a\u0641 \u062d\u0627\u0644\u0643",
}
WORKOUT_PLAN_KEYWORDS = WORKOUT_PLAN_KEYWORDS | {
    "\u062e\u0637\u0629 \u062a\u0645\u0627\u0631\u064a\u0646",
    "\u0628\u0631\u0646\u0627\u0645\u062c \u062a\u0645\u0627\u0631\u064a\u0646",
    "\u062c\u062f\u0648\u0644 \u062a\u0645\u0627\u0631\u064a\u0646",
    "\u062a\u0645\u0631\u064a\u0646",
    "\u062a\u0645\u0627\u0631\u064a\u0646",
    "\u0627\u0644\u0635\u062f\u0631",
    "\u0627\u0644\u0638\u0647\u0631",
    "\u0627\u0644\u0633\u0627\u0642",
    "\u0627\u0644\u0627\u0631\u062c\u0644",
    "\u0627\u0644\u0643\u062a\u0641",
}
NUTRITION_PLAN_KEYWORDS = NUTRITION_PLAN_KEYWORDS | {
    "\u062e\u0637\u0629 \u063a\u0630\u0627\u0626\u064a\u0629",
    "\u062e\u0637\u0629 \u062a\u063a\u0630\u064a\u0629",
    "\u062c\u062f\u0648\u0644 \u0648\u062c\u0628\u0627\u062a",
    "\u0633\u0639\u0631\u0627\u062a",
    "\u0628\u0631\u0648\u062a\u064a\u0646",
}
PROGRESS_KEYWORDS = PROGRESS_KEYWORDS | {
    "\u0627\u0644\u062a\u0632\u0627\u0645",
    "\u0627\u0644\u062a\u0642\u062f\u0645",
    "\u0627\u0646\u062c\u0627\u0632",
    "\u0645\u0627 \u0641\u064a \u0641\u0631\u0642",
}
JORDANIAN_HINTS = JORDANIAN_HINTS | {
    "\u0634\u0648",
    "\u0628\u062f\u0643",
    "\u0645\u0634",
    "\u0645\u0646\u064a\u062d",
    "\u062a\u0645\u0627\u0645",
}

STRONG_DOMAIN_KEYWORDS = {
    "workout",
    "exercise",
    "training",
    "gym",
    "muscle",
    "nutrition",
    "meal",
    "diet",
    "calories",
    "protein",
    "\u062a\u0645\u0631\u064a\u0646",
    "\u062a\u0645\u0627\u0631\u064a\u0646",
    "\u062a\u062f\u0631\u064a\u0628",
    "\u0627\u0644\u0635\u062f\u0631",
    "\u0639\u0636\u0644",
    "\u0639\u0636\u0644\u0627\u062a",
    "\u063a\u0630\u0627\u0621",
    "\u062a\u063a\u0630\u064a\u0629",
    "\u0648\u062c\u0628\u0627\u062a",
    "\u0633\u0639\u0631\u0627\u062a",
    "\u0628\u0631\u0648\u062a\u064a\u0646",
    "\u0644\u064a\u0627\u0642\u0629",
}


def _expand_keyword_set_with_repair(values: set[str]) -> set[str]:
    expanded = set(values)
    for value in list(values):
        repaired = _repair_mojibake(value)
        if repaired:
            expanded.add(repaired)
    return expanded


GREETING_KEYWORDS = _expand_keyword_set_with_repair(GREETING_KEYWORDS)
NAME_KEYWORDS = _expand_keyword_set_with_repair(NAME_KEYWORDS)
HOW_ARE_YOU_KEYWORDS = _expand_keyword_set_with_repair(HOW_ARE_YOU_KEYWORDS)
WORKOUT_PLAN_KEYWORDS = _expand_keyword_set_with_repair(WORKOUT_PLAN_KEYWORDS)
NUTRITION_PLAN_KEYWORDS = _expand_keyword_set_with_repair(NUTRITION_PLAN_KEYWORDS)
NUTRITION_KB_KEYWORDS = _expand_keyword_set_with_repair(NUTRITION_KB_KEYWORDS)
PROGRESS_KEYWORDS = _expand_keyword_set_with_repair(PROGRESS_KEYWORDS)
APPROVE_KEYWORDS = _expand_keyword_set_with_repair(APPROVE_KEYWORDS)
REJECT_KEYWORDS = _expand_keyword_set_with_repair(REJECT_KEYWORDS)
JORDANIAN_HINTS = _expand_keyword_set_with_repair(JORDANIAN_HINTS)
PLAN_CHOICE_KEYWORDS = _expand_keyword_set_with_repair(PLAN_CHOICE_KEYWORDS)
PLAN_REFRESH_KEYWORDS = _expand_keyword_set_with_repair(PLAN_REFRESH_KEYWORDS)
THANKS_KEYWORDS = _expand_keyword_set_with_repair(THANKS_KEYWORDS)
WHO_AM_I_KEYWORDS = _expand_keyword_set_with_repair(WHO_AM_I_KEYWORDS)
ASK_MY_AGE_KEYWORDS = _expand_keyword_set_with_repair(ASK_MY_AGE_KEYWORDS)
ASK_MY_HEIGHT_KEYWORDS = _expand_keyword_set_with_repair(ASK_MY_HEIGHT_KEYWORDS)
ASK_MY_WEIGHT_KEYWORDS = _expand_keyword_set_with_repair(ASK_MY_WEIGHT_KEYWORDS)
ASK_MY_GOAL_KEYWORDS = _expand_keyword_set_with_repair(ASK_MY_GOAL_KEYWORDS)
PROGRESS_CONCERN_KEYWORDS = _expand_keyword_set_with_repair(PROGRESS_CONCERN_KEYWORDS)
TROUBLESHOOT_KEYWORDS = _expand_keyword_set_with_repair(TROUBLESHOOT_KEYWORDS)
PLAN_STATUS_KEYWORDS = _expand_keyword_set_with_repair(PLAN_STATUS_KEYWORDS)
STRONG_DOMAIN_KEYWORDS = _expand_keyword_set_with_repair(STRONG_DOMAIN_KEYWORDS)

MOTIVATION_LINES = {
    "en": [
        "Your consistency lately is excellent.",
        "You are progressing step by step in the right direction.",
        "Even if progress feels slow, your discipline is working.",
        "What you are doing now will show clear results soon.",
        "Real progress starts with routine, and you are building it.",
        "You are doing better than you think.",
    ],
    "ar_fusha": [
        "\u0639\u0645\u0644\u0643 \u0645\u0645\u062a\u0627\u0632 \u0641\u064a \u0627\u0644\u0641\u062a\u0631\u0629 \u0627\u0644\u0623\u062e\u064a\u0631\u0629.",
        "\u0648\u0627\u0636\u062d \u0623\u0646\u0643 \u0645\u0644\u062a\u0632\u0645 \u0648\u062a\u062a\u0642\u062f\u0645 \u062e\u0637\u0648\u0629 \u0628\u062e\u0637\u0648\u0629.",
        "\u0623\u0646\u0627 \u0641\u062e\u0648\u0631 \u0628\u0627\u0644\u0627\u0644\u062a\u0632\u0627\u0645 \u0627\u0644\u0630\u064a \u062a\u0642\u062f\u0645\u0647.",
        "\u062d\u062a\u0649 \u0644\u0648 \u0643\u0627\u0646 \u0627\u0644\u062a\u0642\u062f\u0645 \u0628\u0637\u064a\u0626\u0627\u064b \u0641\u0623\u0646\u062a \u0639\u0644\u0649 \u0627\u0644\u0645\u0633\u0627\u0631 \u0627\u0644\u0635\u062d\u064a\u062d.",
        "\u0627\u0644\u0646\u062a\u0627\u0626\u062c \u0627\u0644\u062c\u064a\u062f\u0629 \u062a\u0628\u062f\u0623 \u0628\u0627\u0644\u0627\u0646\u0636\u0628\u0627\u0637.",
        "\u0627\u0633\u062a\u0645\u0631 \u2014 \u0623\u0646\u062a \u0645\u0627\u0634\u064d \u0628\u0634\u0643\u0644 \u0645\u0645\u062a\u0627\u0632.",
    ],
    "ar_jordanian": [
        "\u0634\u063a\u0644\u0643 \u0645\u0645\u062a\u0627\u0632 \u0628\u0627\u0644\u0641\u062a\u0631\u0629 \u0627\u0644\u0623\u062e\u064a\u0631\u0629.",
        "\u0648\u0627\u0636\u062d \u0625\u0646\u0643 \u0645\u0644\u062a\u0632\u0645 \u0648\u0639\u0645 \u062a\u062a\u0642\u062f\u0645 \u0634\u0648\u064a \u0634\u0648\u064a.",
        "\u062d\u062a\u0649 \u0644\u0648 \u0627\u0644\u062a\u0642\u062f\u0645 \u0628\u0637\u064a\u0621 \u2014 \u0625\u0646\u062a \u0645\u0627\u0634\u064a \u0635\u062d.",
        "\u0627\u0633\u062a\u0645\u0631\u060c \u0625\u0646\u062a \u0639\u0644\u0649 \u0627\u0644\u0645\u0633\u0627\u0631 \u0627\u0644\u0635\u062d.",
        "\u0627\u0644\u0646\u062a\u0627\u0626\u062c \u0628\u062f\u0647\u0627 \u0635\u0628\u0631 \u0628\u0633 \u0625\u0646\u062a \u0634\u063a\u0627\u0644 \u0635\u062d.",
        "\u0623\u0646\u0627 \u0645\u0639\u0643 \u062e\u0637\u0648\u0629 \u0628\u062e\u0637\u0648\u0629.",
    ],
}

def _normalize_user_id(user_id: Optional[str]) -> str:
    return (user_id or "anonymous").strip() or "anonymous"


def _normalize_conversation_id(conversation_id: Optional[str], user_id: str) -> str:
    return (conversation_id or f"conv_{user_id}").strip() or f"conv_{user_id}"


def _session_key(user_id: str, conversation_id: str) -> str:
    return f"{user_id}:{conversation_id}"


def _get_memory_session(user_id: str, conversation_id: str) -> MemorySystem:
    key = _session_key(user_id, conversation_id)
    if key not in MEMORY_SESSIONS:
        MEMORY_SESSIONS[key] = MemorySystem(user_id=user_id, max_short_term=10)
    return MEMORY_SESSIONS[key]


def _get_user_state(user_id: str) -> Dict[str, Any]:
    if user_id not in USER_STATE:
        USER_STATE[user_id] = {}
    return USER_STATE[user_id]


def _contains_any(text: str, keywords: set[str]) -> bool:
    return fuzzy_contains_any(text, keywords)


def _contains_phrase(text: str, phrases: set[str]) -> bool:
    normalized_text = normalize_text(text)
    if not normalized_text:
        return False
    for phrase in phrases:
        phrase_norm = normalize_text(phrase)
        if phrase_norm and phrase_norm in normalized_text:
            return True
    return False


def _is_nutrition_knowledge_query(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    if not normalized:
        return False
    return _contains_any(normalized, NUTRITION_KB_KEYWORDS | NUTRITION_PLAN_KEYWORDS)


def _is_greeting_query(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    if not normalized:
        return False
    if len(normalized.split()) > 4:
        return False
    greeting_phrases = {
        "hi",
        "hello",
        "hey",
        "مرحبا",
        "اهلا",
        "هلا",
        "السلام عليكم",
        "سلام",
    }
    return _contains_phrase(normalized, greeting_phrases)


def _is_name_query(user_input: str) -> bool:
    return _contains_phrase(
        user_input,
        {
            "what is your name",
            "your name",
            "name",
            "اسمك",
            "شو اسمك",
            "مين انت",
            "من انت",
        },
    )


def _is_how_are_you_query(user_input: str) -> bool:
    return _contains_phrase(
        user_input,
        {
            "how are you",
            "كيفك",
            "كيف حالك",
            "شلونك",
            "كيف الحال",
        },
    )


def _is_workout_plan_request(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    plan_terms = {
        "plan",
        "program",
        "schedule",
        "weekly",
        "خطة",
        "جدول",
        "برنامج",
        "اسبوع",
        "أسبوع",
    }
    workout_terms = {
        "workout",
        "training",
        "exercise",
        "gym",
        "تمرين",
        "تمارين",
        "تدريب",
        "عضل",
        "عضلات",
    }
    return _contains_any(normalized, plan_terms) and _contains_any(normalized, workout_terms)


def _is_nutrition_plan_request(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    plan_terms = {
        "plan",
        "program",
        "schedule",
        "daily",
        "خطة",
        "جدول",
        "برنامج",
        "يومي",
        "يومية",
    }
    nutrition_terms = {
        "nutrition",
        "diet",
        "meal",
        "calories",
        "food",
        "تغذية",
        "وجبات",
        "اكل",
        "طعام",
        "سعرات",
    }
    return _contains_any(normalized, plan_terms) and _contains_any(normalized, nutrition_terms)


def _has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


def _detect_language(requested_language: str, message: str, profile: dict[str, Any]) -> str:
    requested = (requested_language or "en").strip().lower()
    if requested in {"en", "ar_fusha", "ar_jordanian"}:
        return requested

    if requested == "ar" or _has_arabic(message):
        preferred = str(profile.get("preferred_language", "")).lower()
        if preferred in {"ar_fusha", "ar_jordanian"}:
            return preferred

        lowered = normalize_text(message)
        if any(token in lowered for token in JORDANIAN_HINTS):
            return "ar_jordanian"
        return "ar_fusha"

    return "en"


def _parse_list_field(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        split_tokens = re.split(r"[,،\n]| and | و ", _repair_mojibake(value))
        return [t.strip() for t in split_tokens if t.strip()]
    return [str(value).strip()]


def _nutrition_kb_context(user_input: str, profile: dict[str, Any], top_k: int = 3) -> str:
    if not NUTRITION_KB.ready:
        return ""
    if not _is_nutrition_knowledge_query(user_input):
        return ""

    query_parts: list[str] = [user_input]
    goal = str(profile.get("goal", "")).strip()
    if goal:
        query_parts.append(goal)

    chronic_diseases = _parse_list_field(profile.get("chronic_diseases"))
    allergies = _parse_list_field(profile.get("allergies"))
    if chronic_diseases:
        query_parts.append(" ".join(chronic_diseases))
    if allergies:
        query_parts.append(" ".join(allergies))

    query = " | ".join(part for part in query_parts if part)
    hits = NUTRITION_KB.search(query, top_k=top_k, max_chars=420)
    if not hits:
        return ""
    return "\n".join(f"- {hit['text']}" for hit in hits)


def _normalize_goal(goal: Any) -> str:
    text = normalize_text(str(goal or ""))
    if not text:
        return ""
    if fuzzy_contains_any(
        text,
        {
            "bulking",
            "muscle gain",
            "gain muscle",
            "build muscle",
            "hypertrophy",
            "تضخيم",
            "زيادة عضل",
            "بناء عضل",
        },
    ):
        return "muscle_gain"
    if fuzzy_contains_any(
        text,
        {
            "cutting",
            "fat loss",
            "lose fat",
            "lose weight",
            "weight loss",
            "تنشيف",
            "خسارة وزن",
            "نزول وزن",
            "حرق دهون",
        },
    ):
        return "fat_loss"
    if fuzzy_contains_any(text, {"fitness", "general fitness", "health", "maintenance", "لياقة", "رشاقة", "صحة"}):
        return "general_fitness"
    if text in {"bulking", "muscle_gain", "gain muscle", "build muscle", "زيادة عضل", "بناء عضل"}:
        return "muscle_gain"
    if text in {"cutting", "fat_loss", "lose fat", "lose weight", "تنشيف", "خسارة وزن"}:
        return "fat_loss"
    if text in {"fitness", "general_fitness", "لياقة", "رشاقة"}:
        return "general_fitness"
    return text


def _build_profile(req: ChatRequest, user_state: dict[str, Any]) -> dict[str, Any]:
    profile = dict(req.user_profile or {})

    if "chronicConditions" in profile and "chronic_diseases" not in profile:
        profile["chronic_diseases"] = _parse_list_field(profile.get("chronicConditions"))
    if "allergies" in profile:
        profile["allergies"] = _parse_list_field(profile.get("allergies"))
    if "chronic_diseases" in profile:
        profile["chronic_diseases"] = _parse_list_field(profile.get("chronic_diseases"))

    profile["goal"] = _normalize_goal(profile.get("goal"))

    for key in (
        "goal",
        "fitness_level",
        "rest_days",
        "age",
        "weight",
        "height",
        "gender",
        "meals_per_day",
        "allergies",
        "chronic_diseases",
        "target_calories",
        "preferred_language",
    ):
        if key in user_state and user_state[key] is not None:
            profile[key] = user_state[key]

    return profile


def _lang_reply(language: str, en: str, ar_fusha: str, ar_jordanian: Optional[str] = None) -> str:
    if language == "en":
        return _repair_mojibake(en)
    if language == "ar_fusha":
        return _repair_mojibake(ar_fusha)
    return _repair_mojibake(ar_jordanian or ar_fusha)


def _motivation_line(language: str, seed: str = "") -> str:
    lines = MOTIVATION_LINES.get(language) or MOTIVATION_LINES["en"]
    if not lines:
        return ""
    idx = abs(hash(seed or "default")) % len(lines)
    return lines[idx]


def _persist_profile_context(profile: dict[str, Any], state: dict[str, Any]) -> None:
    tracked_keys = (
        "name",
        "goal",
        "fitness_level",
        "rest_days",
        "age",
        "weight",
        "height",
        "gender",
        "meals_per_day",
        "allergies",
        "chronic_diseases",
        "target_calories",
        "preferred_language",
    )
    for key in tracked_keys:
        value = profile.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, list) and not value:
            continue
        state[key] = value


def _profile_display_name(profile: dict[str, Any]) -> str:
    for key in ("name", "full_name", "first_name"):
        value = profile.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _profile_goal_label(goal: str, language: str) -> str:
    goal_key = str(goal or "").strip().lower()
    if goal_key == "muscle_gain":
        return _lang_reply(language, "muscle gain", "زيادة الكتلة العضلية", "زيادة العضل")
    if goal_key == "fat_loss":
        return _lang_reply(language, "fat loss", "خسارة الدهون", "تنزيل الدهون")
    if goal_key == "general_fitness":
        return _lang_reply(language, "general fitness", "اللياقة العامة", "لياقة عامة")
    return str(goal or "")


def _profile_query_reply(
    user_input: str,
    language: str,
    profile: dict[str, Any],
    tracking_summary: Optional[dict[str, Any]],
) -> Optional[str]:
    name = _profile_display_name(profile)
    goal_label = _profile_goal_label(str(profile.get("goal", "")), language)
    age = profile.get("age")
    height = profile.get("height")
    weight = profile.get("weight")
    normalized = normalize_text(user_input)

    if _contains_any(normalized, WHO_AM_I_KEYWORDS):
        if name:
            return _lang_reply(
                language,
                f"You are {name}. I have your profile and can coach you using your goal, body stats, and progress.",
                f"أنت {name}. لدي ملفك الشخصي، وأستطيع تدريبك وفق هدفك وقياساتك وتقدمك.",
                f"إنت {name}. عندي ملفك، وبقدر أدربك حسب هدفك وقياساتك وتقدمك.",
            )
        return _lang_reply(
            language,
            "I do not have your name yet. Add it in your profile page and I will personalize every response.",
            "لا أملك اسمك بعد. أضفه في صفحة الملف الشخصي وسأخصص كل الردود لك.",
            "لسا ما عندي اسمك. حطه بصفحة البروفايل وبخصصلك كل الردود.",
        )

    if _contains_any(normalized, ASK_MY_AGE_KEYWORDS):
        if age is not None:
            return _lang_reply(
                language,
                f"Your age is {age}.",
                f"عمرك هو {age}.",
                f"عمرك {age}.",
            )
        return _lang_reply(
            language,
            "I do not have your age yet. Update it in your profile and I will use it in your plans.",
            "لا أملك عمرك بعد. حدّثه في الملف الشخصي وسأستخدمه في خططك.",
            "لسا ما عندي عمرك. حدّثه بالبروفايل وبستخدمه بخططك.",
        )

    if _contains_any(normalized, ASK_MY_HEIGHT_KEYWORDS):
        if height is not None:
            return _lang_reply(
                language,
                f"Your height is {height} cm.",
                f"طولك هو {height} سم.",
                f"طولك {height} سم.",
            )
        return _lang_reply(
            language,
            "I do not have your height yet. Add it in your profile to make training and calories more accurate.",
            "لا أملك طولك بعد. أضفه في ملفك لتحسين دقة التدريب والسعرات.",
            "لسا ما عندي طولك. أضفه بالبروفايل عشان أدق بالتمارين والسعرات.",
        )

    if _contains_any(normalized, ASK_MY_WEIGHT_KEYWORDS):
        if weight is not None:
            return _lang_reply(
                language,
                f"Your weight is {weight} kg.",
                f"وزنك هو {weight} كغ.",
                f"وزنك {weight} كيلو.",
            )
        return _lang_reply(
            language,
            "I do not have your weight yet. Add it in your profile and I will tune your plan calories better.",
            "لا أملك وزنك بعد. أضفه في ملفك وسأضبط سعرات الخطة بدقة أعلى.",
            "لسا ما عندي وزنك. أضفه بالبروفايل وبضبطلك السعرات أدق.",
        )

    if _contains_any(normalized, ASK_MY_GOAL_KEYWORDS):
        if goal_label:
            return _lang_reply(
                language,
                f"Your current goal is {goal_label}.",
                f"هدفك الحالي هو: {goal_label}.",
                f"هدفك الحالي: {goal_label}.",
            )
        return _lang_reply(
            language,
            "Your goal is not set yet. Tell me if you want muscle gain, fat loss, or general fitness.",
            "هدفك غير محدد بعد. أخبرني: زيادة عضل أم خسارة دهون أم لياقة عامة.",
            "لسا هدفك مش محدد. احكيلي: زيادة عضل ولا تنزيل دهون ولا لياقة عامة.",
        )

    if _contains_any(normalized, {"my progress summary", "ملخص تقدمي", "ملخص التقدم"}):
        return _tracking_reply(language, tracking_summary)

    return None


def _social_reply(user_input: str, language: str, profile: dict[str, Any]) -> Optional[str]:
    normalized = normalize_text(user_input)
    name = _profile_display_name(profile)
    name_suffix = f" {name}" if name else ""

    if _contains_any(normalized, THANKS_KEYWORDS):
        return _lang_reply(
            language,
            f"Anytime{name_suffix}. Keep going and send me your next update.",
            f"على الرحب والسعة{name_suffix}. استمر وأرسل لي تحديثك التالي.",
            f"على راسي{name_suffix}. كمل وابعثلي تحديثك الجاي.",
        )
    return None


def _plan_status_reply(language: str, plan_snapshot: Optional[dict[str, Any]]) -> str:
    if not plan_snapshot:
        return _lang_reply(
            language,
            "I do not have your latest plan status yet. Open your Schedule page and I can sync after your next message.",
            "Ù„Ø§ Ø£Ù…Ù„Ùƒ Ø¢Ø®Ø± Ø­Ø§Ù„Ø© Ù„Ø®Ø·Ø·Ùƒ Ø¨Ø¹Ø¯. Ø§ÙØªØ­ ØµÙØ­Ø© Ø§Ù„Ø¬Ø¯ÙˆÙ„ ÙˆØ³Ø£Ø²Ø§Ù…Ù†Ù‡Ø§ Ø¨Ø¹Ø¯ Ø±Ø³Ø§Ù„ØªÙƒ Ø§Ù„ØªØ§Ù„ÙŠØ©.",
            "Ù„Ø³Ø§ Ù…Ø§ Ø¹Ù†Ø¯ÙŠ Ø¢Ø®Ø± Ø­Ø§Ù„Ø© Ù„Ù„Ø®Ø·Ø·. Ø§ÙØªØ­ ØµÙØ­Ø© Ø§Ù„Ø¬Ø¯ÙˆÙ„ ÙˆØ¨Ø±Ø¬Ø¹ Ø¨Ø²Ø§Ù…Ù†Ù‡Ø§ Ù…Ø¹Ùƒ Ø¨Ø¹Ø¯ Ø±Ø³Ø§Ù„ØªÙƒ Ø§Ù„Ø¬Ø§ÙŠØ©.",
        )

    workout_count = int(plan_snapshot.get("active_workout_plans", 0) or 0)
    nutrition_count = int(plan_snapshot.get("active_nutrition_plans", 0) or 0)
    return _lang_reply(
        language,
        f"You currently have {workout_count} active workout plan(s) and {nutrition_count} active nutrition plan(s).",
        f"Ù„Ø¯ÙŠÙƒ Ø­Ø§Ù„ÙŠÙ‹Ø§ {workout_count} Ø®Ø·Ø© ØªÙ…Ø§Ø±ÙŠÙ† Ù†Ø´Ø·Ø© Ùˆ{nutrition_count} Ø®Ø·Ø© ØªØºØ°ÙŠØ© Ù†Ø´Ø·Ø©.",
        f"Ø­Ø§Ù„ÙŠÙ‹Ø§ Ø¹Ù†Ø¯Ùƒ {workout_count} Ø®Ø·Ø© ØªÙ…Ø§Ø±ÙŠÙ† ÙØ¹Ø§Ù„Ø© Ùˆ{nutrition_count} Ø®Ø·Ø© ØªØºØ°ÙŠØ© ÙØ¹Ø§Ù„Ø©.",
    )


def _progress_diagnostic_reply(language: str, profile: dict[str, Any], tracking_summary: Optional[dict[str, Any]]) -> str:
    adherence = 0.0
    if tracking_summary:
        try:
            adherence = float(tracking_summary.get("adherence_score", 0) or 0)
        except (TypeError, ValueError):
            adherence = 0.0
    adherence_pct = int(round(adherence * 100))
    weight = profile.get("weight")
    try:
        hydration_liters = round(max(1.8, float(weight) * 0.033), 1) if weight is not None else 2.5
    except (TypeError, ValueError):
        hydration_liters = 2.5

    return _lang_reply(
        language,
        (
            f"Plateaus are common. Your adherence is about {adherence_pct}%. "
            "Let us find the cause step by step:\n"
            "1. How many hours do you sleep on average?\n"
            f"2. Do you drink around {hydration_liters}L water daily?\n"
            "3. Are you completing your planned sets/reps, or stopping early?\n"
            "4. Are you consistently hitting your calories and protein targets?\n"
            "Reply with these 4 points and I will give you a precise fix."
        ),
        (
            f"ثبات النتائج أمر طبيعي أحيانًا. نسبة التزامك الحالية تقريبًا {adherence_pct}%.\n"
            "لنحدد السبب خطوة بخطوة:\n"
            "1. كم ساعة تنام يوميًا بالمتوسط؟\n"
            f"2. هل تشرب تقريبًا {hydration_liters} لتر ماء يوميًا؟\n"
            "3. هل تكمل المجموعات والتكرارات كاملة أم تتوقف مبكرًا؟\n"
            "4. هل تلتزم يوميًا بسعراتك وبروتينك المستهدف؟\n"
            "أجبني على هذه النقاط الأربع وسأعطيك الحل الأدق."
        ),
        (
            f"ثبات الجسم بصير، والتزامك الحالي تقريبًا {adherence_pct}%.\n"
            "خلينا نعرف السبب شوي شوي:\n"
            "1. كم ساعة نومك بالمتوسط؟\n"
            f"2. بتشرب تقريبًا {hydration_liters} لتر مي باليوم؟\n"
            "3. بتكمل كل المجموعات والتكرارات ولا بتوقف بكير؟\n"
            "4. ملتزم بسعراتك وبروتينك يوميًا؟\n"
            "جاوبني بهدول الأربع نقاط وبعطيك الحل الأدق."
        ),
    )


def _exercise_diagnostic_reply(language: str) -> str:
    return _lang_reply(
        language,
        (
            "Understood. To fix your exercise form safely, answer these points:\n"
            "1. Which exercise exactly?\n"
            "2. Where do you feel pain/tension?\n"
            "3. At which rep does form break down?\n"
            "4. What load are you using now?\n"
            "5. Did this start after an injury or sudden volume increase?\n"
            "After your answers, I will give exact technique corrections and load changes."
        ),
        (
            "ممتاز، لنصحح أداء التمرين بشكل آمن أجبني على التالي:\n"
            "1. ما اسم التمرين بالضبط؟\n"
            "2. أين تشعر بالألم أو الشد؟\n"
            "3. في أي تكرار يبدأ الأداء بالانهيار؟\n"
            "4. ما الوزن الذي تستخدمه الآن؟\n"
            "5. هل بدأ هذا بعد إصابة أو زيادة مفاجئة في الحمل التدريبي؟\n"
            "بعد إجاباتك أعطيك تصحيحًا دقيقًا للحركة وتعديلًا مناسبًا للأوزان."
        ),
        (
            "تمام، عشان نصلح الأداء بدون إصابة جاوبني:\n"
            "1. شو اسم التمرين بالزبط؟\n"
            "2. وين بتحس بالألم أو الشد؟\n"
            "3. بأي تكرار بتخرب الحركة؟\n"
            "4. كم الوزن اللي بتلعب فيه هسا؟\n"
            "5. المشكلة بلشت بعد إصابة أو زيادة حمل مفاجئة؟\n"
            "بعدها بعطيك تصحيح دقيق للحركة وتعديل الوزن."
        ),
    )


def _normalize_recent_messages(raw_messages: Optional[list[dict[str, Any]]]) -> list[dict[str, str]]:
    if not raw_messages:
        return []
    cleaned: list[dict[str, str]] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = _repair_mojibake(str(item.get("content", "")).strip())
        if not content:
            continue
        cleaned.append({"role": role, "content": content})
    return cleaned[-12:]


def _update_plan_snapshot_state(state: dict[str, Any], new_snapshot: Optional[dict[str, Any]]) -> None:
    if not new_snapshot:
        return

    previous = state.get("plan_snapshot")
    state["plan_snapshot"] = new_snapshot

    if not isinstance(previous, dict):
        return

    previous_total = int(previous.get("active_workout_plans", 0) or 0) + int(previous.get("active_nutrition_plans", 0) or 0)
    new_total = int(new_snapshot.get("active_workout_plans", 0) or 0) + int(new_snapshot.get("active_nutrition_plans", 0) or 0)

    if new_total < previous_total:
        state["plans_recently_deleted"] = True
    elif new_total >= previous_total:
        state["plans_recently_deleted"] = False


def _missing_fields_for_plan(plan_type: str, profile: dict[str, Any]) -> list[str]:
    if plan_type == "workout":
        required = ["goal", "fitness_level", "rest_days"]
    else:
        required = ["goal", "age", "weight", "height", "gender", "meals_per_day", "chronic_diseases", "allergies"]

    missing: list[str] = []
    for key in required:
        value = profile.get(key)
        if value is None:
            missing.append(key)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(key)
            continue
        if key == "rest_days" and (not isinstance(value, list) or len(value) == 0):
            missing.append(key)
    return missing


def _missing_field_question(field_name: str, language: str) -> str:
    questions = {
        "en": {
            "goal": "What is your main goal now: muscle gain, fat loss, or general fitness?",
            "fitness_level": "What is your current fitness level: beginner, intermediate, or advanced?",
            "rest_days": "Which days do you want as rest days this week?",
            "age": "What is your age?",
            "weight": "What is your current weight in kg?",
            "height": "What is your height in cm?",
            "gender": "What is your gender (male/female)?",
            "meals_per_day": "How many meals do you want per day (3, 4, or 5)?",
            "chronic_diseases": "Do you have any chronic diseases I should consider? If none, reply with 'none'.",
            "allergies": "Do you have any food allergies? If none, reply with 'none'.",
        },
        "ar_fusha": {
            "goal": "ما هو هدفك الرئيسي الآن: بناء عضل أم خسارة دهون أم لياقة عامة؟",
            "fitness_level": "ما هو مستواك الرياضي الحالي: مبتدئ أم متوسط أم متقدم؟",
            "rest_days": "ما هي أيام الراحة التي تريدها هذا الأسبوع؟",
            "age": "كم عمرك؟",
            "weight": "ما وزنك الحالي بالكيلوغرام؟",
            "height": "ما طولك بالسنتيمتر؟",
            "gender": "ما جنسك (ذكر/أنثى)؟",
            "meals_per_day": "كم وجبة تريد يوميًا (3 أو 4 أو 5)؟",
            "chronic_diseases": "هل لديك أمراض مزمنة يجب أخذها بالحسبان؟ إذا لا يوجد اكتب: لا يوجد",
            "allergies": "هل لديك أي حساسية غذائية؟ إذا لا يوجد اكتب: لا يوجد",
        },
        "ar_jordanian": {
            "goal": "شو هدفك هلأ: زيادة عضل، نزول دهون، ولا لياقة عامة؟",
            "fitness_level": "شو مستواك الرياضي: مبتدئ، متوسط، ولا متقدم؟",
            "rest_days": "أي أيام بدك تكون أيام راحة بالأسبوع؟",
            "age": "كم عمرك؟",
            "weight": "شو وزنك الحالي بالكيلو؟",
            "height": "كم طولك بالسنتي؟",
            "gender": "شو جنسك (ذكر/أنثى)؟",
            "meals_per_day": "كم وجبة بدك باليوم (3 أو 4 أو 5)؟",
            "chronic_diseases": "في أمراض مزمنة لازم آخدها بالحسبان؟ إذا ما في اكتب: ما في",
            "allergies": "عندك حساسية أكل؟ إذا ما في اكتب: ما في",
        },
    }
    return questions.get(language, questions["en"]).get(field_name, questions["en"]["goal"])


def _parse_rest_days(text: str) -> list[str]:
    lowered = text.lower()
    english_map = {
        "saturday": "Saturday",
        "sunday": "Sunday",
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
    }
    arabic_map = {
        "السبت": "Saturday",
        "الأحد": "Sunday",
        "الاحد": "Sunday",
        "الاثنين": "Monday",
        "الثلاثاء": "Tuesday",
        "الأربعاء": "Wednesday",
        "الاربعاء": "Wednesday",
        "الخميس": "Thursday",
        "الجمعة": "Friday",
    }

    results: list[str] = []
    for name, normalized in english_map.items():
        if name in lowered:
            results.append(normalized)
    for name, normalized in arabic_map.items():
        if name in text:
            results.append(normalized)

    deduped: list[str] = []
    for day_name in results:
        if day_name not in deduped:
            deduped.append(day_name)
    return deduped


def _apply_profile_answer(field_name: str, answer: str, user_state: dict[str, Any]) -> bool:
    text = answer.strip()
    lowered = text.lower()

    if field_name == "goal":
        normalized_goal = _normalize_goal(text)
        if not normalized_goal:
            return False
        user_state["goal"] = normalized_goal
        return True
    if field_name == "fitness_level":
        if "begin" in lowered or "مبت" in lowered:
            user_state["fitness_level"] = "beginner"
            return True
        if "inter" in lowered or "متوس" in lowered:
            user_state["fitness_level"] = "intermediate"
            return True
        if "adv" in lowered or "متقد" in lowered:
            user_state["fitness_level"] = "advanced"
            return True
        return False
    if field_name in {"age", "weight", "height"}:
        match = re.search(r"\d+(\.\d+)?", lowered)
        if not match:
            return False
        numeric_value = float(match.group())
        user_state[field_name] = int(numeric_value) if field_name == "age" else numeric_value
        return True
    if field_name == "gender":
        if any(token in lowered for token in ("male", "ذكر", "man")):
            user_state["gender"] = "male"
            return True
        if any(token in lowered for token in ("female", "أنث", "انث", "woman")):
            user_state["gender"] = "female"
            return True
        return False
    if field_name == "meals_per_day":
        match = re.search(r"\d+", lowered)
        if not match:
            return False
        meals_count = int(match.group())
        if meals_count < 3 or meals_count > 6:
            return False
        user_state["meals_per_day"] = meals_count
        return True
    if field_name == "rest_days":
        rest_days = _parse_rest_days(text)
        if not rest_days:
            return False
        user_state["rest_days"] = rest_days
        return True
    if field_name == "chronic_diseases":
        if any(token in lowered for token in ("none", "no", "لا يوجد", "ما في")):
            user_state["chronic_diseases"] = []
            return True
        user_state["chronic_diseases"] = _parse_list_field(text)
        return True
    if field_name == "allergies":
        if any(token in lowered for token in ("none", "no", "لا يوجد", "ما في")):
            user_state["allergies"] = []
            return True
        user_state["allergies"] = _parse_list_field(text)
        return True
    return False


def _select_exercises(focus: str, difficulty: str, max_items: int = 5) -> list[dict[str, Any]]:
    exercises: list[dict[str, Any]] = []
    allowed_difficulties = {
        "beginner": {"Beginner"},
        "intermediate": {"Beginner", "Intermediate"},
        "advanced": {"Beginner", "Intermediate", "Advanced"},
    }
    difficulty_filter = allowed_difficulties.get(difficulty, {"Beginner", "Intermediate"})

    for item in AI_ENGINE.exercises:
        muscle = str(item.get("muscle", "")).lower()
        level = str(item.get("difficulty", "Beginner"))
        if focus in muscle and level in difficulty_filter:
            exercises.append(item)
        if len(exercises) >= max_items:
            break

    if exercises:
        return exercises
    return AI_ENGINE.exercises[:max_items]


def _generate_workout_plan(profile: dict[str, Any], language: str) -> dict[str, Any]:
    goal = profile.get("goal") or "general_fitness"
    difficulty = str(profile.get("fitness_level", "beginner")).lower()
    rest_days = profile.get("rest_days") or ["Friday"]
    rest_days = [day for day in rest_days if isinstance(day, str)]

    if goal == "muscle_gain":
        weekly_focus = ["chest", "back", "legs", "shoulders", "core"]
        default_sets, default_reps = 4, "8-12"
    elif goal == "fat_loss":
        weekly_focus = ["legs", "core", "back", "chest", "shoulders"]
        default_sets, default_reps = 3, "12-15"
    else:
        weekly_focus = ["core", "legs", "back", "chest", "shoulders"]
        default_sets, default_reps = 3, "10-12"

    plan_days: list[dict[str, Any]] = []
    focus_index = 0
    for english_day, arabic_day in WEEK_DAYS:
        if english_day in rest_days:
            plan_days.append(
                {
                    "day": english_day,
                    "dayAr": arabic_day,
                    "focus": "Rest",
                    "exercises": [],
                }
            )
            continue

        focus = weekly_focus[focus_index % len(weekly_focus)]
        focus_index += 1
        exercise_items = _select_exercises(focus, difficulty, max_items=5)

        exercises = []
        for item in exercise_items:
            exercise_name = str(item.get("exercise", "Exercise"))
            exercises.append(
                {
                    "name": exercise_name,
                    "nameAr": exercise_name,
                    "sets": str(default_sets),
                    "reps": default_reps,
                    "rest_seconds": 90 if goal != "fat_loss" else 60,
                    "notes": str(item.get("description", "")),
                }
            )

        plan_days.append(
            {
                "day": english_day,
                "dayAr": arabic_day,
                "focus": focus,
                "exercises": exercises,
            }
        )

    title = "AI Workout Plan"
    title_ar = "خطة تمارين ذكية"
    if language == "ar_jordanian":
        title_ar = "خطة تمارين"

    return {
        "id": f"workout_{uuid.uuid4().hex[:10]}",
        "type": "workout",
        "title": title,
        "title_ar": title_ar,
        "goal": goal,
        "fitness_level": difficulty,
        "rest_days": rest_days,
        "duration_days": 7,
        "days": plan_days,
        "created_at": datetime.utcnow().isoformat(),
    }


def _calculate_calories(profile: dict[str, Any]) -> int:
    if profile.get("target_calories"):
        return int(profile["target_calories"])

    weight = float(profile.get("weight", 70))
    height = float(profile.get("height", 170))
    age = float(profile.get("age", 25))
    gender = str(profile.get("gender", "male")).lower()
    goal = str(profile.get("goal") or "general_fitness")
    fitness_level = str(profile.get("fitness_level", "beginner")).lower()

    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == "male" else -161)
    activity_factor = {"beginner": 1.40, "intermediate": 1.55, "advanced": 1.70}.get(fitness_level, 1.45)
    maintenance = bmr * activity_factor

    if goal == "muscle_gain":
        maintenance += 300
    elif goal == "fat_loss":
        maintenance -= 400

    return max(1200, int(round(maintenance)))


def _safe_meal_templates(allergies: list[str]) -> list[dict[str, Any]]:
    templates = [
        {"name": "Greek Yogurt + Oats + Berries", "calories": 420, "protein": 28, "carbs": 48, "fat": 12, "ingredients": ["yogurt", "oats", "berries"]},
        {"name": "Egg Omelette + Whole Grain Bread", "calories": 460, "protein": 32, "carbs": 34, "fat": 20, "ingredients": ["egg", "bread", "vegetables"]},
        {"name": "Chicken Rice Bowl", "calories": 620, "protein": 45, "carbs": 70, "fat": 16, "ingredients": ["chicken", "rice", "vegetables"]},
        {"name": "Salmon + Sweet Potato", "calories": 650, "protein": 42, "carbs": 58, "fat": 24, "ingredients": ["salmon", "sweet potato", "vegetables"]},
        {"name": "Tuna Wrap", "calories": 480, "protein": 35, "carbs": 44, "fat": 14, "ingredients": ["tuna", "whole wheat tortilla", "vegetables"]},
        {"name": "Lean Beef + Quinoa", "calories": 640, "protein": 43, "carbs": 55, "fat": 20, "ingredients": ["beef", "quinoa", "salad"]},
        {"name": "Protein Shake + Banana", "calories": 320, "protein": 30, "carbs": 34, "fat": 6, "ingredients": ["whey", "banana", "milk"]},
        {"name": "Cottage Cheese + Fruit", "calories": 300, "protein": 24, "carbs": 28, "fat": 8, "ingredients": ["cottage cheese", "fruit"]},
    ]

    allergy_tokens = {a.lower() for a in allergies}
    safe: list[dict[str, Any]] = []
    for meal in templates:
        ingredients_text = " ".join(meal["ingredients"]).lower()
        if any(token and token in ingredients_text for token in allergy_tokens):
            continue
        safe.append(meal)
    return safe if safe else templates


def _build_nutrition_days(profile: dict[str, Any], calories_target: int) -> tuple[list[dict[str, Any]], int]:
    meals_per_day = int(profile.get("meals_per_day", 4))
    meals_per_day = max(3, min(6, meals_per_day))
    allergies = _parse_list_field(profile.get("allergies"))
    chronic = [d.lower() for d in _parse_list_field(profile.get("chronic_diseases"))]

    meal_templates = _safe_meal_templates(allergies)
    meal_templates.sort(key=lambda m: m["calories"])

    if any("diab" in x or "سكر" in x for x in chronic):
        for meal in meal_templates:
            meal["carbs"] = int(round(meal["carbs"] * 0.85))

    meal_ratio = [0.25, 0.10, 0.30, 0.10, 0.20, 0.05]
    day_plans: list[dict[str, Any]] = []
    total_protein = 0

    for day_index, (english_day, arabic_day) in enumerate(WEEK_DAYS):
        meals_for_day: list[dict[str, Any]] = []
        for i in range(meals_per_day):
            template = meal_templates[(i + day_index) % len(meal_templates)]
            target = int(calories_target * meal_ratio[i])
            scale = max(0.6, min(1.6, target / template["calories"]))

            calories = int(round(template["calories"] * scale))
            protein = int(round(template["protein"] * scale))
            carbs = int(round(template["carbs"] * scale))
            fat = int(round(template["fat"] * scale))

            total_protein += protein
            meals_for_day.append(
                {
                    "name": template["name"],
                    "nameAr": template["name"],
                    "description": f"Ingredients: {', '.join(template['ingredients'])}",
                    "descriptionAr": f"المكونات: {', '.join(template['ingredients'])}",
                    "calories": str(calories),
                    "protein": protein,
                    "carbs": carbs,
                    "fat": fat,
                    "time": f"meal_{i + 1}",
                }
            )

        day_plans.append({"day": english_day, "dayAr": arabic_day, "meals": meals_for_day})

    avg_daily_protein = int(round(total_protein / 7))
    return day_plans, avg_daily_protein


def _generate_nutrition_plan(profile: dict[str, Any], language: str) -> dict[str, Any]:
    calories_target = _calculate_calories(profile)
    days, avg_daily_protein = _build_nutrition_days(profile, calories_target)
    chronic = _parse_list_field(profile.get("chronic_diseases"))
    allergies = _parse_list_field(profile.get("allergies"))
    kb_query_parts = [
        "nutrition meal plan",
        str(profile.get("goal", "") or ""),
        " ".join(chronic),
        " ".join(allergies),
    ]
    kb_query = " ".join(part for part in kb_query_parts if part).strip()
    kb_hits = NUTRITION_KB.search(kb_query, top_k=2, max_chars=220) if NUTRITION_KB.ready and kb_query else []
    reference_notes = [hit["text"] for hit in kb_hits]

    notes = []
    if chronic:
        notes.append(f"Adjusted for chronic conditions: {', '.join(chronic)}.")
    if allergies:
        notes.append(f"Avoided allergens: {', '.join(allergies)}.")

    title = "AI Nutrition Plan"
    title_ar = "خطة تغذية ذكية"
    if language == "ar_jordanian":
        title_ar = "خطة أكل"

    return {
        "id": f"nutrition_{uuid.uuid4().hex[:10]}",
        "type": "nutrition",
        "title": title,
        "title_ar": title_ar,
        "goal": profile.get("goal", "general_fitness"),
        "daily_calories": calories_target,
        "estimated_protein": avg_daily_protein,
        "meals_per_day": int(profile.get("meals_per_day", 4)),
        "days": days,
        "notes": " ".join(notes).strip(),
        "reference_notes": reference_notes,
        "created_at": datetime.utcnow().isoformat(),
    }


def _format_plan_preview(plan_type: str, plan: dict[str, Any], language: str) -> str:
    if plan_type == "workout":
        workout_days = [d for d in plan.get("days", []) if d.get("exercises")]
        rest_days = [d.get("day") for d in plan.get("days", []) if not d.get("exercises")]
        sample = workout_days[0]["exercises"][:3] if workout_days else []
        sample_text = "\n".join([f"- {x['name']} ({x['sets']}x{x['reps']})" for x in sample])

        if language == "en":
            return (
                f"I prepared a 7-day workout plan for your goal.\n"
                f"Rest days: {', '.join(rest_days) if rest_days else 'None'}\n"
                f"Sample day:\n{sample_text}\n\n"
                "Do you want to approve this plan and add it to your schedule page?"
            )
        if language == "ar_fusha":
            return (
                f"أعددت لك خطة تمارين لمدة 7 أيام حسب هدفك.\n"
                f"أيام الراحة: {', '.join(rest_days) if rest_days else 'لا يوجد'}\n"
                f"مثال ليوم تدريبي:\n{sample_text}\n\n"
                "هل تريد اعتماد هذه الخطة وإضافتها إلى صفحة الجدول؟"
            )
        return (
            f"جهزتلك خطة تمارين 7 أيام حسب هدفك.\n"
            f"أيام الراحة: {', '.join(rest_days) if rest_days else 'ما في'}\n"
            f"مثال يوم تدريبي:\n{sample_text}\n\n"
            "بدك تعتمد الخطة وتنزل مباشرة بصفحة الجدول؟"
        )

    calories = plan.get("daily_calories", 0)
    meals_count = plan.get("meals_per_day", 4)
    sample_meals = plan.get("days", [{}])[0].get("meals", [])[:3]
    sample_text = "\n".join([f"- {m['name']} ({m['calories']} kcal)" for m in sample_meals])

    if language == "en":
        return (
            f"I prepared a nutrition plan: {calories} kcal/day, {meals_count} meals/day.\n"
            f"Sample meals:\n{sample_text}\n\n"
            "Do you want to approve this plan and add it to your schedule page?"
        )
    if language == "ar_fusha":
        return (
            f"أعددت لك خطة غذائية: {calories} سعرة يوميًا، {meals_count} وجبات يوميًا.\n"
            f"عينة من الوجبات:\n{sample_text}\n\n"
            "هل تريد اعتماد هذه الخطة وإضافتها إلى صفحة الجدول؟"
        )
    return (
        f"جهزتلك خطة أكل: {calories} سعرة باليوم، {meals_count} وجبات باليوم.\n"
        f"عينة وجبات:\n{sample_text}\n\n"
        "بدك تعتمدها وتنزل على صفحة الجدول؟"
    )


def _generate_workout_plan_options(profile: dict[str, Any], language: str, count: int = 5) -> list[dict[str, Any]]:
    variants = [
        {
            "key": "balanced_strength",
            "title": "Balanced Strength Split",
            "title_ar": "خطة قوة متوازنة",
            "focus_cycle": ["legs", "chest", "back", "shoulders", "core"],
            "sets": "4",
            "reps": "8-12",
            "rest_seconds": 90,
            "exercise_count": 5,
        },
        {
            "key": "upper_lower",
            "title": "Upper / Lower Split",
            "title_ar": "خطة علوي وسفلي",
            "focus_cycle": ["chest", "legs", "back", "legs", "shoulders"],
            "sets": "4",
            "reps": "6-10",
            "rest_seconds": 120,
            "exercise_count": 4,
        },
        {
            "key": "hypertrophy_volume",
            "title": "Hypertrophy Volume",
            "title_ar": "خطة تضخيم حجم",
            "focus_cycle": ["chest", "back", "legs", "shoulders", "arms"],
            "sets": "5",
            "reps": "10-15",
            "rest_seconds": 75,
            "exercise_count": 5,
        },
        {
            "key": "fat_loss_circuit",
            "title": "Fat Loss Circuit",
            "title_ar": "خطة حرق دهون دائرية",
            "focus_cycle": ["legs", "core", "back", "chest", "full body"],
            "sets": "3",
            "reps": "12-20",
            "rest_seconds": 45,
            "exercise_count": 6,
        },
        {
            "key": "beginner_foundation",
            "title": "Beginner Foundation",
            "title_ar": "خطة تأسيس للمبتدئ",
            "focus_cycle": ["full body", "legs", "back", "chest", "core"],
            "sets": "3",
            "reps": "10-12",
            "rest_seconds": 75,
            "exercise_count": 4,
        },
        {
            "key": "athletic_performance",
            "title": "Athletic Performance",
            "title_ar": "خطة أداء رياضي",
            "focus_cycle": ["legs", "back", "core", "shoulders", "full body"],
            "sets": "4",
            "reps": "6-10",
            "rest_seconds": 90,
            "exercise_count": 5,
        },
    ]

    if str(profile.get("fitness_level", "")).lower() == "beginner":
        variants = sorted(variants, key=lambda v: 0 if v["key"] == "beginner_foundation" else 1)
    if str(profile.get("goal", "")).lower() == "fat_loss":
        variants = sorted(variants, key=lambda v: 0 if v["key"] == "fat_loss_circuit" else 1)

    selected_variants = variants[: max(1, min(count, len(variants)))]
    rest_days = [d for d in profile.get("rest_days", ["Friday"]) if isinstance(d, str)]
    difficulty = str(profile.get("fitness_level", "beginner")).lower()

    options: list[dict[str, Any]] = []
    for variant in selected_variants:
        plan = _generate_workout_plan(profile, language)
        plan["id"] = f"workout_{uuid.uuid4().hex[:10]}"
        plan["title"] = variant["title"]
        plan["title_ar"] = variant["title_ar"]
        plan["rest_days"] = rest_days
        plan_days: list[dict[str, Any]] = []
        focus_index = 0

        for english_day, arabic_day in WEEK_DAYS:
            if english_day in rest_days:
                plan_days.append({"day": english_day, "dayAr": arabic_day, "focus": "Rest", "exercises": []})
                continue

            focus = variant["focus_cycle"][focus_index % len(variant["focus_cycle"])]
            focus_index += 1
            exercise_items = _select_exercises(focus, difficulty, max_items=int(variant["exercise_count"]))
            exercises = [
                {
                    "name": str(item.get("exercise", "Exercise")),
                    "nameAr": str(item.get("exercise", "Exercise")),
                    "sets": variant["sets"],
                    "reps": variant["reps"],
                    "rest_seconds": int(variant["rest_seconds"]),
                    "notes": str(item.get("description", "")),
                }
                for item in exercise_items
            ]
            plan_days.append({"day": english_day, "dayAr": arabic_day, "focus": focus, "exercises": exercises})

        plan["days"] = plan_days
        plan["variant_key"] = variant["key"]
        options.append(plan)
    return options


def _generate_nutrition_plan_options(profile: dict[str, Any], language: str, count: int = 5) -> list[dict[str, Any]]:
    styles = [
        {"key": "balanced", "title": "Balanced Daily Nutrition", "title_ar": "خطة تغذية متوازنة", "calorie_shift": 0, "protein_mul": 1.00, "carb_mul": 1.00, "fat_mul": 1.00},
        {"key": "high_protein", "title": "High Protein Plan", "title_ar": "خطة بروتين عالي", "calorie_shift": 80, "protein_mul": 1.20, "carb_mul": 0.90, "fat_mul": 0.95},
        {"key": "cutting_lean", "title": "Lean Cutting Plan", "title_ar": "خطة تنشيف", "calorie_shift": -180, "protein_mul": 1.15, "carb_mul": 0.80, "fat_mul": 0.90},
        {"key": "mass_gain", "title": "Mass Gain Plan", "title_ar": "خطة زيادة كتلة", "calorie_shift": 220, "protein_mul": 1.10, "carb_mul": 1.20, "fat_mul": 1.05},
        {"key": "low_gi", "title": "Low GI Plan", "title_ar": "خطة مؤشر سكري منخفض", "calorie_shift": -60, "protein_mul": 1.05, "carb_mul": 0.85, "fat_mul": 1.00},
        {"key": "budget", "title": "Budget Friendly Plan", "title_ar": "خطة اقتصادية", "calorie_shift": 0, "protein_mul": 1.00, "carb_mul": 1.05, "fat_mul": 0.95},
    ]

    goal = str(profile.get("goal", "")).lower()
    if goal == "fat_loss":
        styles = sorted(styles, key=lambda s: 0 if s["key"] == "cutting_lean" else 1)
    elif goal == "muscle_gain":
        styles = sorted(styles, key=lambda s: 0 if s["key"] == "mass_gain" else 1)

    selected_styles = styles[: max(1, min(count, len(styles)))]
    options: list[dict[str, Any]] = []
    for style in selected_styles:
        plan = _generate_nutrition_plan(profile, language)
        plan["id"] = f"nutrition_{uuid.uuid4().hex[:10]}"
        plan["title"] = style["title"]
        plan["title_ar"] = style["title_ar"]
        plan["daily_calories"] = max(1200, int(plan.get("daily_calories", 2000) + style["calorie_shift"]))

        new_days = []
        for day in plan.get("days", []):
            meals = []
            for meal in day.get("meals", []):
                protein = max(5, int(round(float(meal.get("protein", 0)) * style["protein_mul"])))
                carbs = max(5, int(round(float(meal.get("carbs", 0)) * style["carb_mul"])))
                fat = max(3, int(round(float(meal.get("fat", 0)) * style["fat_mul"])))
                calories = int(round((protein * 4) + (carbs * 4) + (fat * 9)))
                meals.append(
                    {
                        **meal,
                        "protein": protein,
                        "carbs": carbs,
                        "fat": fat,
                        "calories": str(calories),
                    }
                )
            new_days.append({**day, "meals": meals})

        plan["days"] = new_days
        plan["variant_key"] = style["key"]
        options.append(plan)
    return options


def _format_plan_options_preview(plan_type: str, options: list[dict[str, Any]], language: str) -> str:
    if not options:
        if language == "en":
            return "I could not generate options right now. Please retry."
        if language == "ar_fusha":
            return "تعذر توليد خيارات الآن. حاول مرة أخرى."
        return "ما قدرت اولّد خيارات هسا. جرّب مرة ثانية."

    lines = []
    for i, plan in enumerate(options, start=1):
        if plan_type == "workout":
            rest_days = ", ".join(plan.get("rest_days", [])) or "None"
            sample_focus = next((d.get("focus") for d in plan.get("days", []) if d.get("exercises")), "general")
            lines.append(f"{i}. {plan.get('title', 'Workout Plan')} | focus: {sample_focus} | rest: {rest_days}")
        else:
            lines.append(
                f"{i}. {plan.get('title', 'Nutrition Plan')} | "
                f"{plan.get('daily_calories', 0)} kcal/day | {plan.get('meals_per_day', 4)} meals/day"
            )

    options_text = "\n".join(lines)
    if language == "en":
        return (
            "I prepared multiple options for you:\n"
            f"{options_text}\n\n"
            "Reply with the option number you want (for example: 1)."
        )
    if language == "ar_fusha":
        return (
            "أعددت لك عدة خيارات:\n"
            f"{options_text}\n\n"
            "أرسل رقم الخيار الذي تريده (مثال: 1)."
        )
    return (
        "جهزتلك كذا خيار:\n"
        f"{options_text}\n\n"
        "ابعت رقم الخيار اللي بدك ياه (مثال: 1)."
    )


def _extract_plan_choice_index(user_input: str, options_count: int) -> int | None:
    if options_count <= 0:
        return None

    number = extract_first_int(user_input)
    if number is not None and 1 <= number <= options_count:
        return number - 1

    normalized = normalize_text(user_input)
    word_to_index = {
        "first": 0,
        "second": 1,
        "third": 2,
        "fourth": 3,
        "fifth": 4,
        "اول": 0,
        "ثاني": 1,
        "ثالث": 2,
        "رابع": 3,
        "خامس": 4,
    }
    for word, idx in word_to_index.items():
        if idx < options_count and fuzzy_contains_any(normalized, {word}):
            return idx
    return None


def _greeting_reply(language: str, profile: Optional[dict[str, Any]] = None) -> str:
    display_name = _profile_display_name(profile or {})
    name_suffix = f" {display_name}" if display_name else ""
    warmup = _motivation_line(language, f"greet-{display_name or 'user'}")
    if language == "en":
        return (
            f"Hi{name_suffix}! {warmup} "
            "I am your AI fitness coach. "
            "I can help with workouts, nutrition plans, and progress tracking."
        )
    if language == "ar_fusha":
        if display_name:
            return (
                f"مرحبًا {display_name}! {warmup} "
                "أنا مدربك الرياضي الذكي. "
                "أساعدك في التمارين والتغذية ومتابعة الالتزام."
            )
        return f"مرحبًا! {warmup} أنا مدربك الرياضي الذكي. أساعدك في التمارين والتغذية ومتابعة الالتزام."
    if display_name:
        return f"هلا {display_name}! {warmup} أنا كوتشك الذكي، وبساعدك بالتمارين والأكل ومتابعة الالتزام."
    return f"هلا! {warmup} أنا كوتشك الذكي، وبساعدك بالتمارين والأكل ومتابعة الالتزام."


def _name_reply(language: str) -> str:
    if language == "en":
        return "I am your AI Fitness Coach specialized in training and nutrition only."
    if language == "ar_fusha":
        return "أنا مدرب اللياقة الذكي الخاص بك، ومتخصص فقط في التدريب والتغذية."
    return "أنا كوتشك الذكي، ومتخصص بس بالتمارين والتغذية."


def _how_are_you_reply(language: str) -> str:
    if language == "en":
        return "I am ready to coach you. Tell me your goal and I will build your plan."
    if language == "ar_fusha":
        return "أنا جاهز لتدريبك. أخبرني بهدفك وسأبني لك خطة مناسبة."
    return "تمام وجاهز أدربك. احكيلي هدفك وببني لك خطة مناسبة."


def _exercise_reply(query: str, language: str) -> str:
    normalized = normalize_text(query)
    mapped_query = query
    muscle_map = {
        "صدر": "chest",
        "ظهر": "back",
        "كتف": "shoulders",
        "اكتاف": "shoulders",
        "ذراع": "arms",
        "باي": "biceps",
        "تراي": "triceps",
        "ارجل": "legs",
        "رجل": "legs",
        "ساق": "legs",
        "بطن": "core",
    }
    for ar_term, en_term in muscle_map.items():
        if ar_term in normalized:
            mapped_query = f"{en_term} workout"
            break

    results = AI_ENGINE.search_exercises(mapped_query, top_k=5)
    if not results:
        if language == "en":
            return "I could not find matching exercises. Rephrase your request and I will try again."
        if language == "ar_fusha":
            return "لم أجد تمارين مطابقة. أعد صياغة طلبك وسأحاول مرة أخرى."
        return "ما لقيت تمارين مطابقة. جرّب صياغة ثانية وبرجع بدور."

    lines = []
    for item in results:
        lines.append(
            f"- {item.get('exercise')} | {item.get('muscle')} | {item.get('difficulty')}\n"
            f"  {item.get('description')}"
        )

    if language == "en":
        suffix = "\nYou can view muscle-specific exercises in the app on: /workouts (3D muscle viewer)."
    elif language == "ar_fusha":
        suffix = "\nيمكنك مشاهدة تمارين كل عضلة داخل التطبيق عبر صفحة: /workouts (المجسم العضلي)."
    else:
        suffix = "\nبتقدر تشوف تمارين كل عضلة داخل التطبيق بصفحة: /workouts (المجسم)."

    return "\n".join(lines) + suffix


def _tracking_reply(language: str, tracking_summary: Optional[dict[str, Any]]) -> str:
    if not tracking_summary:
        if language == "en":
            return (
                f"{_motivation_line(language, 'tracking-empty')} "
                "I do not have your latest tracking snapshot yet. Keep checking tasks in Schedule and I will monitor your adherence."
            )
        if language == "ar_fusha":
            return (
                f"{_motivation_line(language, 'tracking-empty')} "
                "لا أملك حالياً آخر ملخص متابعة لك. استمر بتحديد المهام في صفحة الجدول وسأتابع التزامك."
            )
        return (
            f"{_motivation_line(language, 'tracking-empty')} "
            "لسا ما وصلني آخر ملخص متابعة. ضل علّم المهام بصفحة الجدول وأنا براقب التزامك."
        )

    completed = int(tracking_summary.get("completed_tasks", 0))
    total = int(tracking_summary.get("total_tasks", 0))
    adherence = float(tracking_summary.get("adherence_score", 0))
    adherence_pct = int(round(adherence * 100))

    if language == "en":
        return (
            f"{_motivation_line(language, f'track-{completed}-{total}')} "
            f"Progress update: {completed}/{total} tasks done, adherence {adherence_pct}%.\n"
            "Based on your recent tracking, keep this consistency. If you want, I can adjust your plan intensity for next week."
        )
    if language == "ar_fusha":
        return (
            f"{_motivation_line(language, f'track-{completed}-{total}')} "
            f"تحديث التقدم: أنجزت {completed}/{total} مهمة، ونسبة الالتزام {adherence_pct}%.\n"
            "حسب تقدمك الأسبوع الماضي، استمر على هذا النسق، ويمكنني تعديل شدة الخطة للأسبوع القادم إذا أردت."
        )
    return (
        f"{_motivation_line(language, f'track-{completed}-{total}')} "
        f"تحديث الإنجاز: خلصت {completed}/{total} مهمة، والتزامك {adherence_pct}%.\n"
        "حسب تقدمك الأسبوع الماضي، استمر هيك، وإذا بدك بقدر أعدل شدة الخطة للأسبوع الجاي."
    )


def _general_llm_reply(
    user_message: str,
    language: str,
    profile: dict[str, Any],
    tracking_summary: Optional[dict[str, Any]],
    memory: MemorySystem,
    state: Optional[dict[str, Any]] = None,
    recent_messages: Optional[list[dict[str, Any]]] = None,
) -> str:
    language_instructions = {
        "en": "Reply in clear English.",
        "ar_fusha": "رد باللغة العربية الفصحى.",
        "ar_jordanian": "احكِ باللهجة الأردنية بشكل واضح.",
    }.get(language, "Reply in English.")

    display_name = _profile_display_name(profile)
    state = state or {}
    plan_snapshot = state.get("plan_snapshot", {})
    nutrition_kb_context = _nutrition_kb_context(user_message, profile, top_k=3)

    system_prompt = (
        "You are a professional AI fitness coach.\n"
        "You ONLY answer fitness, training, sports performance, and nutrition topics.\n"
        "If user asks outside this domain, politely refuse and redirect back to fitness.\n"
        "Be warm and supportive, but practical.\n"
        "Personalize responses using user profile fields (name, goal, age, height, weight, health constraints).\n"
        "When nutrition knowledge snippets are provided in context, prioritize them over generic advice.\n"
        "If progress is weak or user reports no body change, ask about sleep, hydration, meal adherence, and workout execution before giving final advice.\n"
        "When user asks about exercises, guide them and mention they can use /workouts for muscle-specific exercise explorer.\n"
        "Keep responses concise but useful.\n"
        f"{language_instructions}\n"
    )

    context_lines = [
        f"User name: {display_name or 'Unknown'}",
        f"User profile: {profile}",
        f"Tracking summary: {tracking_summary or {}}",
        f"Plan snapshot: {plan_snapshot or {}}",
        f"Plans recently deleted flag: {bool(state.get('plans_recently_deleted', False))}",
    ]
    if nutrition_kb_context:
        context_lines.append("Nutrition reference snippets (from DATAFORPROJECT.pdf):")
        context_lines.append(nutrition_kb_context)
    messages = [{"role": "system", "content": system_prompt + '\n'.join(context_lines)}]

    external_history = _normalize_recent_messages(recent_messages)
    if external_history:
        messages.extend(external_history[-10:])
    else:
        messages.extend(memory.get_conversation_history()[-8:])

    last_history_text = normalize_text(messages[-1]["content"]) if len(messages) > 1 else ""
    if last_history_text != normalize_text(user_message):
        messages.append({"role": "user", "content": user_message})
    return LLM.chat_completion(messages, max_tokens=500)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "provider": LLM.active_provider,
        "model": LLM.active_model,
        "nutrition_knowledge_loaded": NUTRITION_KB.ready,
        "nutrition_knowledge_source": str(NUTRITION_KB.data_path),
        "features": [
            "domain_router",
            "moderation",
            "memory",
            "workout_plans",
            "nutrition_plans",
            "nutrition_knowledge",
            "plan_approval",
            "plan_options",
            "multilingual",
        ],
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    user_id = _normalize_user_id(req.user_id)
    conversation_id = _normalize_conversation_id(req.conversation_id, user_id)
    state = _get_user_state(user_id)
    profile = _build_profile(req, state)
    language = _detect_language(req.language or "en", req.message, profile)
    recent_messages = _normalize_recent_messages(req.recent_messages)

    _persist_profile_context(profile, state)
    if req.tracking_summary:
        state["last_progress_summary"] = req.tracking_summary
    _update_plan_snapshot_state(state, req.plan_snapshot)
    tracking_summary = req.tracking_summary or state.get("last_progress_summary")

    user_input = _repair_mojibake(req.message.strip())
    if not user_input:
        return ChatResponse(
            reply="Please send a valid message." if language == "en" else "أرسل رسالة واضحة.",
            conversation_id=conversation_id,
            language=language,
        )

    memory = _get_memory_session(user_id, conversation_id)
    memory.add_user_message(user_input)

    _, has_bad_words = MODERATION.filter_content(user_input, language=language)
    if has_bad_words:
        fallback = MODERATION.get_safe_fallback(language)
        memory.add_assistant_message(fallback)
        return ChatResponse(reply=fallback, conversation_id=conversation_id, language=language)

    lowered = normalize_text(user_input)

    pending_options_payload = state.get("pending_plan_options")
    if pending_options_payload:
        pending_options = pending_options_payload.get("options", [])
        pending_options_type = str(pending_options_payload.get("plan_type", "workout"))
        selected_idx = _extract_plan_choice_index(user_input, len(pending_options))

        if selected_idx is not None:
            selected_plan = deepcopy(pending_options[selected_idx])
            plan_id = selected_plan["id"]
            PENDING_PLANS[plan_id] = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "plan_type": pending_options_type,
                "plan": selected_plan,
                "approved": False,
                "created_at": datetime.utcnow().isoformat(),
            }
            state["last_pending_plan_id"] = plan_id
            state["pending_plan_options"] = None
            state["pending_plan_type"] = None

            reply = _format_plan_preview(pending_options_type, selected_plan, language)
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="ask_plan",
                data={"plan_id": plan_id, "plan_type": pending_options_type, "plan": selected_plan},
            )

        if _contains_any(user_input, PLAN_REFRESH_KEYWORDS):
            profile = _build_profile(req, state)
            if pending_options_type == "nutrition":
                refreshed_options = _generate_nutrition_plan_options(profile, language, count=5)
            else:
                refreshed_options = _generate_workout_plan_options(profile, language, count=5)
            state["pending_plan_options"] = {"plan_type": pending_options_type, "options": refreshed_options}
            reply = _format_plan_options_preview(pending_options_type, refreshed_options, language)
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="choose_plan",
                data={"plan_type": pending_options_type, "options_count": len(refreshed_options)},
            )

        reply = _format_plan_options_preview(pending_options_type, pending_options, language)
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="choose_plan",
            data={"plan_type": pending_options_type, "options_count": len(pending_options)},
        )

    pending_field = state.get("pending_field")
    if pending_field:
        if _apply_profile_answer(pending_field, user_input, state):
            state["pending_field"] = None
            pending_plan_type = state.get("pending_plan_type")
            profile = _build_profile(req, state)
            if pending_plan_type:
                missing = _missing_fields_for_plan(pending_plan_type, profile)
                if missing:
                    state["pending_field"] = missing[0]
                    question = _missing_field_question(missing[0], language)
                    memory.add_assistant_message(question)
                    return ChatResponse(
                        reply=question,
                        conversation_id=conversation_id,
                        language=language,
                        action="ask_profile",
                        data={"missing_field": missing[0], "plan_type": pending_plan_type},
                    )
                if pending_plan_type == "workout":
                    options = _generate_workout_plan_options(profile, language, count=5)
                else:
                    options = _generate_nutrition_plan_options(profile, language, count=5)

                state["pending_plan_options"] = {"plan_type": pending_plan_type, "options": options}
                state["pending_plan_type"] = None
                reply = _format_plan_options_preview(pending_plan_type, options, language)
                memory.add_assistant_message(reply)
                return ChatResponse(
                    reply=reply,
                    conversation_id=conversation_id,
                    language=language,
                    action="choose_plan",
                    data={"plan_type": pending_plan_type, "options_count": len(options)},
                )
        else:
            question = _missing_field_question(pending_field, language)
            memory.add_assistant_message(question)
            return ChatResponse(
                reply=question,
                conversation_id=conversation_id,
                language=language,
                action="ask_profile",
                data={"missing_field": pending_field, "plan_type": state.get("pending_plan_type")},
            )

    pending_diagnostic = state.get("pending_diagnostic")
    pending_diagnostic_conversation_id = state.get("pending_diagnostic_conversation_id")
    if pending_diagnostic and pending_diagnostic_conversation_id and pending_diagnostic_conversation_id != conversation_id:
        pending_diagnostic = None
    if pending_diagnostic and not _contains_any(lowered, PROGRESS_CONCERN_KEYWORDS | TROUBLESHOOT_KEYWORDS):
        diag_in_domain, _ = ROUTER.is_in_domain(user_input, language=language)
        if not diag_in_domain:
            state["pending_diagnostic"] = None
            state["pending_diagnostic_conversation_id"] = None
            out_reply = ROUTER.get_out_of_domain_response(language, query=user_input)
            memory.add_assistant_message(out_reply)
            return ChatResponse(reply=out_reply, conversation_id=conversation_id, language=language)

        if pending_diagnostic == "progress":
            prompt = (
                "The user answered my progress-diagnostic questions. "
                "Analyze likely bottlenecks (sleep, hydration, nutrition adherence, execution) "
                "and give a concrete fix for the next 7 days."
            )
        else:
            prompt = (
                "The user answered my exercise-diagnostic questions. "
                "Identify likely form/load issue, provide corrective cues, safer load adjustment, "
                "and when to stop and seek in-person assessment."
            )
        diagnostic_reply = _general_llm_reply(
            user_message=f"{prompt}\n\nUser answer: {user_input}",
            language=language,
            profile=profile,
            tracking_summary=tracking_summary,
            memory=memory,
            state=state,
            recent_messages=recent_messages,
        )
        state["pending_diagnostic"] = None
        state["pending_diagnostic_conversation_id"] = None
        filtered_diagnostic, _ = MODERATION.filter_content(diagnostic_reply, language=language)
        memory.add_assistant_message(filtered_diagnostic)
        return ChatResponse(reply=filtered_diagnostic, conversation_id=conversation_id, language=language)

    if _is_greeting_query(user_input):
        reply = _greeting_reply(language, profile)
        memory.add_assistant_message(reply)
        return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

    if _is_name_query(user_input):
        reply = _name_reply(language)
        memory.add_assistant_message(reply)
        return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

    if _is_how_are_you_query(user_input):
        reply = _how_are_you_reply(language)
        memory.add_assistant_message(reply)
        return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

    latest_plan_id = state.get("last_pending_plan_id")
    if latest_plan_id and latest_plan_id in PENDING_PLANS:
        if _contains_any(lowered, APPROVE_KEYWORDS):
            plan_record = PENDING_PLANS[latest_plan_id]
            plan_record["approved"] = True
            state["last_pending_plan_id"] = None
            if language == "en":
                reply = "Plan approved. I added it for your schedule flow. You can track completion daily."
            elif language == "ar_fusha":
                reply = "تم اعتماد الخطة. يمكنك الآن متابعتها يوميًا داخل صفحة الجدول."
            else:
                reply = "تم اعتماد الخطة. هلا بتقدر تتابعها يوم بيوم بصفحة الجدول."
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="plan_approved",
                data={
                    "plan_id": latest_plan_id,
                    "approved_plan": {
                        "type": plan_record["plan_type"],
                        "plan": plan_record["plan"],
                    },
                },
            )
        if _contains_any(lowered, REJECT_KEYWORDS):
            state["last_pending_plan_id"] = None
            if language == "en":
                reply = "No problem. I canceled this draft. Tell me what to change and I will regenerate it."
            elif language == "ar_fusha":
                reply = "لا مشكلة. ألغيت هذه المسودة. أخبرني ما الذي تريد تغييره وسأعيد التوليد."
            else:
                reply = "تمام، لغيت المسودة. احكيلي شو بدك أغير وبرجع ببنيها."
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="plan_rejected",
                data={"plan_id": latest_plan_id},
            )

    social_reply = _social_reply(user_input, language, profile)
    if social_reply:
        memory.add_assistant_message(social_reply)
        return ChatResponse(reply=social_reply, conversation_id=conversation_id, language=language)

    profile_reply = _profile_query_reply(user_input, language, profile, tracking_summary)
    if profile_reply:
        memory.add_assistant_message(profile_reply)
        return ChatResponse(reply=profile_reply, conversation_id=conversation_id, language=language)

    if _contains_any(lowered, PLAN_STATUS_KEYWORDS):
        status_reply = _plan_status_reply(language, state.get("plan_snapshot"))
        memory.add_assistant_message(status_reply)
        return ChatResponse(reply=status_reply, conversation_id=conversation_id, language=language)

    if _contains_any(lowered, PROGRESS_CONCERN_KEYWORDS):
        state["pending_diagnostic"] = "progress"
        state["pending_diagnostic_conversation_id"] = conversation_id
        response = _progress_diagnostic_reply(language, profile, tracking_summary)
        memory.add_assistant_message(response)
        return ChatResponse(reply=response, conversation_id=conversation_id, language=language)

    if _contains_any(lowered, TROUBLESHOOT_KEYWORDS):
        state["pending_diagnostic"] = "exercise"
        state["pending_diagnostic_conversation_id"] = conversation_id
        response = _exercise_diagnostic_reply(language)
        memory.add_assistant_message(response)
        return ChatResponse(reply=response, conversation_id=conversation_id, language=language)

    in_domain, _score = ROUTER.is_in_domain(user_input, language=language)
    if not in_domain:
        out_reply = ROUTER.get_out_of_domain_response(language, query=user_input)
        memory.add_assistant_message(out_reply)
        return ChatResponse(reply=out_reply, conversation_id=conversation_id, language=language)

    if _is_workout_plan_request(user_input):
        state["pending_plan_type"] = "workout"
        profile = _build_profile(req, state)
        missing = _missing_fields_for_plan("workout", profile)
        if missing:
            state["pending_field"] = missing[0]
            question = _missing_field_question(missing[0], language)
            memory.add_assistant_message(question)
            return ChatResponse(
                reply=question,
                conversation_id=conversation_id,
                language=language,
                action="ask_profile",
                data={"missing_field": missing[0], "plan_type": "workout"},
            )

        options = _generate_workout_plan_options(profile, language, count=5)
        state["pending_plan_options"] = {"plan_type": "workout", "options": options}
        state["pending_plan_type"] = None
        reply = _format_plan_options_preview("workout", options, language)
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="choose_plan",
            data={"plan_type": "workout", "options_count": len(options)},
        )

    if _is_nutrition_plan_request(user_input):
        state["pending_plan_type"] = "nutrition"
        profile = _build_profile(req, state)
        missing = _missing_fields_for_plan("nutrition", profile)
        if missing:
            state["pending_field"] = missing[0]
            question = _missing_field_question(missing[0], language)
            memory.add_assistant_message(question)
            return ChatResponse(
                reply=question,
                conversation_id=conversation_id,
                language=language,
                action="ask_profile",
                data={"missing_field": missing[0], "plan_type": "nutrition"},
            )

        options = _generate_nutrition_plan_options(profile, language, count=5)
        state["pending_plan_options"] = {"plan_type": "nutrition", "options": options}
        state["pending_plan_type"] = None
        reply = _format_plan_options_preview("nutrition", options, language)
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="choose_plan",
            data={"plan_type": "nutrition", "options_count": len(options)},
        )

    if _contains_any(lowered, PROGRESS_KEYWORDS):
        reply = _tracking_reply(language, tracking_summary)
        memory.add_assistant_message(reply)
        return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

    if _contains_any(
        user_input,
        {
            "exercise",
            "exercises",
            "muscle",
            "workout",
            "train",
            "تمرين",
            "تمارين",
            "اتمرن",
            "تمرن",
            "كيفية التمرين",
            "عضلة",
            "عضلات",
            "الصدر",
            "الظهر",
            "الكتف",
            "الأكتاف",
            "الأرجل",
            "الرجل",
            "الساق",
            "البطن",
        },
    ):
        reply = _exercise_reply(user_input, language)
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="exercise_results",
            data={"redirect_to": "/workouts"},
        )

    llm_reply = _general_llm_reply(
        user_message=user_input,
        language=language,
        profile=profile,
        tracking_summary=tracking_summary,
        memory=memory,
        state=state,
        recent_messages=recent_messages,
    )
    if llm_reply.startswith("Ollama error:"):
        llm_reply = _lang_reply(
            language,
            "Local AI model is temporarily unavailable. Please make sure Ollama is running, then try again.",
            "نموذج الذكاء المحلي غير متاح مؤقتًا. تأكد من تشغيل Ollama ثم أعد المحاولة.",
            "نموذج الذكاء المحلي واقف مؤقتًا. شغّل Ollama وارجع جرّب.",
        )
    filtered_reply, _ = MODERATION.filter_content(llm_reply, language=language)
    memory.add_assistant_message(filtered_reply)
    return ChatResponse(reply=filtered_reply, conversation_id=conversation_id, language=language)


@app.post("/plans/{plan_id}/approve")
def approve_plan(plan_id: str, req: PlanActionRequest | None = None) -> dict[str, Any]:
    record = PENDING_PLANS.get(plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Plan not found")

    if req and req.user_id and record["user_id"] != req.user_id:
        raise HTTPException(status_code=403, detail="Not allowed to approve this plan")

    record["approved"] = True
    return {
        "status": "approved",
        "plan_id": plan_id,
        "approved_plan": {
            "type": record["plan_type"],
            "plan": record["plan"],
        },
        "message": "Plan approved successfully.",
    }


@app.post("/plans/{plan_id}/reject")
def reject_plan(plan_id: str, req: PlanActionRequest | None = None) -> dict[str, Any]:
    record = PENDING_PLANS.get(plan_id)
    if not record:
        raise HTTPException(status_code=404, detail="Plan not found")

    if req and req.user_id and record["user_id"] != req.user_id:
        raise HTTPException(status_code=403, detail="Not allowed to reject this plan")

    record["approved"] = False
    return {"status": "rejected", "plan_id": plan_id}


@app.get("/conversation/{conversation_id}")
def get_conversation_history(conversation_id: str, user_id: Optional[str] = None) -> dict[str, Any]:
    uid = _normalize_user_id(user_id)
    key = _session_key(uid, _normalize_conversation_id(conversation_id, uid))
    memory = MEMORY_SESSIONS.get(key)
    return {
        "conversation_id": conversation_id,
        "user_id": uid,
        "messages": memory.short_term.get_full_history() if memory else [],
    }


@app.post("/conversation/{conversation_id}/clear")
def clear_conversation(conversation_id: str, user_id: Optional[str] = None) -> dict[str, Any]:
    uid = _normalize_user_id(user_id)
    key = _session_key(uid, _normalize_conversation_id(conversation_id, uid))
    if key in MEMORY_SESSIONS:
        MEMORY_SESSIONS[key].clear_short_term()
    return {"status": "cleared", "conversation_id": conversation_id}


@app.get("/progress/{user_id}")
def get_progress(user_id: str) -> dict[str, Any]:
    state = _get_user_state(_normalize_user_id(user_id))
    return {
        "user_id": user_id,
        "date": datetime.utcnow().isoformat(),
        "summary": state.get("last_progress_summary", {}),
    }



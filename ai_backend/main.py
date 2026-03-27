from __future__ import annotations

import os
import threading
import logging
import re
import json
import uuid
import shutil
from functools import lru_cache
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from ai_engine import AIEngine
from domain_router import DomainRouter
from dataset_registry import DatasetRegistry
from knowledge_engine import KnowledgeEngine
from llm_client import LLMClient
from logic_engine import evaluate_logic_metrics
from memory_system import MemorySystem
from moderation_layer import ModerationLayer
from predict import predict_goal, predict_plan_intent, predict_success
from response_datasets import ResponseDatasets
from data_catalog import DataCatalog
from dataset_paths import resolve_dataset_root, resolve_derived_root
from rag_context import RagContextBuilder
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag_faiss import RagService
from voice.stt import WhisperSTT
from voice.tts import LocalTTS
from voice.voice_pipeline import VoicePipeline, VoicePipelineError, VoicePipelineResult
from coach_memory_store import get_coach_memory, upsert_coach_memory, summarize_memory
from db import get_supabase_client
from analytics_engine import compute_stats, generate_insights, dashboard_summary
from feedback_store import get_feedback_summary, record_plan_feedback
from intelligent_router import IntelligentRouter
from modes import CHAT_MODE, PLAN_MODE, ANALYTICS_MODE, MOTIVATION_MODE
from plan_scoring import rank_plans
from prompt_builder import build_system_prompt
from response_postprocessor import post_process_response
from safety_system import filter_workout_plan, filter_nutrition_plan, detect_overtraining
from nlp_utils import (
    extract_first_int,
    fuzzy_contains_any,
    normalize_text,
    repair_mojibake as nlp_repair_mojibake,
    repair_mojibake_deep,
)
from routers import users_router, plans_router, analytics_router, ai_router, admin_router


app = FastAPI(title="AI Fitness Coach Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production-grade modular routers
app.include_router(users_router)
app.include_router(plans_router)
app.include_router(analytics_router)
app.include_router(ai_router)
app.include_router(admin_router)

logger = logging.getLogger(__name__)

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
STATIC_DIR = BACKEND_DIR / "static"
STATIC_AUDIO_DIR = STATIC_DIR / "audio"
STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize Multi-Dataset Training Pipeline
training_pipeline = None
RAG_SERVICE: Any = None
TRAINING_PIPELINE_STATUS = {"state": "idle", "error": None}
RAG_STATUS = {"state": "idle", "error": None}

def _training_pipeline_worker():
    """Background worker to initialize training pipeline without blocking startup."""
    global training_pipeline, TRAINING_PIPELINE_STATUS
    TRAINING_PIPELINE_STATUS["state"] = "loading"
    TRAINING_PIPELINE_STATUS["error"] = None
    try:
        from training_pipeline import TrainingPipeline
        from dataset_paths import resolve_dataset_root

        logger.info("Initializing multi-dataset training pipeline (background)...")
        dataset_root = resolve_dataset_root()
        model_cache_path = BACKEND_DIR / "models" / "training_cache"

        pipeline = TrainingPipeline(dataset_root, model_cache_path)
        if pipeline.load_cached_models():
            logger.info("✅ Loaded cached training models")
            training_pipeline = pipeline
            TRAINING_PIPELINE_STATUS["state"] = "ready"
        else:
            auto_train = os.getenv("TRAINING_PIPELINE_AUTO_TRAIN", "0").lower() in {"1", "true", "yes"}
            if auto_train:
                logger.info("Training on 50+ datasets... this may take some time")
                pipeline.train()
                training_pipeline = pipeline
                TRAINING_PIPELINE_STATUS["state"] = "ready"
                logger.info("✅ Training complete! Models cached for next startup")
            else:
                TRAINING_PIPELINE_STATUS["state"] = "needs_training"
                logger.warning(
                    "Training cache not found. Skipping auto-train. "
                    "Set TRAINING_PIPELINE_AUTO_TRAIN=1 to train at startup."
                )
        summary = pipeline.get_summary()
        logger.info("📊 Training Pipeline Ready: datasets=%s records=%s",
                    summary["dataset_summary"]["total_datasets"],
                    summary["dataset_summary"]["total_records"])
    except Exception as e:
        TRAINING_PIPELINE_STATUS["state"] = "failed"
        TRAINING_PIPELINE_STATUS["error"] = str(e)
        logger.warning(f"⚠️ Training pipeline initialization failed: {e}")
        training_pipeline = None


@app.on_event("startup")
async def initialize_training_pipeline():
    """Kick off training pipeline in the background to avoid blocking startup."""
    if os.getenv("TRAINING_PIPELINE_ENABLED", "1").lower() in {"0", "false", "no", "off"}:
        logger.info("Training pipeline disabled by TRAINING_PIPELINE_ENABLED")
        return
    threading.Thread(target=_training_pipeline_worker, daemon=True).start()


def _rag_worker():
    global RAG_SERVICE, RAG_STATUS
    RAG_STATUS["state"] = "loading"
    RAG_STATUS["error"] = None
    try:
        from rag_faiss import RagService
        force_rebuild = os.getenv("RAG_FORCE_REBUILD", "0").lower() in {"1", "true", "yes"}
        index_dir = BACKEND_DIR / "models" / "rag"
        RAG_SERVICE = RagService.build_default(
            dataset_dir=_resolve_response_dataset_dir(),
            knowledge_path=Path(__file__).resolve().parent / "knowledge" / "dataforproject.txt",
            index_dir=index_dir,
            force_rebuild=force_rebuild,
        )
        if RAG_SERVICE.index.ready:
            logger.info("✅ RAG index ready (FAISS)")
            RAG_STATUS["state"] = "ready"
        else:
            logger.warning("⚠️ RAG index not ready (empty or missing docs)")
            RAG_STATUS["state"] = "empty"
    except Exception as exc:
        logger.warning(f"⚠️ RAG index initialization failed: {exc}")
        RAG_SERVICE = None
        RAG_STATUS["state"] = "failed"
        RAG_STATUS["error"] = str(exc)


@app.on_event("startup")
async def initialize_rag_index():
    """Initialize FAISS RAG index in the background to avoid blocking startup."""
    if os.getenv("RAG_ENABLED", "1").lower() in {"0", "false", "no", "off"}:
        logger.info("RAG index disabled by RAG_ENABLED")
        return
    threading.Thread(target=_rag_worker, daemon=True).start()


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


class VoiceChatResponse(BaseModel):
    transcript: str
    reply: str
    audio_path: str
    conversation_id: str
    language: str


class PlanActionRequest(BaseModel):
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


class GoalPredictionRequest(BaseModel):
    age: Optional[float] = 0.0
    gender: Optional[str] = "Other"
    weight_kg: Optional[float] = 0.0
    height_m: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = 0.0
    fat_percentage: Optional[float] = 0.0
    workout_frequency_days_week: Optional[float] = 0.0
    experience_level: Optional[float] = 0.0
    calories_burned: Optional[float] = 0.0
    avg_bpm: Optional[float] = 0.0


class SuccessPredictionRequest(BaseModel):
    age: Optional[float] = 0.0
    gender: Optional[str] = "Other"
    membership_type: Optional[str] = "Unknown"
    workout_type: Optional[str] = "Unknown"
    workout_duration_minutes: Optional[float] = 0.0
    calories_burned: Optional[float] = 0.0
    check_in_hour: Optional[int] = 0
    check_in_time: Optional[str] = None


class LogicEvaluationRequest(BaseModel):
    start_value: Optional[float] = None
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    direction: str = "decrease"
    weight_history: Optional[list[float]] = None
    previous_value: Optional[float] = None
    elapsed_weeks: float = 1.0


class PlanIntentPredictionRequest(BaseModel):
    message: str


def _resolve_response_dataset_dir() -> Path:
    base_data_dir = Path(__file__).resolve().parent / "data"
    candidates = [
        base_data_dir / "week2",
        base_data_dir / "chat data",
    ]
    required_files = ("conversation_intents.json", "workout_programs.json", "nutrition_programs.json")
    for candidate in candidates:
        if all((candidate / name).exists() for name in required_files):
            return candidate
    return candidates[0]


ROUTER = DomainRouter(threshold=0.42, enable_semantic=False)
MODERATION = ModerationLayer()
LLM = LLMClient()
AI_ENGINE = AIEngine(Path(__file__).resolve().parent / "exercises.json")
NUTRITION_KB = KnowledgeEngine(Path(__file__).resolve().parent / "knowledge" / "dataforproject.txt")
RESPONSE_DATASET_DIR = _resolve_response_dataset_dir()
RESPONSE_DATASETS = ResponseDatasets(RESPONSE_DATASET_DIR)
CHAT_RESPONSE_MODE = os.getenv('CHAT_RESPONSE_MODE', 'hybrid').strip().lower()
FORCE_LLM_RESPONSE = os.getenv("FORCE_LLM_RESPONSE", "0").strip().lower() in {"1", "true", "yes", "on"}
SUPABASE_CONTEXT_CACHE_SECONDS = max(5, int(os.getenv("SUPABASE_CONTEXT_CACHE_SECONDS", "25")))
CHAT_LLM_MAX_TOKENS = max(80, int(os.getenv("CHAT_LLM_MAX_TOKENS", "90")))
VOICE_STT = WhisperSTT(model_name=os.getenv("WHISPER_MODEL", "openai/whisper-base"))
VOICE_TTS = LocalTTS(output_dir=STATIC_AUDIO_DIR)
VOICE_PIPELINE = VoicePipeline(stt_engine=VOICE_STT, tts_engine=VOICE_TTS, llm_client=LLM)
DATASET_REGISTRY = DatasetRegistry(
    resolve_dataset_root(),
    Path(__file__).resolve().parent / "data" / "dataset_registry_index.json",
)
try:
    # Avoid blocking startup with full rebuild; use cached index if present.
    DATASET_REGISTRY.build_index(force_rebuild=False)
except Exception as exc:
    logger.warning("Dataset registry build failed: %s", exc)
CATALOG: DataCatalog | None = None
RAG_BUILDER: RagContextBuilder | None = None


def _get_catalog() -> DataCatalog:
    global CATALOG
    if CATALOG is None:
        CATALOG = DataCatalog(resolve_dataset_root(), resolve_derived_root())
    return CATALOG


def _get_rag_builder() -> RagContextBuilder:
    global RAG_BUILDER
    if RAG_BUILDER is None:
        RAG_BUILDER = RagContextBuilder(_get_catalog())
    return RAG_BUILDER
SMART_ROUTER = IntelligentRouter()

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
PERFORMANCE_ANALYSIS_KEYWORDS = {
    "performance",
    "weekly performance",
    "monthly performance",
    "performance analysis",
    "rate of progress",
    "on track",
    "ahead of schedule",
    "behind schedule",
    "weeks remaining",
    "timeline",
    "remaining time",
    "time to goal",
    "remaining weeks",
    "progress percentage",
    "how am i progressing",
    "تحليل الأداء",
    "تحليل الاداء",
    "اداء",
    "أداء",
    "اسبوعي",
    "أسبوعي",
    "شهري",
    "تحليل التقدم",
    "على المسار",
    "متقدم",
    "متأخر",
    "كم أسبوع",
    "كم اسبوع",
    "قديش ضايل",
    "كم ضايل",
    "ضايلي",
    "ضايل",
    "ضايل لهدفي",
    "كم ضايلي",
    "قديش ضايلي",
    "قديش ضل",
    "كيف تقدمي",
    "قديش تقدمي",
    "وين وصلت",
    "شو نسبة التقدم",
    "نسبة التقدم"
}
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
    
}
PLAN_REFRESH_KEYWORDS = {"more options", "another options", "Ø®ÙŠØ§Ø±Ø§Øª Ø§ÙƒØ«Ø±", "Ø®ÙŠØ§Ø±Ø§Øª Ø£Ø®Ø±Ù‰", "ØºÙŠØ±Ù‡Ù…"}
APPROVE_KEYWORDS = APPROVE_KEYWORDS | {"accept", "okay", "ok", "Ù…Ø§Ø´ÙŠ"}
REJECT_KEYWORDS = REJECT_KEYWORDS | {"decline", "cancel"}
WORKOUT_PLAN_KEYWORDS = WORKOUT_PLAN_KEYWORDS | {"workout", "training", "routine", "\u062a\u0645\u0627\u0631\u064a\u0646", "\u0628\u0631\u0646\u0627\u0645\u062c"}
NUTRITION_PLAN_KEYWORDS = NUTRITION_PLAN_KEYWORDS | {"nutrition", "diet", "meal", "\u062a\u063a\u0630\u064a\u0629", "\u0648\u062c\u0628\u0627\u062a"}


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
    "\u062e\u0637\u0647 \u062a\u0645\u0627\u0631\u064a\u0646",
    "\u0628\u062f\u064a \u062e\u0637\u0629 \u062a\u0645\u0627\u0631\u064a\u0646",
    "\u0627\u0639\u0637\u064a\u0646\u064a \u062e\u0637\u0629 \u062a\u0645\u0627\u0631\u064a\u0646",
    "\u0627\u0628\u063a\u0649 \u062e\u0637\u0629 \u062a\u0645\u0627\u0631\u064a\u0646",
    "\u062e\u0637\u0629 \u062a\u062f\u0631\u064a\u0628",
    "\u0628\u0631\u0646\u0627\u0645\u062c \u062a\u062f\u0631\u064a\u0628\u064a",
    "\u062c\u062f\u0648\u0644 \u062a\u062f\u0631\u064a\u0628",
    "\u0628\u062f\u064a \u062e\u0637\u0629",
    "\u0628\u062f\u064a \u0628\u0631\u0646\u0627\u0645\u062c",
    "\u0627\u0639\u0637\u064a\u0646\u064a \u0628\u0631\u0646\u0627\u0645\u062c",
    "\u0627\u0628\u063a\u0649 \u0628\u0631\u0646\u0627\u0645\u062c",
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
    "strength",
    "hypertrophy",
    "progressive overload",
    "overload",
    "sets",
    "reps",
    "rest time",
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
    "\u0642\u0648\u0629",
    "\u0636\u062e\u0627\u0645\u0629",
    "\u062d\u0645\u0644 \u062a\u062f\u0631\u064a\u062c\u064a",
    "\u0627\u0648\u0641\u0631\u0644\u0648\u062f",
    "\u0645\u062c\u0645\u0648\u0639\u0627\u062a",
    "\u062a\u0643\u0631\u0627\u0631\u0627\u062a",
    "\u063a\u0630\u0627\u0621",
    "\u062a\u063a\u0630\u064a\u0629",
    "\u0648\u062c\u0628\u0627\u062a",
    "\u0633\u0639\u0631\u0627\u062a",
    "\u0628\u0631\u0648\u062a\u064a\u0646",
    "\u0644\u064a\u0627\u0642\u0629",
}

ML_GOAL_QUERY_KEYWORDS = {
    "predict goal",
    "goal prediction",
    "predict my goal",
    "best goal for me",
    "recommended goal",
    "what goal suits me",
    "توقع الهدف",
    "تنبؤ الهدف",
    "شو الهدف المناسب",
    "اي هدف مناسب",
    "ما الهدف المناسب",
    "توقع هدفي",
}

ML_SUCCESS_QUERY_KEYWORDS = {
    "success prediction",
    "predict success",
    "success probability",
    "chance of success",
    "will i succeed",
    "am i likely to succeed",
    "نسبة النجاح",
    "احتمال النجاح",
    "توقع النجاح",
    "هل رح انجح",
    "هل سأنجح",
    "هل رح ألتزم",
    "هل سانجح",
}

ML_GENERAL_PREDICTION_KEYWORDS = {
    "predict",
    "prediction",
    "ai prediction",
    "model prediction",
    "توقع",
    "تنبؤ",
    "توقعي",
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
ML_GOAL_QUERY_KEYWORDS = _expand_keyword_set_with_repair(ML_GOAL_QUERY_KEYWORDS)
ML_SUCCESS_QUERY_KEYWORDS = _expand_keyword_set_with_repair(ML_SUCCESS_QUERY_KEYWORDS)
ML_GENERAL_PREDICTION_KEYWORDS = _expand_keyword_set_with_repair(ML_GENERAL_PREDICTION_KEYWORDS)

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


def _load_coach_memory(user_id: str, state: dict[str, Any]) -> Optional[dict[str, Any]]:
    cached = state.get("coach_memory")
    if cached is not None:
        return cached
    memory = get_coach_memory(user_id)
    if memory:
        state["coach_memory"] = memory
    return memory


def _build_coach_memory_update(profile: dict[str, Any], tracking_summary: Optional[dict[str, Any]]) -> dict[str, Any]:
    tracking_summary = tracking_summary if isinstance(tracking_summary, dict) else {}
    weekly_stats = tracking_summary.get("weekly_stats") if isinstance(tracking_summary.get("weekly_stats"), dict) else {}
    monthly_stats = tracking_summary.get("monthly_stats") if isinstance(tracking_summary.get("monthly_stats"), dict) else {}

    workouts_week = _to_float(_dict_get_any(weekly_stats, ["workout_days", "completed_workouts", "sessions"]))
    streak_days = _to_float(_dict_get_any(tracking_summary, ["streak_days", "current_streak", "streak"]))
    calories_burned = _to_float(
        _dict_get_any(weekly_stats, ["calories_burned", "avg_calories_burned", "calories_burned_avg"])
    )
    if calories_burned is None:
        calories_burned = _to_float(_dict_get_any(monthly_stats, ["avg_calories_burned", "calories_burned"]))

    goal = profile.get("goal")
    speaking_style = profile.get("speaking_style") or profile.get("speakingStyle")
    injuries = profile.get("injuries")
    allergies = profile.get("allergies")
    chronic = profile.get("chronic_diseases") or profile.get("chronicConditions")
    dietary = profile.get("dietary_preferences") or profile.get("dietaryPreferences")
    equipment = profile.get("equipment") or profile.get("available_equipment")
    fitness_level = profile.get("fitness_level")
    training_days = profile.get("training_days_per_week")

    update = {
        "goals": {"primary": goal} if goal else {},
        "speaking_style": speaking_style or {},
        "preferences": {
            "injuries": injuries or [],
            "allergies": allergies or [],
            "chronic_conditions": chronic or [],
            "dietary_preferences": dietary or [],
            "equipment": equipment or "",
            "fitness_level": fitness_level or "",
            "training_days_per_week": training_days or None,
        },
        "exercise_history": {
            "workouts_per_week": int(workouts_week) if workouts_week is not None else None,
            "streak_days": int(streak_days) if streak_days is not None else None,
            "calories_burned": int(calories_burned) if calories_burned is not None else None,
            "last_completed_at": tracking_summary.get("last_completed_at"),
        },
    }
    return update


def _persist_coach_memory(user_id: str, updates: dict[str, Any], state: dict[str, Any]) -> None:
    if not user_id or not updates:
        return
    stored = upsert_coach_memory(user_id, updates)
    if stored:
        state["coach_memory"] = stored


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _completion_date_from_row(row: dict[str, Any]) -> Optional[date]:
    if not isinstance(row, dict):
        return None
    for key in ("log_date", "completed_at", "created_at"):
        parsed = _parse_iso_datetime(row.get(key))
        if parsed is not None:
            return parsed.date()
    return None


def _compute_streak_days(days: set[date]) -> int:
    if not days:
        return 0
    ordered = sorted(days, reverse=True)
    streak = 1
    prev = ordered[0]
    for current in ordered[1:]:
        if (prev - current) == timedelta(days=1):
            streak += 1
            prev = current
            continue
        break
    return streak


def _count_tasks_from_plan_data(plan_data: Any) -> int:
    total = 0

    def _consume_days(days_payload: Any) -> None:
        nonlocal total
        if not isinstance(days_payload, list):
            return
        for day in days_payload:
            if not isinstance(day, dict):
                continue
            exercises = day.get("exercises")
            meals = day.get("meals")
            if isinstance(exercises, list):
                total += len(exercises)
            if isinstance(meals, list):
                total += len(meals)

    if isinstance(plan_data, list):
        _consume_days(plan_data)
        return total

    if isinstance(plan_data, dict):
        _consume_days(plan_data.get("days"))
        weekly_schedule = plan_data.get("weekly_schedule")
        if isinstance(weekly_schedule, dict):
            for payload in weekly_schedule.values():
                if isinstance(payload, list):
                    total += len(payload)
                elif isinstance(payload, dict):
                    exercises = payload.get("exercises")
                    if isinstance(exercises, list):
                        total += len(exercises)
        nutrition_days = plan_data.get("nutrition_days")
        if isinstance(nutrition_days, list):
            for day in nutrition_days:
                if isinstance(day, dict) and isinstance(day.get("meals"), list):
                    total += len(day.get("meals"))
    return total


def _is_nutrition_plan_row(row: dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    title = str(row.get("title") or "").strip().lower()
    if title.startswith("nutrition::") or "nutrition" in title or "meal" in title or "diet" in title:
        return True
    title_ar = normalize_text(str(row.get("title_ar") or ""))
    if any(token in title_ar for token in {"تغذية", "غذائية", "وجبات", "دايت"}):
        return True
    plan_data = row.get("plan_data")
    if isinstance(plan_data, list):
        has_meals = any(isinstance(day, dict) and isinstance(day.get("meals"), list) and day.get("meals") for day in plan_data)
        has_exercises = any(
            isinstance(day, dict) and isinstance(day.get("exercises"), list) and day.get("exercises")
            for day in plan_data
        )
        if has_meals and not has_exercises:
            return True
    return False


def _build_profile_payload_from_db(user_id: str, row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    payload = {
        "id": user_id,
        "user_id": user_id,
        "name": row.get("name"),
        "age": row.get("age"),
        "gender": row.get("gender"),
        "weight": row.get("weight"),
        "height": row.get("height"),
        "goal": row.get("goal"),
        "location": row.get("location"),
        "fitnessLevel": row.get("fitness_level"),
        "trainingDaysPerWeek": row.get("training_days_per_week"),
        "equipment": row.get("equipment") or "",
        "injuries": row.get("injuries") or "",
        "activityLevel": row.get("activity_level"),
        "dietaryPreferences": row.get("dietary_preferences") or "",
        "chronicConditions": row.get("chronic_conditions") or "",
        "allergies": row.get("allergies") or "",
        "speakingStyle": row.get("speaking_style"),
        "preferred_language": row.get("preferred_language"),
        "fitness_level": row.get("fitness_level"),
        "training_days_per_week": row.get("training_days_per_week"),
        "available_equipment": row.get("equipment") or "",
        "activity_level": row.get("activity_level"),
        "dietary_preferences": row.get("dietary_preferences") or "",
        "chronic_diseases": row.get("chronic_conditions") or "",
        "speaking_style": row.get("speaking_style"),
    }
    return {k: v for k, v in payload.items() if v not in (None, "", [], {})}


def _build_profile_payload_from_user_profiles(user_id: str, row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    payload = {
        "id": user_id,
        "user_id": user_id,
        "name": row.get("full_name"),
        "age": row.get("age"),
        "gender": row.get("gender"),
        "weight": row.get("weight_kg"),
        "height": row.get("height_cm"),
        "goal": row.get("goal_primary"),
        "fitnessLevel": row.get("fitness_level"),
        "fitness_level": row.get("fitness_level"),
        "preferred_language": row.get("locale"),
    }
    return {k: v for k, v in payload.items() if v not in (None, "", [], {})}


def _merge_missing_profile_fields(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(base, dict):
        base = {}
    if not isinstance(extra, dict):
        return base
    merged = dict(base)
    for key, value in extra.items():
        if value in (None, "", [], {}):
            continue
        if key not in merged or merged.get(key) in (None, "", [], {}):
            merged[key] = value
    return merged


def _get_supabase_user_context(user_id: str, state: dict[str, Any]) -> dict[str, Any]:
    if not user_id or user_id == "anonymous":
        return {}

    now_ts = datetime.utcnow().timestamp()
    cached = state.get("supabase_context_cache")
    if isinstance(cached, dict):
        cached_at = cached.get("cached_at")
        if isinstance(cached_at, (int, float)) and now_ts - float(cached_at) < SUPABASE_CONTEXT_CACHE_SECONDS:
            return cached.get("data") or {}

    sb = get_supabase_client()
    if not sb:
        return {}

    profile_row: dict[str, Any] | None = None
    normalized_profile_row: dict[str, Any] | None = None
    preferences_row: dict[str, Any] | None = None
    active_plan_rows: list[dict[str, Any]] = []
    active_nutrition_rows: list[dict[str, Any]] = []
    completion_rows: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []
    condition_names: list[str] = []
    allergy_names: list[str] = []

    try:
        profile_resp = (
            sb.table("profiles")
            .select(
                "name,age,gender,weight,height,goal,location,fitness_level,training_days_per_week,"
                "equipment,injuries,activity_level,dietary_preferences,chronic_conditions,allergies,"
                "speaking_style,preferred_language"
            )
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        profile_data = profile_resp.data or []
        if profile_data:
            profile_row = profile_data[0]
    except Exception as exc:
        logger.debug("Supabase profiles fetch failed: %s", exc)

    try:
        normalized_profile_resp = (
            sb.table("user_profiles")
            .select("full_name,gender,height_cm,weight_kg,fitness_level,goal_primary,locale")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        normalized_data = normalized_profile_resp.data or []
        if normalized_data:
            normalized_profile_row = normalized_data[0]
    except Exception:
        normalized_profile_row = None

    try:
        preferences_resp = (
            sb.table("user_preferences")
            .select("diet_style,equipment_available")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        pref_data = preferences_resp.data or []
        if pref_data:
            preferences_row = pref_data[0]
    except Exception:
        preferences_row = None

    try:
        condition_rows = (
            sb.table("user_conditions")
            .select("condition_id")
            .eq("user_id", user_id)
            .execute()
        ).data or []
        condition_ids = [row.get("condition_id") for row in condition_rows if isinstance(row, dict) and row.get("condition_id")]
        if condition_ids:
            conditions_ref = (
                sb.table("health_conditions")
                .select("id,name")
                .in_("id", condition_ids)
                .execute()
            ).data or []
            condition_names = [str(row.get("name")).strip() for row in conditions_ref if isinstance(row, dict) and str(row.get("name") or "").strip()]
    except Exception:
        condition_names = []

    try:
        allergy_rows = (
            sb.table("user_allergies")
            .select("allergen_id")
            .eq("user_id", user_id)
            .execute()
        ).data or []
        allergen_ids = [row.get("allergen_id") for row in allergy_rows if isinstance(row, dict) and row.get("allergen_id")]
        if allergen_ids:
            allergens_ref = (
                sb.table("allergens")
                .select("id,name")
                .in_("id", allergen_ids)
                .execute()
            ).data or []
            allergy_names = [str(row.get("name")).strip() for row in allergens_ref if isinstance(row, dict) and str(row.get("name") or "").strip()]
    except Exception:
        allergy_names = []

    try:
        plans_resp = (
            sb.table("workout_plans")
            .select("title,title_ar,plan_data,is_active,updated_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        active_plan_rows = plans_resp.data or []
    except Exception as exc:
        logger.debug("Supabase workout_plans fetch failed: %s", exc)

    try:
        nutrition_resp = (
            sb.table("nutrition_plans")
            .select("title,is_active,updated_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        active_nutrition_rows = nutrition_resp.data or []
    except Exception:
        active_nutrition_rows = []

    try:
        completions_resp = (
            sb.table("workout_completions")
            .select("completed_at,log_date,created_at")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .limit(800)
            .execute()
        )
        completion_rows = completions_resp.data or []
    except Exception as exc:
        logger.debug("Supabase workout_completions fetch failed: %s", exc)

    try:
        logs_resp = (
            sb.table("daily_logs")
            .select("log_date,workout_notes,nutrition_notes,mood,updated_at")
            .eq("user_id", user_id)
            .order("log_date", desc=True)
            .limit(90)
            .execute()
        )
        log_rows = logs_resp.data or []
    except Exception as exc:
        logger.debug("Supabase daily_logs fetch failed: %s", exc)

    profile_payload = _build_profile_payload_from_db(user_id, profile_row or {})
    profile_payload = _merge_missing_profile_fields(
        profile_payload,
        _build_profile_payload_from_user_profiles(user_id, normalized_profile_row or {}),
    )

    if isinstance(preferences_row, dict):
        diet_style = preferences_row.get("diet_style")
        if diet_style and not profile_payload.get("dietary_preferences"):
            profile_payload["dietary_preferences"] = diet_style
            profile_payload["dietaryPreferences"] = diet_style
        equipment_available = preferences_row.get("equipment_available")
        if isinstance(equipment_available, list):
            equipment_value = ", ".join(
                [str(item).strip() for item in equipment_available if str(item).strip()]
            )
            if equipment_value and not profile_payload.get("equipment"):
                profile_payload["equipment"] = equipment_value
                profile_payload["available_equipment"] = equipment_value

    if condition_names:
        conditions_value = ", ".join(condition_names)
        if not profile_payload.get("chronic_conditions"):
            profile_payload["chronic_conditions"] = conditions_value
            profile_payload["chronicConditions"] = conditions_value
            profile_payload["chronic_diseases"] = conditions_value

    if allergy_names:
        allergies_value = ", ".join(allergy_names)
        if not profile_payload.get("allergies"):
            profile_payload["allergies"] = allergies_value

    nutrition_from_workout = [row for row in active_plan_rows if _is_nutrition_plan_row(row)]
    workout_plan_rows = [row for row in active_plan_rows if row not in nutrition_from_workout]
    nutrition_plan_rows = nutrition_from_workout + active_nutrition_rows

    total_tasks = sum(_count_tasks_from_plan_data(row.get("plan_data")) for row in active_plan_rows)
    completed_tasks = len(completion_rows)
    adherence_score = min(1.0, completed_tasks / total_tasks) if total_tasks > 0 else 0.0

    completion_days: set[date] = set()
    for row in completion_rows:
        day_value = _completion_date_from_row(row)
        if day_value:
            completion_days.add(day_value)

    today = datetime.utcnow().date()
    week_cutoff = today - timedelta(days=6)
    completed_last_7_days = sum(1 for row in completion_rows if (_completion_date_from_row(row) or today - timedelta(days=5000)) >= week_cutoff)
    workout_days_last_7 = sum(1 for day in completion_days if day >= week_cutoff)
    streak_days = _compute_streak_days(completion_days)

    last_completed_at = None
    if completion_rows:
        for key in ("completed_at", "created_at", "log_date"):
            value = completion_rows[0].get(key)
            if value:
                last_completed_at = str(value)
                break

    days_logged_last_7 = 0
    last_log_date = None
    for idx, row in enumerate(log_rows):
        log_day = _completion_date_from_row(row)
        if idx == 0 and log_day is not None:
            last_log_date = str(row.get("log_date") or log_day.isoformat())
        if log_day is not None and log_day >= week_cutoff:
            days_logged_last_7 += 1

    planned_days = profile_payload.get("training_days_per_week") or profile_payload.get("trainingDaysPerWeek")
    planned_days_float = _to_float(planned_days)
    weekly_stats = {
        "workout_days": workout_days_last_7,
        "planned_days": int(planned_days_float) if planned_days_float is not None else None,
    }
    monthly_stats = {
        "consistency_percent": round(adherence_score * 100.0, 1),
    }
    goal_type = profile_payload.get("goal")
    goal_payload = {"type": goal_type} if goal_type else {}
    if profile_payload.get("weight") is not None:
        goal_payload["current_weight"] = profile_payload.get("weight")

    tracking_summary = {
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "adherence_score": adherence_score,
        "completed_last_7_days": completed_last_7_days,
        "last_completed_at": last_completed_at,
        "days_logged_last_7": days_logged_last_7,
        "last_log_date": last_log_date,
        "last_daily_logs": log_rows[:5],
        "streak_days": streak_days,
        "active_workout_plans": len(workout_plan_rows),
        "active_nutrition_plans": len(nutrition_plan_rows),
        "weekly_stats": weekly_stats,
        "monthly_stats": monthly_stats,
        "goal": goal_payload,
    }

    workout_titles = [str(row.get("title")).strip() for row in workout_plan_rows if str(row.get("title") or "").strip()]
    nutrition_titles = [str(row.get("title")).strip() for row in nutrition_plan_rows if str(row.get("title") or "").strip()]
    last_plan_update = None
    for row in (active_plan_rows + active_nutrition_rows):
        value = row.get("updated_at")
        if value:
            last_plan_update = str(value)
            break

    plan_snapshot = {
        "active_workout_plans": len(workout_plan_rows),
        "active_nutrition_plans": len(nutrition_plan_rows),
        "workout_titles": workout_titles,
        "nutrition_titles": nutrition_titles,
        "updated_at": last_plan_update or datetime.utcnow().isoformat(),
    }

    data = {
        "profile_payload": profile_payload,
        "tracking_summary": tracking_summary,
        "plan_snapshot": plan_snapshot,
    }

    state["supabase_context_cache"] = {"cached_at": now_ts, "data": data}
    return data


def _contains_any(text: str, keywords: set[str]) -> bool:
    return fuzzy_contains_any(text, keywords)


def _compact_tracking_summary_for_prompt(tracking_summary: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(tracking_summary, dict):
        return {}
    compact: dict[str, Any] = {}
    keep_keys = {
        "completed_tasks",
        "total_tasks",
        "adherence_score",
        "completed_last_7_days",
        "streak_days",
        "active_workout_plans",
        "active_nutrition_plans",
        "last_completed_at",
        "last_log_date",
    }
    for key in keep_keys:
        if key in tracking_summary and tracking_summary.get(key) is not None:
            compact[key] = tracking_summary.get(key)
    weekly_stats = tracking_summary.get("weekly_stats")
    if isinstance(weekly_stats, dict):
        compact["weekly_stats"] = {
            "workout_days": weekly_stats.get("workout_days"),
            "planned_days": weekly_stats.get("planned_days"),
        }
    monthly_stats = tracking_summary.get("monthly_stats")
    if isinstance(monthly_stats, dict):
        compact["monthly_stats"] = {
            "consistency_percent": monthly_stats.get("consistency_percent"),
        }
    return compact


def _truncate_text(value: str, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


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
    if _dataset_intent_matches(user_input, "greeting"):
        return True
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
        "خطه",
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
        "خطه",
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


def _is_generic_plan_request(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    if not normalized:
        return False

    plan_terms = {
        "plan",
        "program",
        "schedule",
        "routine",
        "خطة",
        "خطه",
        "برنامج",
        "جدول",
        "بلان",
    }
    if not _contains_any(normalized, plan_terms):
        return False

    # Not generic if already explicit.
    if _is_workout_plan_request(user_input) or _is_nutrition_plan_request(user_input):
        return False
    return True


def _resolve_plan_type_from_message(user_input: str) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    if _is_workout_plan_request(user_input):
        return "workout", None
    if _is_nutrition_plan_request(user_input):
        return "nutrition", None
    if not _is_generic_plan_request(user_input):
        return None, None

    try:
        prediction = predict_plan_intent(user_input)
        predicted = str(prediction.get("predicted_intent", "")).strip().lower()
        confidence = _to_float(prediction.get("confidence"))
        if predicted in {"workout", "nutrition"} and (confidence is None or confidence >= 0.50):
            return predicted, prediction
    except FileNotFoundError:
        return None, None
    except Exception:
        return None, None

    return None, None


def _infer_goal_for_plan(profile: dict[str, Any], tracking_summary: Optional[dict[str, Any]]) -> tuple[str, Optional[float], bool]:
    explicit = _normalize_goal(profile.get("goal"))
    if explicit in {"muscle_gain", "fat_loss", "general_fitness"}:
        return explicit, None, False

    payload, _missing = _build_goal_prediction_payload(profile, tracking_summary)
    try:
        prediction = predict_goal(payload)
    except Exception:
        return "general_fitness", None, True

    predicted = _normalize_goal(prediction.get("predicted_goal"))
    confidence = None
    probs = prediction.get("probabilities") if isinstance(prediction.get("probabilities"), dict) else {}
    if predicted in probs:
        confidence = _to_float(probs.get(predicted))

    if predicted not in {"muscle_gain", "fat_loss", "general_fitness"}:
        predicted = "general_fitness"
    return predicted, confidence, True


def _has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


def _detect_language(requested_language: str, message: str, profile: dict[str, Any]) -> str:
    requested = (requested_language or "en").strip().lower()
    repaired_message = _repair_mojibake(message or "")
    preferred = str(profile.get("preferred_language", "")).lower()

    # Always prioritize the actual message content so Arabic works even if UI language is English.
    if _has_arabic(repaired_message):
        if preferred in {"ar_fusha", "ar_jordanian"}:
            return preferred

        lowered = normalize_text(repaired_message)
        if any(token in lowered for token in JORDANIAN_HINTS):
            return "ar_jordanian"
        return "ar_fusha"

    if requested in {"ar_fusha", "ar_jordanian"}:
        return requested

    if requested == "ar":
        if preferred in {"ar_fusha", "ar_jordanian"}:
            return preferred
        return "ar_fusha"

    if preferred in {"ar_fusha", "ar_jordanian"}:
        return preferred

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


def _normalize_digits(text: str) -> str:
    if not text:
        return ""
    arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return text.translate(arabic_digits)


def _extract_profile_updates_from_message(message: str) -> dict[str, Any]:
    text = normalize_text(message)
    raw = _normalize_digits(message or "")
    if not text:
        return {}

    updates: dict[str, Any] = {}

    def _merge_list(key: str, items: list[str]) -> None:
        existing = _parse_list_field(updates.get(key))
        merged = existing[:]
        for item in items:
            if item and item not in merged:
                merged.append(item)
        if merged:
            updates[key] = merged

    # Goals
    if fuzzy_contains_any(text, {"تضخيم", "زيادة عضل", "بناء عضل", "muscle gain", "bulking"}):
        updates["goal"] = "muscle_gain"
    if fuzzy_contains_any(text, {"تنشيف", "حرق دهون", "خسارة وزن", "weight loss", "fat loss", "cutting"}):
        updates["goal"] = "fat_loss"
    if fuzzy_contains_any(text, {"لياقة", "رشاقة", "general fitness", "fitness", "maintain"}):
        updates["goal"] = updates.get("goal") or "general_fitness"

    # Fitness level
    if fuzzy_contains_any(text, {"مبتدئ", "beginner"}):
        updates["fitness_level"] = "beginner"
    if fuzzy_contains_any(text, {"متوسط", "intermediate"}):
        updates["fitness_level"] = "intermediate"
    if fuzzy_contains_any(text, {"متقدم", "advanced"}):
        updates["fitness_level"] = "advanced"

    # Training days per week
    match_days = re.search(r"(\d{1,2})\s*(?:day|days|times|مره|مرة|مرات|ايام|أيام)", raw, re.IGNORECASE)
    if match_days:
        try:
            updates["training_days_per_week"] = int(match_days.group(1))
        except ValueError:
            pass

    # Weight / height / age
    weight_match = re.search(r"(وزني|weight)\s*[:\-]?\s*(\d{2,3})", raw, re.IGNORECASE)
    if weight_match:
        updates["weight"] = int(weight_match.group(2))
    height_match = re.search(r"(طولي|height)\s*[:\-]?\s*(\d{2,3})", raw, re.IGNORECASE)
    if height_match:
        updates["height"] = int(height_match.group(2))
    age_match = re.search(r"(عمري|age)\s*[:\-]?\s*(\d{1,2})", raw, re.IGNORECASE)
    if age_match:
        updates["age"] = int(age_match.group(2))

    # Allergies
    if "حساسية" in text or "allerg" in text:
        allergen_candidates = []
        match = re.search(r"(?:حساسية|allergic|allergy)\s*(?:من|to|على)?\s*([^\n\.\،]+)", raw, re.IGNORECASE)
        if match:
            allergen_candidates.extend(_parse_list_field(match.group(1)))
        for allergen in ["milk", "dairy", "peanut", "nuts", "egg", "wheat", "gluten", "shrimp", "shellfish", "حليب", "مكسرات", "بيض", "قمح", "محار"]:
            if normalize_text(allergen) in text:
                allergen_candidates.append(allergen)
        _merge_list("allergies", allergen_candidates)

    # Chronic conditions
    chronic_candidates = []
    for cond in ["diabetes", "blood pressure", "hypertension", "asthma", "heart", "سكري", "ضغط", "ربو", "قلب"]:
        if normalize_text(cond) in text:
            chronic_candidates.append(cond)
    if chronic_candidates:
        _merge_list("chronic_diseases", chronic_candidates)

    # Injuries / pain
    injury_candidates = []
    if fuzzy_contains_any(text, {"اصابة", "إصابة", "injury", "pain", "وجع", "الم"}):
        for part in ["knee", "back", "shoulder", "ankle", "hip", "ركبة", "ظهر", "كتف", "كاحل", "ورك"]:
            if normalize_text(part) in text:
                injury_candidates.append(part)
        if not injury_candidates:
            injury_candidates.append("general pain/injury")
    if injury_candidates:
        _merge_list("injuries", injury_candidates)

    # Dietary preferences
    diet_candidates = []
    for pref in ["vegan", "vegetarian", "keto", "halal", "gluten free", "lactose free", "نباتي", "فيجن", "كيتو", "حلال", "خالي من الغلوتين", "خالي من اللاكتوز"]:
        if normalize_text(pref) in text:
            diet_candidates.append(pref)
    if diet_candidates:
        _merge_list("dietary_preferences", diet_candidates)

    # Equipment
    equipment_candidates = []
    if fuzzy_contains_any(text, {"دمبل", "بار", "bands", "resistance", "معدات", "equipment", "dumbbell", "barbell"}):
        equipment_candidates.extend([t for t in ["دمبل", "بار", "باند", "dumbbells", "barbell", "bands"] if normalize_text(t) in text])
    if equipment_candidates:
        updates["equipment"] = ", ".join(dict.fromkeys(equipment_candidates))
        updates["available_equipment"] = updates["equipment"]

    return updates


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


def _dataset_text(value: Any, language: str = "en") -> str:
    if isinstance(value, dict):
        en_text = _repair_mojibake(str(value.get("en", "")).strip())
        ar_text = _repair_mojibake(str(value.get("ar", "")).strip())
        if language == "en":
            return en_text or ar_text
        return ar_text or en_text
    return _repair_mojibake(str(value or "").strip())


def _dataset_goal_key(value: Any) -> str:
    if isinstance(value, dict):
        text = f"{value.get('en', '')} {value.get('ar', '')}".strip()
    else:
        text = str(value or "")
    return _normalize_goal(text)


def _dataset_level_key(value: Any) -> str:
    normalized = normalize_text(str(value or ""))
    if "beg" in normalized or "مبت" in normalized:
        return "beginner"
    if "inter" in normalized or "متوس" in normalized:
        return "intermediate"
    if "adv" in normalized or "متقد" in normalized:
        return "advanced"
    return "beginner"


def _dataset_intent_matches(user_input: str, tag: str) -> bool:
    return RESPONSE_DATASETS.matches_intent(user_input, tag)


def _dataset_intent_response(tag: str, language: str, seed: str = "") -> Optional[str]:
    if tag == "out_of_scope":
        return _strict_out_of_scope_reply(language)
    response = RESPONSE_DATASETS.pick_response(tag, language=language, seed=seed)
    if not response:
        return None
    return _repair_mojibake(response)


def _dataset_conversation_reply(user_input: str, language: str) -> Optional[str]:
    # Priority order for conversational intents loaded from the provided dataset.
    ordered_tags: list[str] = [
        "greeting",
        "gratitude",
        "goodbye",
        "ask_exercise",
        "ask_muscle",
        "ask_home_workout",
        "ask_gym_workout",
        "ask_weight_loss",
        "ask_muscle_gain",
        "ask_general_fitness",
    ]
    known_tags = set(RESPONSE_DATASETS.intents.keys())
    for tag in ordered_tags:
        if tag not in known_tags:
            continue
        if _dataset_intent_matches(user_input, tag):
            return _dataset_intent_response(tag, language, seed=user_input)

    # Include any additional tags from dataset except fallback/sample buckets.
    for tag in RESPONSE_DATASETS.intents.keys():
        if tag in set(ordered_tags) or tag in {"out_of_scope", "short_conversations"}:
            continue
        if _dataset_intent_matches(user_input, tag):
            return _dataset_intent_response(tag, language, seed=user_input)
    return None


def _dataset_fallback_reply(language: str, seed: str = "") -> str:
    for tag in ("out_of_scope", "greeting", "gratitude", "goodbye"):
        response = _dataset_intent_response(tag, language, seed=seed)
        if response:
            return response
    return "Unable to respond."


def _strict_out_of_scope_reply(language: str) -> str:
    return _lang_reply(
        language,
        "I understand the question, but my role is focused only on fitness and nutrition. "
        "If you want help with workouts, meal plans, or improving your fitness, I am ready to help.",
        "أفهم سؤالك 👍، لكن دوري هنا يركّز على اللياقة والصحة فقط 💪  "
        "إذا حاب تسأل عن: تمارين، نظام غذائي، أو تحسين لياقتك، أنا جاهز أساعدك بكل سرور 🔥",
        "أفهم سؤالك 👍، بس دوري هون للياقة والصحة فقط 💪  "
        "إذا بدك تسأل عن تمارين أو نظام غذائي أو تحسين لياقتك، أنا جاهز أساعدك بكل سرور 🔥",
    )


def _generate_workout_plan_options_from_dataset(
    profile: dict[str, Any],
    language: str,
    count: int = 5,
) -> list[dict[str, Any]]:
    programs = RESPONSE_DATASETS.workout_programs
    if not isinstance(programs, list) or not programs:
        return []

    goal_key = _normalize_goal(profile.get("goal") or "general_fitness")
    level_key = str(profile.get("fitness_level", "beginner")).lower()
    if level_key not in {"beginner", "intermediate", "advanced"}:
        level_key = "beginner"

    scored_programs: list[tuple[int, dict[str, Any]]] = []
    for program in programs:
        if not isinstance(program, dict):
            continue
        score = 0
        program_goal = _dataset_goal_key(program.get("goal"))
        if program_goal == goal_key:
            score += 2
        program_level = _dataset_level_key(program.get("level"))
        if program_level == level_key:
            score += 1
        scored_programs.append((score, program))

    scored_programs.sort(key=lambda item: item[0], reverse=True)
    selected = [item[1] for item in scored_programs[: max(1, min(count, len(scored_programs)))]]

    rest_days = [d for d in profile.get("rest_days", []) if isinstance(d, str) and any(d == wd[0] for wd in WEEK_DAYS)]
    options: list[dict[str, Any]] = []

    for program in selected:
        program_days = [d for d in program.get("days", []) if isinstance(d, dict)]
        if not program_days:
            continue
        program_days = sorted(program_days, key=lambda d: int(d.get("day_number", 0) or 0))

        days_per_week = int(program.get("days_per_week", len(program_days)) or len(program_days) or 3)
        days_per_week = max(1, min(7, days_per_week))

        user_days = profile.get("training_days_per_week")
        if not rest_days and isinstance(user_days, (int, float)) and int(user_days) > 0:
            days_per_week = max(1, min(7, int(user_days)))

        if not rest_days:
            rest_count = max(0, 7 - days_per_week)
            rest_days_local = [day for day, _ in WEEK_DAYS[-rest_count:]] if rest_count else []
        else:
            rest_days_local = rest_days[:]

        training_days = [day for day, _ in WEEK_DAYS if day not in rest_days_local][:days_per_week]
        if len(training_days) < days_per_week:
            for day, _ in WEEK_DAYS:
                if day not in training_days:
                    training_days.append(day)
                if len(training_days) >= days_per_week:
                    break

        training_day_payload: dict[str, dict[str, Any]] = {}
        for idx, day_name in enumerate(training_days):
            source_day = program_days[idx % len(program_days)]
            exercises_raw = source_day.get("exercises", [])
            exercises: list[dict[str, Any]] = []
            for ex in exercises_raw:
                if not isinstance(ex, dict):
                    continue
                name_en = _dataset_text(ex.get("name"), "en") or "Exercise"
                name_ar = _dataset_text(ex.get("name"), "ar_fusha") or name_en
                reps = str(ex.get("reps", "8-12"))
                sets = str(ex.get("sets", 3))
                rest_seconds = int(_to_float(ex.get("rest_seconds")) or 60)
                exercises.append(
                    {
                        "name": name_en,
                        "nameAr": name_ar,
                        "sets": sets,
                        "reps": reps,
                        "rest_seconds": rest_seconds,
                        "notes": "",
                    }
                )

            training_day_payload[day_name] = {
                "focus": _dataset_text(source_day.get("focus"), language) or "Workout",
                "exercises": exercises,
            }

        normalized_days: list[dict[str, Any]] = []
        for day_en, day_ar in WEEK_DAYS:
            payload = training_day_payload.get(day_en)
            if payload:
                normalized_days.append(
                    {
                        "day": day_en,
                        "dayAr": day_ar,
                        "focus": payload.get("focus", "Workout"),
                        "exercises": payload.get("exercises", []),
                    }
                )
            else:
                normalized_days.append({"day": day_en, "dayAr": day_ar, "focus": "Rest", "exercises": []})

        title_en = _dataset_text(program.get("name"), "en") or "Workout Plan"
        title_ar = _dataset_text(program.get("name"), "ar_fusha") or title_en
        goal = _dataset_goal_key(program.get("goal")) or goal_key

        options.append(
            {
                "id": f"workout_{uuid.uuid4().hex[:10]}",
                "type": "workout",
                "title": title_en,
                "title_ar": title_ar,
                "goal": goal,
                "fitness_level": _dataset_level_key(program.get("level")),
                "rest_days": [d["day"] for d in normalized_days if not d.get("exercises")],
                "duration_days": 7,
                "days": normalized_days,
                "created_at": datetime.utcnow().isoformat(),
                "source": "week2_workout_programs_dataset",
            }
        )

    return options


def _generate_nutrition_plan_options_from_dataset(
    profile: dict[str, Any],
    language: str,
    count: int = 5,
) -> list[dict[str, Any]]:
    programs = RESPONSE_DATASETS.nutrition_programs
    if not isinstance(programs, list) or not programs:
        return []

    goal_key = _normalize_goal(profile.get("goal") or "general_fitness")
    current_weight = _to_float(profile.get("weight"))

    scored_programs: list[tuple[int, dict[str, Any]]] = []
    for program in programs:
        if not isinstance(program, dict):
            continue
        score = 0
        program_goal = _dataset_goal_key(program.get("goal"))
        if program_goal == goal_key:
            score += 2
        range_payload = program.get("weight_range_kg", {}) if isinstance(program.get("weight_range_kg"), dict) else {}
        min_w = _to_float(range_payload.get("min"))
        max_w = _to_float(range_payload.get("max"))
        if current_weight is not None and min_w is not None and max_w is not None and min_w <= current_weight <= max_w:
            score += 1
        scored_programs.append((score, program))

    scored_programs.sort(key=lambda item: item[0], reverse=True)
    selected = [item[1] for item in scored_programs[: max(1, min(count, len(scored_programs)))]]

    options: list[dict[str, Any]] = []
    for program in selected:
        restrictions = _build_food_restrictions(profile)
        calorie_range = program.get("calorie_range", {}) if isinstance(program.get("calorie_range"), dict) else {}
        cal_min = int(_to_float(calorie_range.get("min")) or 1800)
        cal_max = int(_to_float(calorie_range.get("max")) or max(cal_min, 2000))
        daily_calories = int(round((cal_min + cal_max) / 2))

        macro = program.get("macro_split", {}) if isinstance(program.get("macro_split"), dict) else {}
        protein_pct = _to_float(macro.get("protein_pct")) or 30.0
        carbs_pct = _to_float(macro.get("carbs_pct")) or 45.0
        fat_pct = _to_float(macro.get("fat_pct")) or 25.0

        sample_meals = [m for m in program.get("sample_meals", []) if isinstance(m, dict)]
        if not sample_meals:
            sample_meals = [{"meal_type": "Meal", "description": "Balanced meal"}]
        sample_meals = _filter_meals_by_restrictions(sample_meals, restrictions.get("tokens", set()))

        meals_per_day = int(profile.get("meals_per_day") or len(sample_meals) or 3)
        meals_per_day = max(2, min(6, meals_per_day))
        calories_per_meal = max(120, int(round(daily_calories / meals_per_day)))

        days_payload: list[dict[str, Any]] = []
        for day_en, day_ar in WEEK_DAYS:
            meals: list[dict[str, Any]] = []
            for i in range(meals_per_day):
                template = sample_meals[i % len(sample_meals)]
                meal_name_en = _dataset_text(template.get("meal_type"), "en") or f"Meal {i + 1}"
                meal_name_ar = _dataset_text(template.get("meal_type"), "ar_fusha") or meal_name_en
                meal_desc_en = _dataset_text(template.get("description"), "en")
                meal_desc_ar = _dataset_text(template.get("description"), "ar_fusha") or meal_desc_en
                meals.append(
                    {
                        "name": meal_name_en,
                        "nameAr": meal_name_ar,
                        "description": meal_desc_en,
                        "descriptionAr": meal_desc_ar,
                        "calories": str(calories_per_meal),
                        "time": f"meal_{i + 1}",
                    }
                )
            days_payload.append({"day": day_en, "dayAr": day_ar, "meals": meals})

        title_goal_en = _dataset_text(program.get("goal"), "en") or "Nutrition Plan"
        title_goal_ar = _dataset_text(program.get("goal"), "ar_fusha") or title_goal_en
        tips = program.get("tips", []) if isinstance(program.get("tips"), list) else []
        tips_text = " ".join(_dataset_text(tip, language) for tip in tips if str(tip).strip())
        if restrictions.get("labels"):
            tips_text = " ".join([tips_text, f"Avoid: {', '.join(restrictions['labels'])}."]).strip()
        est_protein = int(round((daily_calories * (protein_pct / 100.0)) / 4.0))

        options.append(
            {
                "id": f"nutrition_{uuid.uuid4().hex[:10]}",
                "type": "nutrition",
                "title": f"{title_goal_en} - Nutrition Plan",
                "title_ar": f"{title_goal_ar} - خطة تغذية",
                "goal": _dataset_goal_key(program.get("goal")) or goal_key,
                "daily_calories": daily_calories,
                "estimated_protein": est_protein,
                "meals_per_day": meals_per_day,
                "days": days_payload,
                "notes": tips_text,
                "macro_split": {"protein_pct": protein_pct, "carbs_pct": carbs_pct, "fat_pct": fat_pct},
                "forbidden_foods": list(restrictions.get("labels", [])),
                "created_at": datetime.utcnow().isoformat(),
                "source": "week2_nutrition_programs_dataset",
            }
        )

    return options


def _training_pipeline_ready() -> bool:
    global training_pipeline
    if training_pipeline is None:
        return False
    return getattr(training_pipeline, "trained", False) or TRAINING_PIPELINE_STATUS.get("state") == "ready"


def _normalize_training_schedule(schedule: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(schedule, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for key, value in schedule.items():
        if not isinstance(value, dict):
            continue
        key_text = str(key or "").strip()
        if not key_text:
            continue
        normalized[key_text.lower()] = value
    return normalized


def _normalize_training_exercises(exercises_raw: Any, default_sets: str, default_reps: str) -> list[dict[str, Any]]:
    if not isinstance(exercises_raw, list):
        return []
    exercises: list[dict[str, Any]] = []
    for item in exercises_raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("exercise") or item.get("name") or "Exercise").strip() or "Exercise"
        reps = str(item.get("reps") or default_reps)
        sets = str(item.get("sets") or default_sets)
        rest_seconds = int(_to_float(item.get("rest_seconds")) or 60)
        notes = str(item.get("why_recommended") or item.get("description") or "")
        exercises.append(
            {
                "name": name,
                "nameAr": name,
                "sets": sets,
                "reps": reps,
                "rest_seconds": rest_seconds,
                "notes": notes,
            }
        )
    return exercises


def _training_plan_to_workout_option(
    training_plan: dict[str, Any],
    profile: dict[str, Any],
    language: str,
) -> Optional[dict[str, Any]]:
    workout = training_plan.get("workout") if isinstance(training_plan, dict) else None
    if not isinstance(workout, dict):
        return None

    weekly_schedule = workout.get("weekly_schedule")
    schedule_map = _normalize_training_schedule(weekly_schedule)
    recommended = workout.get("recommended_exercises")
    recommended = [item for item in recommended if isinstance(item, dict)] if isinstance(recommended, list) else []

    default_sets = "3"
    default_reps = "8-12"
    cursor = 0
    plan_days: list[dict[str, Any]] = []

    for english_day, arabic_day in WEEK_DAYS:
        payload = schedule_map.get(english_day.lower())
        focus = str(payload.get("focus") if payload else "") or "Workout"
        exercises = _normalize_training_exercises(payload.get("exercises") if payload else [], default_sets, default_reps)

        is_rest = "rest" in focus.lower() and not exercises
        if not exercises and not is_rest and recommended:
            chunk = recommended[cursor: cursor + 4]
            cursor += len(chunk)
            exercises = _normalize_training_exercises(chunk, default_sets, default_reps)
            if not exercises:
                exercises = _normalize_training_exercises(recommended[:4], default_sets, default_reps)

        if not exercises and "rest" in focus.lower():
            focus = "Rest"

        plan_days.append(
            {
                "day": english_day,
                "dayAr": arabic_day,
                "focus": focus,
                "exercises": exercises,
            }
        )

    rest_days = [d.get("day") for d in plan_days if not d.get("exercises")]

    title_en = "Personalized Workout Plan"
    title_ar = "خطة تمارين مخصصة"
    if language == "ar_jordanian":
        title_ar = "خطة تمارين مخصصة"

    return {
        "id": f"workout_{uuid.uuid4().hex[:10]}",
        "type": "workout",
        "title": title_en,
        "title_ar": title_ar,
        "goal": profile.get("goal", "general_fitness"),
        "fitness_level": profile.get("fitness_level", "beginner"),
        "rest_days": rest_days,
        "duration_days": 7,
        "days": plan_days,
        "created_at": datetime.utcnow().isoformat(),
        "source": "multi_dataset_training",
    }


def _build_training_meals(
    sample_meal_plans: list[dict[str, Any]],
    daily_calories: int,
    meals_per_day: int,
) -> list[dict[str, Any]]:
    meals: list[dict[str, Any]] = []
    if sample_meal_plans:
        for idx, meal in enumerate(sample_meal_plans[:meals_per_day]):
            meal_type = str(meal.get("meal_type") or f"Meal {idx + 1}")
            options = meal.get("options") if isinstance(meal.get("options"), list) else []
            option = options[0] if options else {}
            name = str(option.get("name") or meal_type).strip() or meal_type
            macros = option.get("approximate_macros") if isinstance(option.get("approximate_macros"), dict) else {}
            protein = _to_float(macros.get("protein_g")) or 0
            carbs = _to_float(macros.get("carbs_g")) or 0
            fat = _to_float(macros.get("fat_g")) or 0
            calories = int(round((protein * 4) + (carbs * 4) + (fat * 9)))
            if calories <= 0 and daily_calories > 0:
                calories = int(round(daily_calories / max(1, meals_per_day)))

            meals.append(
                {
                    "name": name,
                    "nameAr": name,
                    "description": name,
                    "descriptionAr": name,
                    "calories": str(calories),
                    "protein": int(round(protein)),
                    "carbs": int(round(carbs)),
                    "fat": int(round(fat)),
                    "time": f"meal_{idx + 1}",
                }
            )

    if not meals and daily_calories > 0:
        calories_per_meal = int(round(daily_calories / max(1, meals_per_day)))
        for idx in range(meals_per_day):
            meals.append(
                {
                    "name": f"Meal {idx + 1}",
                    "nameAr": f"وجبة {idx + 1}",
                    "description": "Balanced meal",
                    "descriptionAr": "وجبة متوازنة",
                    "calories": str(calories_per_meal),
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0,
                    "time": f"meal_{idx + 1}",
                }
            )
    return meals


def _training_plan_to_nutrition_option(
    training_plan: dict[str, Any],
    profile: dict[str, Any],
    language: str,
) -> Optional[dict[str, Any]]:
    nutrition = training_plan.get("nutrition") if isinstance(training_plan, dict) else None
    if not isinstance(nutrition, dict):
        return None

    daily_targets = nutrition.get("daily_targets") if isinstance(nutrition.get("daily_targets"), dict) else {}
    daily_calories = int(_to_float(daily_targets.get("calorie_target")) or 0)
    macro_targets = daily_targets.get("macro_targets") if isinstance(daily_targets.get("macro_targets"), dict) else {}
    meals_per_day = int(_to_float(daily_targets.get("meal_frequency")) or profile.get("meals_per_day") or 4)
    meals_per_day = max(2, min(6, meals_per_day))

    sample_meals = [m for m in nutrition.get("sample_meal_plans", []) if isinstance(m, dict)]
    meals = _build_training_meals(sample_meals, daily_calories, meals_per_day)

    if not meals:
        days, avg_daily_protein = _build_nutrition_days(profile, daily_calories or _calculate_calories(profile))
    else:
        days = [{"day": day_en, "dayAr": day_ar, "meals": meals} for day_en, day_ar in WEEK_DAYS]
        avg_daily_protein = int(round(sum(int(_to_float(m.get("protein")) or 0) for m in meals) / max(1, len(meals))))

    protein_g = _to_float(macro_targets.get("protein_g")) or avg_daily_protein
    carbs_g = _to_float(macro_targets.get("carbs_g")) or 0
    fat_g = _to_float(macro_targets.get("fat_g")) or 0
    total_macro_cal = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
    macro_split = {}
    if total_macro_cal > 0:
        macro_split = {
            "protein_pct": round((protein_g * 4) / total_macro_cal * 100, 1),
            "carbs_pct": round((carbs_g * 4) / total_macro_cal * 100, 1),
            "fat_pct": round((fat_g * 9) / total_macro_cal * 100, 1),
        }

    restrictions = _build_food_restrictions(profile)

    title_en = "Personalized Nutrition Plan"
    title_ar = "خطة تغذية مخصصة"
    if language == "ar_jordanian":
        title_ar = "خطة أكل مخصصة"

    return {
        "id": f"nutrition_{uuid.uuid4().hex[:10]}",
        "type": "nutrition",
        "title": title_en,
        "title_ar": title_ar,
        "goal": profile.get("goal", "general_fitness"),
        "daily_calories": daily_calories or _calculate_calories(profile),
        "estimated_protein": int(round(protein_g or avg_daily_protein or 0)),
        "meals_per_day": meals_per_day,
        "days": days,
        "notes": "",
        "macro_split": macro_split,
        "forbidden_foods": list(restrictions.get("labels", [])),
        "created_at": datetime.utcnow().isoformat(),
        "source": "multi_dataset_training",
    }


def _generate_workout_plan_options_from_training(
    profile: dict[str, Any],
    language: str,
    count: int = 5,
) -> list[dict[str, Any]]:
    if not _training_pipeline_ready():
        return []
    try:
        plan = training_pipeline.get_personalized_plan(profile)
    except Exception as exc:
        logger.warning("Training pipeline plan generation failed: %s", exc)
        return []

    option = _training_plan_to_workout_option(plan, profile, language)
    if not option:
        return []
    return [option]


def _generate_nutrition_plan_options_from_training(
    profile: dict[str, Any],
    language: str,
    count: int = 5,
) -> list[dict[str, Any]]:
    if not _training_pipeline_ready():
        return []
    try:
        plan = training_pipeline.get_personalized_plan(profile)
    except Exception as exc:
        logger.warning("Training pipeline plan generation failed: %s", exc)
        return []

    option = _training_plan_to_nutrition_option(plan, profile, language)
    if not option:
        return []
    return [option]


def _build_profile(
    req: ChatRequest,
    user_state: dict[str, Any],
    profile_payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    profile = dict(profile_payload or req.user_profile or {})
    explicit_keys = set(profile.keys())

    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, list) and not value:
            return True
        return False

    tracked_keys = (
        "goal",
        "fitness_level",
        "training_days_per_week",
        "activity_level",
        "available_equipment",
        "equipment",
        "injuries",
        "dietary_preferences",
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

    if "chronicConditions" in profile and "chronic_diseases" not in profile:
        profile["chronic_diseases"] = profile.get("chronicConditions")
        explicit_keys.add("chronic_diseases")
    if "fitnessLevel" in profile and "fitness_level" not in profile:
        profile["fitness_level"] = profile.get("fitnessLevel")
        explicit_keys.add("fitness_level")
    if "trainingDaysPerWeek" in profile and "training_days_per_week" not in profile:
        profile["training_days_per_week"] = profile.get("trainingDaysPerWeek")
        explicit_keys.add("training_days_per_week")
    if "activityLevel" in profile and "activity_level" not in profile:
        profile["activity_level"] = profile.get("activityLevel")
        explicit_keys.add("activity_level")
    if "equipment" in profile and "available_equipment" not in profile:
        profile["available_equipment"] = profile.get("equipment")
        explicit_keys.add("available_equipment")
    if "dietaryPreferences" in profile and "dietary_preferences" not in profile:
        profile["dietary_preferences"] = profile.get("dietaryPreferences")
        explicit_keys.add("dietary_preferences")
    if "speakingStyle" in profile and "speaking_style" not in profile:
        profile["speaking_style"] = profile.get("speakingStyle")
        explicit_keys.add("speaking_style")

    if req.user_id:
        if "id" not in profile:
            profile["id"] = req.user_id
        if "user_id" not in profile:
            profile["user_id"] = req.user_id

    for key in tracked_keys:
        if key in explicit_keys:
            continue
        if not _is_missing(profile.get(key)):
            continue
        state_value = user_state.get(key)
        if _is_missing(state_value):
            continue
        profile[key] = state_value

    if "allergies" in profile:
        profile["allergies"] = _parse_list_field(profile.get("allergies"))
    if "chronic_diseases" in profile:
        profile["chronic_diseases"] = _parse_list_field(profile.get("chronic_diseases"))
    if "dietary_preferences" in profile:
        profile["dietary_preferences"] = _parse_list_field(profile.get("dietary_preferences"))
    if "speaking_style" in profile and isinstance(profile.get("speaking_style"), str):
        try:
            profile["speaking_style"] = json.loads(profile.get("speaking_style"))
        except Exception:
            pass

    if "training_days_per_week" in profile:
        try:
            profile["training_days_per_week"] = int(float(profile.get("training_days_per_week") or 0))
        except (TypeError, ValueError):
            pass
    if "activity_level" in profile and isinstance(profile.get("activity_level"), str):
        profile["activity_level"] = profile.get("activity_level").strip().lower()

    profile["goal"] = _normalize_goal(profile.get("goal"))

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


def _persist_profile_context(profile: dict[str, Any], state: dict[str, Any], explicit_keys: Optional[set[str]] = None) -> None:
    tracked_keys = (
        "name",
        "goal",
        "fitness_level",
        "training_days_per_week",
        "activity_level",
        "available_equipment",
        "equipment",
        "injuries",
        "dietary_preferences",
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
        "speaking_style",
    )
    explicit_keys = explicit_keys or set()
    for key in tracked_keys:
        value = profile.get(key)
        if key in explicit_keys:
            if value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
                state.pop(key, None)
                continue
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


def _profile_level_label(level: str, language: str) -> str:
    level_key = str(level or "").strip().lower()
    if level_key == "beginner":
        return _lang_reply(language, "beginner", "مبتدئ", "مبتدئ")
    if level_key == "intermediate":
        return _lang_reply(language, "intermediate", "متوسط", "متوسط")
    if level_key == "advanced":
        return _lang_reply(language, "advanced", "متقدم", "متقدم")
    return str(level or "")


def _profile_placeholder_value(key: str, profile: dict[str, Any], language: str) -> str:
    normalized_key = str(key or "").strip().lower()
    alias_map: dict[str, str] = {
        "target": "goal",
        "experience_level": "fitness_level",
        "level": "fitness_level",
        "equipment": "available_equipment",
        "training_days": "training_days_per_week",
        "workout_days": "training_days_per_week",
        "days_per_week": "training_days_per_week",
    }
    field = alias_map.get(normalized_key, normalized_key)
    value = profile.get(field)

    if field == "goal":
        return _profile_goal_label(str(value or ""), language)
    if field == "fitness_level":
        return _profile_level_label(str(value or ""), language)
    if value is None:
        return ""
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(items)
    return str(value).strip()


def _sanitize_dataset_template_text(text: str, language: str, profile: dict[str, Any]) -> str:
    cleaned = _repair_mojibake(str(text or "")).strip()
    if not cleaned:
        return cleaned

    literal_map = {
        "muscle_gain": _profile_goal_label("muscle_gain", language),
        "weight_loss": _profile_goal_label("fat_loss", language),
        "fat_loss": _profile_goal_label("fat_loss", language),
        "general_fitness": _profile_goal_label("general_fitness", language),
        "beginner": _profile_level_label("beginner", language),
        "intermediate": _profile_level_label("intermediate", language),
        "advanced": _profile_level_label("advanced", language),
    }

    for raw_token, natural_value in literal_map.items():
        if not natural_value:
            continue
        cleaned = re.sub(rf"\b{re.escape(raw_token)}\b", natural_value, cleaned, flags=re.IGNORECASE)

    def _placeholder_replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        value = _profile_placeholder_value(key, profile, language)
        return value if value else ""

    cleaned = re.sub(r"\{([a-zA-Z0-9_]+)\}", _placeholder_replacer, cleaned)
    cleaned = re.sub(r"\{[^{}]+\}", "", cleaned)
    cleaned = re.sub(r"(?i)\b(goal|target|fitness_level|experience_level|level)\s*:\s*", "", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


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

    if _is_greeting_query(user_input):
        return _greeting_reply(language, profile)

    if _is_name_query(user_input):
        return _name_reply(language)

    if _is_how_are_you_query(user_input):
        return _how_are_you_reply(language)

    if _dataset_intent_matches(user_input, "gratitude") or _contains_any(normalized, THANKS_KEYWORDS):
        dataset_reply = _dataset_intent_response("gratitude", language, seed=name or user_input)
        if dataset_reply:
            return dataset_reply
        return _lang_reply(
            language,
            f"Anytime{name_suffix}. Keep going and send me your next update.",
            f"على الرحب والسعة{name_suffix}. استمر وأرسل لي تحديثك التالي.",
            f"على راسي{name_suffix}. كمل وابعثلي تحديثك الجاي.",
        )

    if _dataset_intent_matches(user_input, "goodbye"):
        dataset_reply = _dataset_intent_response("goodbye", language, seed=name or user_input)
        if dataset_reply:
            return dataset_reply

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
    activity_level = str(profile.get("activity_level") or "").lower()

    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == "male" else -161)
    activity_factor = {"low": 1.30, "moderate": 1.50, "high": 1.70}.get(activity_level)
    if activity_factor is None:
        activity_factor = {"beginner": 1.40, "intermediate": 1.55, "advanced": 1.70}.get(fitness_level, 1.45)
    maintenance = bmr * activity_factor

    if goal == "muscle_gain":
        maintenance += 300
    elif goal == "fat_loss":
        maintenance -= 400

    return max(1200, int(round(maintenance)))


@lru_cache(maxsize=1)
def _allergy_categories_from_dataset() -> set[str]:
    dataset_root = resolve_dataset_root()
    candidates = [
        dataset_root / "food_allergy_dataset.csv",
        BACKEND_DIR / "datasets" / "food_allergy_dataset.csv",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            import csv

            with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                values = {str(row.get("Food_Type", "")).strip().lower() for row in reader if row.get("Food_Type")}
                return {v for v in values if v}
        except Exception:
            continue
    return set()


ALLERGY_CATEGORY_TOKENS: dict[str, set[str]] = {
    "gluten": {
        "gluten",
        "wheat",
        "bread",
        "flour",
        "pasta",
        "oats",
        "barley",
        "rye",
        "قمح",
        "خبز",
        "طحين",
        "معكرونة",
        "شوفان",
        "شعير",
    },
    "dairy": {
        "milk",
        "cheese",
        "yogurt",
        "butter",
        "cream",
        "milk",
        "حليب",
        "جبن",
        "لبنة",
        "زبادي",
        "زبدة",
        "قشطة",
    },
    "eggs": {
        "egg",
        "eggs",
        "omelette",
        "بيض",
        "بياض",
        "صفار",
        "اومليت",
    },
    "nuts": {
        "nuts",
        "peanut",
        "almond",
        "walnut",
        "cashew",
        "hazelnut",
        "pistachio",
        "مكسرات",
        "فول سوداني",
        "لوز",
        "جوز",
        "كاجو",
        "بندق",
        "فستق",
    },
    "seafood": {
        "seafood",
        "fish",
        "salmon",
        "tuna",
        "shrimp",
        "crab",
        "lobster",
        "سمك",
        "سلمون",
        "تونة",
        "جمبري",
        "روبيان",
        "سرطان",
        "لوبستر",
    },
}

CHRONIC_RESTRICTION_TOKENS: dict[str, set[str]] = {
    "diabetes": {
        "sugar",
        "sweet",
        "sweets",
        "soda",
        "juice",
        "white bread",
        "white rice",
        "dessert",
        "cake",
        "chocolate",
        "honey",
        "jam",
        "سكر",
        "حلويات",
        "عصير",
        "مشروبات غازية",
        "خبز ابيض",
        "رز ابيض",
        "كيك",
        "شوكولاتة",
        "عسل",
        "مربى",
    },
    "hypertension": {
        "salt",
        "salty",
        "sodium",
        "pickle",
        "processed",
        "sausage",
        "chips",
        "soy sauce",
        "ملح",
        "مخللات",
        "لحوم مصنعة",
        "نقانق",
        "شيبس",
        "صلصة الصويا",
    },
    "heart": {
        "fried",
        "butter",
        "ghee",
        "cream",
        "fatty",
        "red meat",
        "bacon",
        "sausages",
        "cheese",
        "مقلي",
        "زبدة",
        "سمنة",
        "دهون",
        "لحمة دهنية",
        "نقانق",
        "جبن",
    },
    "cholesterol": {
        "fried",
        "butter",
        "ghee",
        "cream",
        "fatty",
        "red meat",
        "bacon",
        "sausages",
        "cheese",
        "مقلي",
        "زبدة",
        "سمنة",
        "دهون",
        "لحمة دهنية",
        "نقانق",
        "جبن",
    },
}

DIETARY_PREFERENCE_MATCH: dict[str, set[str]] = {
    "vegan": {"vegan", "plant based", "plant-based", "نباتي صرف", "نباتي صارم", "نباتي بالكامل"},
    "vegetarian": {"vegetarian", "vegetrian", "veg", "نباتي", "نباتية"},
    "halal": {"halal", "حلال"},
    "keto": {"keto", "ketogenic", "كيتو"},
    "gluten_free": {
        "gluten free",
        "gluten-free",
        "خالي من الجلوتين",
        "خالي من الغلوتين",
        "بدون جلوتين",
        "بدون غلوتين",
    },
    "lactose_free": {"lactose free", "lactose-free", "dairy free", "dairy-free", "خالي من اللاكتوز", "بدون لاكتوز"},
}

MEAT_TOKENS = {
    "meat",
    "beef",
    "chicken",
    "turkey",
    "lamb",
    "goat",
    "pork",
    "bacon",
    "ham",
    "sausage",
    "fish",
    "salmon",
    "tuna",
    "shrimp",
    "crab",
    "lobster",
    "لحم",
    "دجاج",
    "ديك رومي",
    "غنم",
    "ماعز",
    "خنزير",
    "لحم خنزير",
    "نقانق",
    "سمك",
    "سلمون",
    "تونة",
    "جمبري",
    "روبيان",
    "سرطان",
}

PORK_ALCOHOL_TOKENS = {
    "pork",
    "bacon",
    "ham",
    "wine",
    "beer",
    "whiskey",
    "vodka",
    "rum",
    "gin",
    "liquor",
    "alcohol",
    "خنزير",
    "لحم خنزير",
    "بيكون",
    "نبيذ",
    "بيرة",
    "ويسكي",
    "فودكا",
    "رم",
    "كحول",
    "مشروب كحولي",
}

KETO_AVOID_TOKENS = (
    CHRONIC_RESTRICTION_TOKENS["diabetes"]
    | {
        "bread",
        "rice",
        "pasta",
        "potato",
        "oats",
        "corn",
        "flour",
        "cereal",
        "juice",
        "cake",
        "dessert",
        "خبز",
        "رز",
        "معكرونة",
        "بطاطا",
        "شوفان",
        "ذرة",
        "طحين",
        "حبوب",
        "عصير",
        "كيك",
        "حلويات",
    }
)

DIETARY_PREFERENCE_TOKENS: dict[str, set[str]] = {
    "vegan": MEAT_TOKENS | ALLERGY_CATEGORY_TOKENS["dairy"] | ALLERGY_CATEGORY_TOKENS["eggs"] | {"honey", "عسل"},
    "vegetarian": MEAT_TOKENS,
    "halal": PORK_ALCOHOL_TOKENS,
    "keto": KETO_AVOID_TOKENS,
    "gluten_free": ALLERGY_CATEGORY_TOKENS["gluten"],
    "lactose_free": ALLERGY_CATEGORY_TOKENS["dairy"],
}


def _text_contains_any(text: str, tokens: set[str]) -> bool:
    normalized = normalize_text(text or "")
    if not normalized or not tokens:
        return False
    return any(token and normalize_text(token) in normalized for token in tokens)


def _build_food_restrictions(profile: dict[str, Any]) -> dict[str, Any]:
    allergies = _parse_list_field(profile.get("allergies"))
    chronic = _parse_list_field(profile.get("chronic_diseases"))
    dietary_preferences = _parse_list_field(profile.get("dietary_preferences"))

    tokens: set[str] = set()
    labels: list[str] = []

    known_categories = _allergy_categories_from_dataset()

    for allergy in allergies:
        norm = normalize_text(allergy)
        matched = False
        for key, key_tokens in ALLERGY_CATEGORY_TOKENS.items():
            if key in norm or any(normalize_text(tok) in norm for tok in key_tokens):
                tokens |= key_tokens
                if key not in labels:
                    labels.append(key)
                matched = True
        if not matched and norm:
            tokens.add(allergy)
            if allergy not in labels:
                labels.append(allergy)

    # If dataset categories exist, include them in labels when user mentions them.
    for category in known_categories:
        if category and any(category in normalize_text(a) for a in allergies):
            if category not in labels:
                labels.append(category)

    for disease in chronic:
        norm = normalize_text(disease)
        if "diab" in norm or "سكر" in norm:
            tokens |= CHRONIC_RESTRICTION_TOKENS["diabetes"]
            labels.append("diabetes")
            continue
        if "ضغط" in norm or "hypertension" in norm:
            tokens |= CHRONIC_RESTRICTION_TOKENS["hypertension"]
            labels.append("hypertension")
            continue
        if "قلب" in norm or "heart" in norm:
            tokens |= CHRONIC_RESTRICTION_TOKENS["heart"]
            labels.append("heart")
            continue
        if "كوليسترول" in norm or "cholesterol" in norm:
            tokens |= CHRONIC_RESTRICTION_TOKENS["cholesterol"]
            labels.append("cholesterol")

    for pref in dietary_preferences:
        norm = normalize_text(pref)
        matched = False
        for key, aliases in DIETARY_PREFERENCE_MATCH.items():
            if any(alias and alias in norm for alias in aliases):
                tokens |= DIETARY_PREFERENCE_TOKENS.get(key, set())
                if key not in labels:
                    labels.append(key)
                matched = True
                break
        if not matched and norm:
            if pref not in labels:
                labels.append(pref)

    return {
        "tokens": {t for t in tokens if t},
        "labels": labels,
        "allergies": allergies,
        "chronic_diseases": chronic,
        "dietary_preferences": dietary_preferences,
    }


def _filter_meals_by_restrictions(meals: list[dict[str, Any]], restriction_tokens: set[str]) -> list[dict[str, Any]]:
    if not meals or not restriction_tokens:
        return meals
    filtered: list[dict[str, Any]] = []
    for meal in meals:
        haystack = " ".join(
            [
                str(meal.get("meal_type", "")),
                str(meal.get("description", "")),
                str(meal.get("name", "")),
                str(meal.get("descriptionAr", "")),
                str(meal.get("nameAr", "")),
            ]
        )
        if _text_contains_any(haystack, restriction_tokens):
            continue
        filtered.append(meal)
    return filtered if filtered else meals


def _safe_meal_templates(allergies: list[str], restriction_tokens: set[str] | None = None) -> list[dict[str, Any]]:
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
    if restriction_tokens:
        allergy_tokens |= {t.lower() for t in restriction_tokens}
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
    restrictions = _build_food_restrictions(profile)

    meal_templates = _safe_meal_templates(allergies, restrictions.get("tokens", set()))
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
    restrictions = _build_food_restrictions(profile)
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
    if restrictions.get("labels"):
        notes.append(f"Restricted foods based on profile: {', '.join(restrictions['labels'])}.")

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
        "forbidden_foods": list(restrictions.get("labels", [])),
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


def _format_recommended_plan(plan_type: str, plan: dict[str, Any], language: str) -> str:
    warning_lines = plan.get("safety_warnings") or []
    warning_text = "\n".join([f"⚠️ {w}" for w in warning_lines]) if warning_lines else ""
    base_preview = _format_plan_preview(plan_type, plan, language)
    if not warning_text:
        return base_preview
    if language == "en":
        return f"{base_preview}\n\nSafety notes:\n{warning_text}"
    if language == "ar_fusha":
        return f"{base_preview}\n\nملاحظات سلامة:\n{warning_text}"
    return f"{base_preview}\n\nملاحظات سلامة:\n{warning_text}"


def _generate_workout_plan_options(profile: dict[str, Any], language: str, count: int = 5) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    training_options = _generate_workout_plan_options_from_training(profile, language, count)
    if training_options:
        options.extend(training_options)

    remaining = max(0, count - len(options))
    if remaining:
        dataset_options = _generate_workout_plan_options_from_dataset(profile, language, remaining)
        options.extend(dataset_options)

    if not options:
        options = [_generate_workout_plan(profile, language)]

    return options[:count]

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
    options: list[dict[str, Any]] = []
    training_options = _generate_nutrition_plan_options_from_training(profile, language, count)
    if training_options:
        options.extend(training_options)

    remaining = max(0, count - len(options))
    if remaining:
        dataset_options = _generate_nutrition_plan_options_from_dataset(profile, language, remaining)
        options.extend(dataset_options)

    if not options:
        options = [_generate_nutrition_plan(profile, language)]

    return options[:count]


def _recommend_best_plan(
    plan_type: str,
    profile: dict[str, Any],
    language: str,
    user_id: str,
    tracking_summary: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]] | tuple[None, list[dict[str, Any]]]:
    options = (
        _generate_nutrition_plan_options(profile, language, count=8)
        if plan_type == "nutrition"
        else _generate_workout_plan_options(profile, language, count=8)
    )
    if not options:
        return None, []

    penalties = get_feedback_summary(user_id) if user_id else {}
    ranked = rank_plans(options, profile, feedback_penalties=penalties)
    best = deepcopy(ranked[0])

    # Safety adjustments
    if plan_type == "nutrition":
        best = filter_nutrition_plan(best, profile)
    else:
        best = filter_workout_plan(best, profile)
        if detect_overtraining(profile, tracking_summary):
            notes = best.get("notes") or ""
            best["notes"] = f"{notes} Add one extra rest day due to recovery risk.".strip()
    return best, ranked

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
    dataset_reply = _dataset_intent_response("greeting", language, seed=display_name or "user")
    if dataset_reply:
        return dataset_reply

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


def _dict_get_any(source: Any, keys: list[str]) -> Any:
    if not isinstance(source, dict):
        return None
    for key in keys:
        if key in source and source[key] not in (None, ""):
            return source[key]
    return None


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base or {})
    for key, value in (patch or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _extract_json_objects(text: str) -> list[str]:
    results: list[str] = []
    start_idx: Optional[int] = None
    depth = 0
    for idx, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start_idx = idx
            depth += 1
        elif char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start_idx is not None:
                candidate = text[start_idx : idx + 1].strip()
                if candidate:
                    results.append(candidate)
                start_idx = None
    return results


def _try_parse_json_object(raw_text: str) -> Optional[dict[str, Any]]:
    candidate = (raw_text or "").strip()
    if not candidate:
        return None

    parse_candidates = [
        candidate,
        re.sub(r",\s*([}\]])", r"\1", candidate),
    ]
    for payload in parse_candidates:
        try:
            obj = json.loads(payload)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


def _looks_like_tracking_summary(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    if any(key in payload for key in ("goal", "weekly_stats", "monthly_stats", "adherence_score")):
        return True
    # Some payloads may arrive flattened.
    flat_keys = {"goal.type", "goal.current_weight", "goal.target_weight", "weekly_stats.weight_change"}
    return any(key in payload for key in flat_keys)


def _extract_float_from_patterns(source: str, patterns: list[str]) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if not match:
            continue
        parsed = _to_float(match.group(1))
        if parsed is not None:
            return parsed
    return None


def _extract_float_series_from_patterns(source: str, patterns: list[str]) -> list[float]:
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if not match:
            continue
        values = _to_float_list(match.group(1))
        if len(values) >= 2:
            return values
    return []


def _extract_goal_type_from_patterns(source: str) -> str:
    goal_patterns = [
        r"(?:goal(?:\s*type)?|goal_type|نوع\s*الهدف|الهدف)\s*[:=]\s*([a-z_\-\s\u0600-\u06FF]+)",
    ]
    for pattern in goal_patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if not match:
            continue
        normalized = _normalize_goal(match.group(1))
        if normalized in {"muscle_gain", "fat_loss", "general_fitness"}:
            return normalized
    inferred = _normalize_goal(source)
    if inferred in {"muscle_gain", "fat_loss", "general_fitness"}:
        return inferred
    return ""


def _extract_tracking_summary_from_message(
    user_input: str,
    profile: dict[str, Any],
) -> Optional[dict[str, Any]]:
    source = _repair_mojibake(user_input or "")
    if not source:
        return None

    extracted: dict[str, Any] = {}
    has_tracking_signal = False

    for candidate in _extract_json_objects(source):
        obj = _try_parse_json_object(candidate)
        if not obj:
            continue
        if _looks_like_tracking_summary(obj):
            extracted = _deep_merge_dict(extracted, obj)
            has_tracking_signal = True

    goal_payload = extracted.get("goal") if isinstance(extracted.get("goal"), dict) else {}
    weekly_payload = extracted.get("weekly_stats") if isinstance(extracted.get("weekly_stats"), dict) else {}
    monthly_payload = extracted.get("monthly_stats") if isinstance(extracted.get("monthly_stats"), dict) else {}

    goal_type = _extract_goal_type_from_patterns(source)
    if goal_type:
        goal_payload["type"] = goal_type
        has_tracking_signal = True

    number_pattern = r"([+-]?\d+(?:\.\d+)?)(?:\s*\+)?"
    current_weight = _extract_float_from_patterns(
        source,
        [
            rf"(?:current[_\s-]*weight|weight[_\s-]*now|وزن(?:ي)?\s*(?:الحالي|الان|الآن)?)\s*[:=]?\s*{number_pattern}",
            rf"(?:وزن(?:ي)?|وزني)\s*[:=]?\s*{number_pattern}",
            rf"(?:goal\.current_weight|current_weight)\s*[:=]?\s*{number_pattern}",
        ],
    )
    target_weight = _extract_float_from_patterns(
        source,
        [
            rf"(?:target[_\s-]*weight|goal[_\s-]*weight|الوزن\s*(?:المستهدف|الهدف)|هدف(?:ي)?\s*وزن)\s*[:=]?\s*{number_pattern}",
            rf"(?:هدفي|هدف(?:ي)?)\s*[:=]?\s*{number_pattern}",
            rf"(?:goal\.target_weight|target_weight)\s*[:=]?\s*{number_pattern}",
        ],
    )
    weekly_weight_change = _extract_float_from_patterns(
        source,
        [
            rf"(?:weekly[_\s-]*weight[_\s-]*change|weekly[_\s-]*change|تغير\s*الوزن\s*(?:الاسبوعي|الأسبوعي)|نزول\s*(?:اسبوعي|أسبوعي)|زيادة\s*(?:اسبوعية|أسبوعية))\s*[:=]?\s*{number_pattern}",
            rf"(?:weekly_stats\.weight_change|weight_change)\s*[:=]?\s*{number_pattern}",
        ],
    )

    if weekly_weight_change is None:
        gain_match = re.search(
            rf"(?:زاد(?:ت)?\s*وزن(?:ي)?|وزن(?:ي)?\s*زاد|وزن(?:ي)?\s*بزيد|وزن(?:ي)?\s*عم\s*يزيد|زيادة\s*وزن(?:ي)?)\s*(?:بالاسبوع|بالأسبوع|اسبوعي|أسبوعي)?\s*[:=]?\s*{number_pattern}",
            source,
            flags=re.IGNORECASE,
        )
        loss_match = re.search(
            rf"(?:نقص(?:ت)?\s*وزن(?:ي)?|وزن(?:ي)?\s*نقص|وزن(?:ي)?\s*بنقص|وزن(?:ي)?\s*عم\s*ينقص|نزول\s*وزن(?:ي)?|خسرت\s*وزن(?:ي)?)\s*(?:بالاسبوع|بالأسبوع|اسبوعي|أسبوعي)?\s*[:=]?\s*{number_pattern}",
            source,
            flags=re.IGNORECASE,
        )
        if gain_match:
            weekly_weight_change = _to_float(gain_match.group(1))
        elif loss_match:
            loss_value = _to_float(loss_match.group(1))
            weekly_weight_change = -abs(loss_value) if loss_value is not None else None
    monthly_weight_change = _extract_float_from_patterns(
        source,
        [
            rf"(?:monthly[_\s-]*weight[_\s-]*change|monthly[_\s-]*change|تغير\s*الوزن\s*الشهري)\s*[:=]?\s*{number_pattern}",
            rf"(?:monthly_stats\.weight_change|monthly_weight_change)\s*[:=]?\s*{number_pattern}",
        ],
    )
    strength_increase = _extract_float_from_patterns(
        source,
        [
            rf"(?:strength[_\s-]*increase(?:[_\s-]*percent)?|strength[_\s-]*percent|زيادة\s*القوة(?:\s*الشهرية)?)\s*[:=]?\s*{number_pattern}\s*%?",
            rf"(?:monthly_stats\.strength_increase_percent|strength_increase_percent)\s*[:=]?\s*{number_pattern}",
        ],
    )
    consistency_percent = _extract_float_from_patterns(
        source,
        [
            rf"(?:consistency(?:[_\s-]*percent)?|consistency[_\s-]*pct|نسبة\s*الالتزام|الالتزام)\s*[:=]?\s*{number_pattern}\s*%?",
            rf"(?:monthly_stats\.consistency_percent|consistency_percent)\s*[:=]?\s*{number_pattern}",
        ],
    )
    workout_days = _extract_float_from_patterns(
        source,
        [
            rf"(?:workout[_\s-]*days|days[_\s-]*trained|ايام\s*التمرين|أيام\s*التمرين)\s*[:=]?\s*{number_pattern}",
            rf"(?:weekly_stats\.workout_days|workout_days)\s*[:=]?\s*{number_pattern}",
        ],
    )
    planned_days = _extract_float_from_patterns(
        source,
        [
            rf"(?:planned[_\s-]*days|plan[_\s-]*days|ايام\s*الخطة|أيام\s*الخطة)\s*[:=]?\s*{number_pattern}",
            rf"(?:weekly_stats\.planned_days|planned_days)\s*[:=]?\s*{number_pattern}",
        ],
    )
    avg_calories = _extract_float_from_patterns(
        source,
        [
            rf"(?:avg[_\s-]*calories|average[_\s-]*calories|متوسط\s*السعرات|السعرات)\s*[:=]?\s*{number_pattern}",
            rf"(?:weekly_stats\.avg_calories|avg_calories)\s*[:=]?\s*{number_pattern}",
        ],
    )
    avg_protein = _extract_float_from_patterns(
        source,
        [
            rf"(?:avg[_\s-]*protein|average[_\s-]*protein|متوسط\s*البروتين|البروتين)\s*[:=]?\s*{number_pattern}",
            rf"(?:weekly_stats\.avg_protein|avg_protein)\s*[:=]?\s*{number_pattern}",
        ],
    )
    sleep_avg_hours = _extract_float_from_patterns(
        source,
        [
            rf"(?:sleep[_\s-]*avg[_\s-]*hours|average[_\s-]*sleep|sleep[_\s-]*hours|متوسط\s*النوم|ساعات\s*النوم)\s*[:=]?\s*{number_pattern}",
            rf"(?:weekly_stats\.sleep_avg_hours|sleep_avg_hours)\s*[:=]?\s*{number_pattern}",
        ],
    )
    weight_change_history = _extract_float_series_from_patterns(
        source,
        [
            r"(?:weight[_\s-]*change[_\s-]*history|weekly[_\s-]*history|last[_\s-]*4[_\s-]*weeks(?:[_\s-]*weight[_\s-]*change)?)\s*[:=]\s*([0-9,\.\-\+\s|;/]+)",
            r"(?:تغير(?:ات)?\s*الوزن\s*(?:آخر|اخر)\s*4\s*(?:اسابيع|أسابيع)|آخر\s*4\s*(?:اسابيع|أسابيع)\s*تغير\s*الوزن)\s*[:=]\s*([0-9,\.\-\+\s|;/]+)",
        ],
    )

    if current_weight is not None:
        goal_payload["current_weight"] = current_weight
        has_tracking_signal = True
    if target_weight is not None:
        goal_payload["target_weight"] = target_weight
        has_tracking_signal = True
    if weekly_weight_change is not None:
        weekly_payload["weight_change"] = weekly_weight_change
        has_tracking_signal = True
    if monthly_weight_change is not None:
        monthly_payload["weight_change"] = monthly_weight_change
        has_tracking_signal = True
    if strength_increase is not None:
        monthly_payload["strength_increase_percent"] = strength_increase
        has_tracking_signal = True
    if consistency_percent is not None:
        monthly_payload["consistency_percent"] = consistency_percent
        has_tracking_signal = True
    if workout_days is not None:
        weekly_payload["workout_days"] = workout_days
        has_tracking_signal = True
    if planned_days is not None:
        weekly_payload["planned_days"] = planned_days
        has_tracking_signal = True
    if avg_calories is not None:
        weekly_payload["avg_calories"] = avg_calories
        has_tracking_signal = True
    if avg_protein is not None:
        weekly_payload["avg_protein"] = avg_protein
        has_tracking_signal = True
    if sleep_avg_hours is not None:
        weekly_payload["sleep_avg_hours"] = sleep_avg_hours
        has_tracking_signal = True
    if weight_change_history:
        weekly_payload["weight_change_history"] = weight_change_history[-4:]
        has_tracking_signal = True

    if goal_payload:
        extracted["goal"] = goal_payload
    if weekly_payload:
        extracted["weekly_stats"] = weekly_payload
    if monthly_payload:
        extracted["monthly_stats"] = monthly_payload

    if not has_tracking_signal:
        return None
    return extracted or None


def _merge_tracking_summaries(
    current_summary: Optional[dict[str, Any]],
    new_summary: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if not isinstance(current_summary, dict) and not isinstance(new_summary, dict):
        return None
    if not isinstance(current_summary, dict):
        return deepcopy(new_summary) if isinstance(new_summary, dict) else None
    if not isinstance(new_summary, dict):
        return deepcopy(current_summary)
    return _deep_merge_dict(current_summary, new_summary)


def _has_actionable_tracking_metrics(summary: Optional[dict[str, Any]]) -> bool:
    if not isinstance(summary, dict):
        return False

    goal = summary.get("goal") if isinstance(summary.get("goal"), dict) else {}
    weekly = summary.get("weekly_stats") if isinstance(summary.get("weekly_stats"), dict) else {}
    monthly = summary.get("monthly_stats") if isinstance(summary.get("monthly_stats"), dict) else {}

    if _to_float(_dict_get_any(goal, ["current_weight", "target_weight", "target_strength_increase_percent"])) is not None:
        return True
    if _to_float(_dict_get_any(weekly, ["weight_change", "weekly_weight_change"])) is not None:
        return True
    if _to_float(_dict_get_any(monthly, ["strength_increase_percent", "weight_change"])) is not None:
        return True
    if _to_float(_dict_get_any(monthly, ["consistency_percent"])) is not None:
        return True
    if _to_float_list(_dict_get_any(weekly, ["weight_change_history", "weight_change_last_4_weeks"])):
        return True
    if _to_float_list(_dict_get_any(summary, ["weekly_weight_change_history", "last_4_weeks_weight_change"])):
        return True

    return False


def _is_performance_analysis_request(
    user_input: str,
    message_tracking_summary: Optional[dict[str, Any]] = None,
) -> bool:
    normalized = normalize_text(user_input)
    if not normalized:
        return False

    if _contains_any(normalized, PERFORMANCE_ANALYSIS_KEYWORDS):
        return True

    if _contains_any(normalized, {"analyze", "analysis", "حلل", "تحليل", "قيّم", "قيم"}):
        if _contains_any(normalized, {"performance", "progress", "اداء", "أداء", "ادائي", "تقدمي", "تقدم"}):
            return True

    intent_terms = {
        "analysis",
        "analyze",
        "progress rate",
        "on track",
        "ahead",
        "behind",
        "estimate",
        "timeline",
        "weeks remaining",
        "تحليل",
        "حلل",
        "تقييم",
        "على المسار",
        "متقدم",
        "متاخر",
        "متأخر",
        "كم اسبوع",
        "كم أسبوع",
        "الوقت المتبقي",
        "المتبقي",
    }
    metric_terms = {
        "weight",
        "strength",
        "calories",
        "protein",
        "sleep",
        "consistency",
        "وزن",
        "قوة",
        "سعرات",
        "بروتين",
        "نوم",
        "التزام",
        "تقدم",
    }
    if _contains_any(normalized, intent_terms) and _contains_any(normalized, metric_terms):
        return True

    # If the user sends actionable tracking metrics in the same message, treat it as analysis intent.
    if _has_actionable_tracking_metrics(message_tracking_summary):
        return True

    return False


def _format_number(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def _to_float_list(value: Any) -> list[float]:
    values: list[float] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                parsed = _to_float(
                    _dict_get_any(item, ["weight_change", "weekly_weight_change", "weightChange", "delta", "change"])
                )
            else:
                parsed = _to_float(item)
            if parsed is not None:
                values.append(parsed)
        return values

    if isinstance(value, str):
        for token in re.findall(r"-?\d+(?:\.\d+)?", value):
            parsed = _to_float(token)
            if parsed is not None:
                values.append(parsed)
    return values


def _extract_weight_change_series(
    tracking_summary: dict[str, Any],
    weekly_stats: dict[str, Any],
) -> list[float]:
    direct_series_keys = [
        "weight_change_last_4_weeks",
        "weight_change_history",
        "last_4_weeks_weight_change",
        "weekly_weight_change_history",
        "last4_weight_change",
        "recent_weight_changes",
    ]
    for key in direct_series_keys:
        if key in weekly_stats:
            values = _to_float_list(weekly_stats.get(key))
            if values:
                return values

    summary_series_keys = [
        "weekly_weight_change_history",
        "weight_change_history",
        "last_4_weeks_weight_change",
        "recent_weight_changes",
        "last_4_weeks",
    ]
    for key in summary_series_keys:
        if key in tracking_summary:
            values = _to_float_list(tracking_summary.get(key))
            if values:
                return values

    weekly_history = tracking_summary.get("weekly_history")
    values = _to_float_list(weekly_history)
    if values:
        return values

    return []


def _average(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _mean_abs_deviation(values: list[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    mean_value = _average(values)
    if mean_value is None:
        return None
    return sum(abs(item - mean_value) for item in values) / len(values)


def _fitness_level_to_experience(value: Any) -> float:
    normalized = normalize_text(str(value or ""))
    if any(token in normalized for token in {"advanced", "adv", "متقدم"}):
        return 3.0
    if any(token in normalized for token in {"intermediate", "inter", "متوسط"}):
        return 2.0
    if any(token in normalized for token in {"beginner", "beg", "مبتد"}):
        return 1.0
    parsed = _to_float(value)
    return float(parsed) if parsed is not None else 0.0


def _is_goal_prediction_request(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    if _contains_any(normalized, ML_GOAL_QUERY_KEYWORDS):
        return True
    return _contains_any(normalized, {"goal", "هدف"}) and _contains_any(normalized, ML_GENERAL_PREDICTION_KEYWORDS)


def _is_success_prediction_request(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    if _contains_any(normalized, ML_SUCCESS_QUERY_KEYWORDS):
        return True
    return _contains_any(normalized, {"success", "نجاح", "التزام"}) and _contains_any(
        normalized, ML_GENERAL_PREDICTION_KEYWORDS
    )


def _build_goal_prediction_payload(
    profile: dict[str, Any], tracking_summary: Optional[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    tracking_summary = tracking_summary if isinstance(tracking_summary, dict) else {}
    weekly_stats = tracking_summary.get("weekly_stats") if isinstance(tracking_summary.get("weekly_stats"), dict) else {}
    monthly_stats = tracking_summary.get("monthly_stats") if isinstance(tracking_summary.get("monthly_stats"), dict) else {}

    age = _to_float(profile.get("age"))
    gender = str(profile.get("gender") or "Other")
    weight_kg = _to_float(_dict_get_any(profile, ["weight", "weight_kg"]))

    height_value = _to_float(_dict_get_any(profile, ["height", "height_cm", "height_m"]))
    height_cm: Optional[float] = None
    height_m: Optional[float] = None
    if height_value is not None:
        if height_value > 3:
            height_cm = height_value
            height_m = height_value / 100.0
        else:
            height_m = height_value
            height_cm = height_value * 100.0

    fat_percentage = _to_float(_dict_get_any(profile, ["fat_percentage", "body_fat_percentage", "body_fat"]))
    workout_frequency_days_week = _to_float(
        _dict_get_any(weekly_stats, ["workout_days", "training_days", "sessions", "completed_workouts"])
    )
    calories_burned = _to_float(
        _dict_get_any(weekly_stats, ["calories_burned", "avg_calories_burned", "calories_burned_avg"])
    )
    if calories_burned is None:
        calories_burned = _to_float(_dict_get_any(monthly_stats, ["avg_calories_burned", "calories_burned"]))
    avg_bpm = _to_float(_dict_get_any(weekly_stats, ["avg_bpm", "heart_rate_avg", "average_bpm"]))

    payload = {
        "age": age or 0.0,
        "gender": gender,
        "weight_kg": weight_kg or 0.0,
        "height_m": height_m,
        "height_cm": height_cm,
        "bmi": _to_float(_dict_get_any(profile, ["bmi"])) or 0.0,
        "fat_percentage": fat_percentage or 0.0,
        "workout_frequency_days_week": workout_frequency_days_week or 0.0,
        "experience_level": _fitness_level_to_experience(profile.get("fitness_level")),
        "calories_burned": calories_burned or 0.0,
        "avg_bpm": avg_bpm or 0.0,
    }

    missing_fields: list[str] = []
    if age is None:
        missing_fields.append("age")
    if weight_kg is None:
        missing_fields.append("weight")
    if height_value is None:
        missing_fields.append("height")

    return payload, missing_fields


def _build_success_prediction_payload(
    profile: dict[str, Any], tracking_summary: Optional[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    tracking_summary = tracking_summary if isinstance(tracking_summary, dict) else {}
    weekly_stats = tracking_summary.get("weekly_stats") if isinstance(tracking_summary.get("weekly_stats"), dict) else {}
    monthly_stats = tracking_summary.get("monthly_stats") if isinstance(tracking_summary.get("monthly_stats"), dict) else {}

    age = _to_float(profile.get("age"))
    gender = str(profile.get("gender") or "Other")
    membership_type = str(_dict_get_any(profile, ["membership_type", "membership", "plan_type"]) or "Unknown")
    workout_type = str(
        _dict_get_any(weekly_stats, ["workout_type", "main_workout_type"])
        or _dict_get_any(profile, ["workout_type", "preferred_workout_type"])
        or "General"
    )
    workout_duration_minutes = _to_float(
        _dict_get_any(
            weekly_stats,
            ["avg_workout_duration_minutes", "workout_duration_minutes", "session_duration_minutes", "duration_minutes"],
        )
    )
    if workout_duration_minutes is None:
        workout_duration_minutes = _to_float(_dict_get_any(monthly_stats, ["avg_workout_duration_minutes"]))
    calories_burned = _to_float(
        _dict_get_any(weekly_stats, ["calories_burned", "avg_calories_burned", "calories_burned_avg"])
    )
    if calories_burned is None:
        calories_burned = _to_float(_dict_get_any(monthly_stats, ["avg_calories_burned", "calories_burned"]))

    check_in_hour_value = _to_float(_dict_get_any(weekly_stats, ["check_in_hour", "avg_check_in_hour"]))
    check_in_hour = int(check_in_hour_value) if check_in_hour_value is not None else int(datetime.utcnow().hour)

    payload = {
        "age": age or 0.0,
        "gender": gender,
        "membership_type": membership_type,
        "workout_type": workout_type,
        "workout_duration_minutes": workout_duration_minutes or 0.0,
        "calories_burned": calories_burned or 0.0,
        "check_in_hour": check_in_hour,
    }

    missing_fields: list[str] = []
    if age is None:
        missing_fields.append("age")
    if workout_duration_minutes is None:
        missing_fields.append("weekly_stats.avg_workout_duration_minutes")
    if calories_burned is None:
        missing_fields.append("weekly_stats.calories_burned")

    return payload, missing_fields


def _ml_missing_fields_reply(language: str, prediction_type: str, missing_fields: list[str]) -> str:
    missing_text = ", ".join(missing_fields)
    if prediction_type == "goal":
        return _lang_reply(
            language,
            f"To run goal prediction, I still need: {missing_text}.",
            f"لتشغيل توقع الهدف، أحتاج هذه البيانات: {missing_text}.",
            f"عشان أشغّل توقع الهدف، لسا بحتاج: {missing_text}.",
        )
    return _lang_reply(
        language,
        f"To run success prediction, I still need: {missing_text}.",
        f"لتشغيل توقع النجاح، أحتاج هذه البيانات: {missing_text}.",
        f"عشان أشغّل توقع النجاح، لسا بحتاج: {missing_text}.",
    )


def _goal_label_from_prediction(value: Any, language: str) -> str:
    key = str(value or "").strip().lower()
    if key in {"muscle_gain", "fat_loss", "general_fitness"}:
        return _profile_goal_label(key, language)
    return str(value or "unknown")


def _ml_prediction_chat_response(
    user_input: str,
    language: str,
    profile: dict[str, Any],
    tracking_summary: Optional[dict[str, Any]],
) -> Optional[tuple[str, dict[str, Any]]]:
    want_goal = _is_goal_prediction_request(user_input)
    want_success = _is_success_prediction_request(user_input)

    if not want_goal and not want_success:
        return None

    reply_parts: list[str] = []
    payload: dict[str, Any] = {}

    if want_goal:
        goal_features, missing = _build_goal_prediction_payload(profile, tracking_summary)
        if missing:
            reply_parts.append(_ml_missing_fields_reply(language, "goal", missing))
        else:
            try:
                result = predict_goal(goal_features)
                predicted_goal = result.get("predicted_goal")
                predicted_goal_label = _goal_label_from_prediction(predicted_goal, language)
                confidence = None
                probabilities = result.get("probabilities") if isinstance(result.get("probabilities"), dict) else {}
                if predicted_goal in probabilities:
                    confidence = _to_float(probabilities.get(predicted_goal))

                goal_reply = _lang_reply(
                    language,
                    (
                        f"Goal prediction: {predicted_goal_label}"
                        + (f" (confidence {_format_number((confidence or 0) * 100, 1)}%)" if confidence is not None else "")
                        + "."
                    ),
                    (
                        f"توقع الهدف: {predicted_goal_label}"
                        + (f" (ثقة {_format_number((confidence or 0) * 100, 1)}%)" if confidence is not None else "")
                        + "."
                    ),
                    (
                        f"توقع الهدف: {predicted_goal_label}"
                        + (f" (ثقة {_format_number((confidence or 0) * 100, 1)}%)" if confidence is not None else "")
                        + "."
                    ),
                )
                reply_parts.append(goal_reply)
                payload["goal_prediction"] = result
                payload["goal_features_used"] = goal_features
            except FileNotFoundError:
                reply_parts.append(
                    _lang_reply(
                        language,
                        "Goal model is not available yet. Train `model_goal.pkl` first.",
                        "نموذج توقع الهدف غير متاح بعد. درّب `model_goal.pkl` أولًا.",
                        "نموذج توقع الهدف مش جاهز. درّب `model_goal.pkl` أول.",
                    )
                )

    if want_success:
        success_features, missing = _build_success_prediction_payload(profile, tracking_summary)
        if missing:
            reply_parts.append(_ml_missing_fields_reply(language, "success", missing))
        else:
            try:
                result = predict_success(success_features)
                prediction_flag = int(result.get("success_prediction", 0) or 0)
                probability = _to_float(result.get("success_probability"))
                status_text = _lang_reply(
                    language,
                    "likely on track" if prediction_flag == 1 else "at risk / needs adjustment",
                    "غالبًا على المسار الصحيح" if prediction_flag == 1 else "مُعرّض للتأخر ويحتاج تعديل",
                    "غالبًا ماشي صح" if prediction_flag == 1 else "في خطر تأخير وبدها تعديل",
                )
                success_reply = _lang_reply(
                    language,
                    (
                        "Success prediction: "
                        + (f"{_format_number((probability or 0) * 100, 1)}% " if probability is not None else "")
                        + f"({status_text})."
                    ),
                    (
                        "توقع النجاح: "
                        + (f"{_format_number((probability or 0) * 100, 1)}% " if probability is not None else "")
                        + f"({status_text})."
                    ),
                    (
                        "توقع النجاح: "
                        + (f"{_format_number((probability or 0) * 100, 1)}% " if probability is not None else "")
                        + f"({status_text})."
                    ),
                )
                reply_parts.append(success_reply)
                payload["success_prediction"] = result
                payload["success_features_used"] = success_features
            except FileNotFoundError:
                reply_parts.append(
                    _lang_reply(
                        language,
                        "Success model is not available yet. Train `model_success.pkl` first.",
                        "نموذج توقع النجاح غير متاح بعد. درّب `model_success.pkl` أولًا.",
                        "نموذج توقع النجاح مش جاهز. درّب `model_success.pkl` أول.",
                    )
                )

    if not reply_parts:
        return None

    return "\n".join(reply_parts), payload


def _status_label(language: str, status: str) -> str:
    status_key = status.strip().lower()
    if status_key == "ahead of schedule":
        return _lang_reply(language, "Ahead of schedule", "متقدم عن الخطة", "متقدّم عن الخطة")
    if status_key == "behind schedule":
        return _lang_reply(language, "Behind schedule", "متأخر عن الخطة", "متأخر عن الخطة")
    return _lang_reply(language, "On track", "على المسار الصحيح", "على المسار")


def _performance_missing_data_reply(language: str, missing_fields: list[str]) -> str:
    fields_text = ", ".join(missing_fields)
    quick_example = (
        "وزني الحالي 92، هدفي 85، تغير وزني الأسبوعي -0.5"
    )
    return _lang_reply(
        language,
        (
            "I can estimate how long is left, but I need a few missing details: "
            f"{fields_text}. "
            "Send them in plain text, for example: "
            f"{quick_example}"
        ),
        (
            "بقدر أحسب لك كم ضايل، بس ناقصني شوية بيانات: "
            f"{fields_text}. "
            "ابعثهم كتابة بشكل بسيط مثل: "
            f"{quick_example}"
        ),
        (
            "بقدر أحسب لك قديش ضايل، بس ناقصني بيانات: "
            f"{fields_text}. "
            "ابعتهم بشكل بسيط مثل: "
            f"{quick_example}"
        ),
    )

def _basic_progress_reply(language: str, tracking_summary: dict[str, Any]) -> str:
    completed = _to_float(tracking_summary.get("completed_tasks")) or 0
    total = _to_float(tracking_summary.get("total_tasks")) or 0
    adherence = _to_float(tracking_summary.get("adherence_score"))
    if adherence is None and total > 0:
        adherence = completed / total
    percent = int(round((adherence or 0) * 100))
    last7 = _to_float(tracking_summary.get("completed_last_7_days")) or 0
    last_completion = tracking_summary.get("last_completed_at")

    if language == "en":
        parts = [
            f"Progress: {percent}% ({int(completed)}/{int(total)} tasks).",
            f"Last 7 days: {int(last7)} completed.",
        ]
        if last_completion:
            parts.append(f"Last completion: {last_completion}.")
        parts.append("If you want a timeline to your goal, share your current and target weight.")
        return " ".join(parts)

    parts_ar = [
        f"????? {percent}% ({int(completed)}/{int(total)} ????).",
        f"??? 7 ????: {int(last7)} ????.",
    ]
    if last_completion:
        parts_ar.append(f"??? ?????: {last_completion}.")
    parts_ar.append("??? ??? ???? ????? ?????? ???? ???? ?????? ??????.")
    return " ".join(parts_ar)


def _performance_analysis_reply(
    language: str,
    profile: dict[str, Any],
    tracking_summary: Optional[dict[str, Any]],
) -> str:
    if not isinstance(tracking_summary, dict):
        return _performance_missing_data_reply(
            language,
            ["goal.type", "goal.current_weight", "goal.target_weight", "weekly_stats.weight_change or weekly_stats.weight_change_history"],
        )

    goal_data = tracking_summary.get("goal") if isinstance(tracking_summary.get("goal"), dict) else {}
    weekly_stats = (
        tracking_summary.get("weekly_stats")
        if isinstance(tracking_summary.get("weekly_stats"), dict)
        else {}
    )
    monthly_stats = (
        tracking_summary.get("monthly_stats")
        if isinstance(tracking_summary.get("monthly_stats"), dict)
        else {}
    )

    goal_type_raw = _dict_get_any(goal_data, ["type", "goal_type"]) or profile.get("goal")
    goal_type = _normalize_goal(goal_type_raw)

    current_weight = _to_float(
        _dict_get_any(goal_data, ["current_weight", "currentWeight", "weight"]) or profile.get("weight")
    )
    target_weight = _to_float(_dict_get_any(goal_data, ["target_weight", "targetWeight"]))

    weekly_weight_change_point = _to_float(
        _dict_get_any(weekly_stats, ["weight_change", "weekly_weight_change", "weightChange"])
    )
    monthly_weight_change = _to_float(_dict_get_any(monthly_stats, ["weight_change", "monthly_weight_change"]))
    weight_change_series_all = _extract_weight_change_series(tracking_summary, weekly_stats)
    weight_change_series_recent = weight_change_series_all[-4:]
    weekly_weight_change = _average(weight_change_series_recent)
    if weekly_weight_change is None and weekly_weight_change_point is not None:
        weekly_weight_change = weekly_weight_change_point
    if weekly_weight_change is None and monthly_weight_change is not None:
        weekly_weight_change = monthly_weight_change / 4.0

    strength_increase_monthly = _to_float(
        _dict_get_any(monthly_stats, ["strength_increase_percent", "strength_increase_pct", "strength_percent"])
    )
    target_strength_increase = _to_float(
        _dict_get_any(goal_data, ["target_strength_increase_percent", "target_strength_percent"])
    )

    workout_days = _to_float(_dict_get_any(weekly_stats, ["workout_days"]))
    planned_days = _to_float(_dict_get_any(weekly_stats, ["planned_days"]))
    avg_calories = _to_float(_dict_get_any(weekly_stats, ["avg_calories", "average_calories"]))
    avg_protein = _to_float(_dict_get_any(weekly_stats, ["avg_protein", "average_protein"]))
    sleep_avg_hours = _to_float(_dict_get_any(weekly_stats, ["sleep_avg_hours", "sleep_hours"]))

    consistency_percent = _to_float(
        _dict_get_any(monthly_stats, ["consistency_percent", "consistency_pct"])
    )
    if consistency_percent is None:
        adherence_score = _to_float(_dict_get_any(tracking_summary, ["adherence_score"]))
        if adherence_score is not None:
            consistency_percent = adherence_score * 100.0

    trend_weeks_count = len(weight_change_series_recent)
    trend_series_text = ", ".join(f"{value:+.2f}" for value in weight_change_series_recent)
    trend_variability = _mean_abs_deviation(weight_change_series_recent)

    missing_fields: list[str] = []
    weight_goal_mode = goal_type == "fat_loss" or target_weight is not None

    if weight_goal_mode:
        if current_weight is None:
            missing_fields.append("goal.current_weight")
        if target_weight is None:
            missing_fields.append("goal.target_weight")
        if weekly_weight_change is None:
            missing_fields.append("weekly_stats.weight_change or weekly_stats.weight_change_history")
    elif goal_type == "muscle_gain":
        if strength_increase_monthly is None and weekly_weight_change is None:
            missing_fields.append("monthly_stats.strength_increase_percent or weekly_stats.weight_change/weight_change_history")
        if target_weight is None and target_strength_increase is None:
            missing_fields.append("goal.target_weight or goal.target_strength_increase_percent")
    else:
        if weekly_weight_change is None and strength_increase_monthly is None:
            missing_fields.append("weekly_stats.weight_change/weight_change_history or monthly_stats.strength_increase_percent")

    if missing_fields:
        if isinstance(tracking_summary, dict) and (
            tracking_summary.get("completed_tasks") is not None
            or tracking_summary.get("adherence_score") is not None
        ):
            return _basic_progress_reply(language, tracking_summary)
        return _performance_missing_data_reply(language, missing_fields)

    status = "on track"
    weeks_remaining: Optional[float] = None
    remaining_weight: Optional[float] = None

    if target_weight is not None and current_weight is not None and weekly_weight_change is not None:
        remaining_weight = target_weight - current_weight
        if abs(remaining_weight) < 0.05:
            status = "ahead of schedule"
            weeks_remaining = 0.0
        elif abs(weekly_weight_change) < 1e-9:
            status = "behind schedule"
        else:
            toward_target = weekly_weight_change * remaining_weight > 0
            if not toward_target:
                status = "behind schedule"
            else:
                weeks_remaining = abs(remaining_weight) / abs(weekly_weight_change)
                weekly_pct = abs(weekly_weight_change) / max(current_weight, 1e-6) * 100.0
                if goal_type == "fat_loss":
                    if weekly_pct > 1.0:
                        status = "ahead of schedule"
                    elif weekly_pct >= 0.25:
                        status = "on track"
                    else:
                        status = "behind schedule"
                elif goal_type == "muscle_gain":
                    if weekly_pct > 0.5:
                        status = "ahead of schedule"
                    elif weekly_pct >= 0.1:
                        status = "on track"
                    else:
                        status = "behind schedule"
                else:
                    status = "on track"

                if trend_weeks_count >= 2:
                    toward_weeks = sum(1 for change in weight_change_series_recent if (change * remaining_weight) > 0)
                    toward_ratio = toward_weeks / trend_weeks_count
                    if toward_ratio < 0.5:
                        status = "behind schedule"
                    elif toward_ratio < 0.75 and status == "ahead of schedule":
                        status = "on track"

                    if trend_variability is not None and abs(weekly_weight_change) > 1e-9:
                        variability_ratio = trend_variability / abs(weekly_weight_change)
                        if variability_ratio > 1.6:
                            status = "behind schedule"
                        elif variability_ratio > 1.1 and status == "ahead of schedule":
                            status = "on track"

    elif goal_type == "muscle_gain" and target_strength_increase is not None and strength_increase_monthly is not None:
        if strength_increase_monthly <= 0:
            status = "behind schedule"
        else:
            strength_remaining = max(0.0, target_strength_increase - strength_increase_monthly)
            weeks_remaining = (strength_remaining / strength_increase_monthly) * 4.0
            if strength_increase_monthly >= 5.0:
                status = "ahead of schedule"
            elif strength_increase_monthly > 0:
                status = "on track"
            else:
                status = "behind schedule"

    if consistency_percent is not None and consistency_percent < 70.0:
        status = "behind schedule"

    status_text = _status_label(language, status)
    weeks_text = "N/A" if weeks_remaining is None else f"{weeks_remaining:.1f}"

    workout_adherence_line = "N/A"
    if workout_days is not None and planned_days is not None and planned_days > 0:
        workout_adherence_line = f"{(workout_days / planned_days) * 100:.0f}% ({int(workout_days)}/{int(planned_days)} days)"

    calorie_target = _to_float(_dict_get_any(weekly_stats, ["target_calories"])) or _to_float(profile.get("target_calories"))
    calorie_delta: Optional[float] = None
    if avg_calories is not None and calorie_target is not None:
        calorie_delta = avg_calories - calorie_target

    recommendations: list[str] = []
    if goal_type == "fat_loss":
        if calorie_delta is not None and calorie_delta > 0:
            recommendations.append(f"Calories: reduce daily intake by ~{int(min(300, max(120, calorie_delta)))} kcal to match deficit target.")
        elif status == "ahead of schedule":
            recommendations.append("Calories: fat loss speed is high; add 100-150 kcal/day to protect recovery and muscle.")
        else:
            recommendations.append("Training volume: keep 10-16 hard sets per major muscle/week; add +2 sets for weak muscles if needed.")
    elif goal_type == "muscle_gain":
        if status == "behind schedule":
            recommendations.append("Volume: increase by +2 to +4 hard sets per target muscle/week and track progressive overload.")
        else:
            recommendations.append("Volume: keep current progression; maintain controlled overload weekly.")
        if calorie_delta is not None and calorie_delta < 0:
            recommendations.append(f"Calories: add ~{int(min(300, max(120, abs(calorie_delta))))} kcal/day to support muscle gain.")
    else:
        recommendations.append("Volume: adjust weekly load by +/-10% based on fatigue and performance trend.")

    if avg_protein is not None and current_weight is not None:
        protein_per_kg = avg_protein / max(current_weight, 1e-6)
        if protein_per_kg < 1.6:
            recommendations.append("Protein: increase toward 1.6-2.2 g/kg/day for better adaptation.")
    if sleep_avg_hours is not None and sleep_avg_hours < 7.0:
        recommendations.append("Recovery: increase sleep to 7-9 h/night to improve strength and body-composition progress.")

    if not recommendations:
        recommendations.append("Keep consistency high and review weekly data before adjusting plan variables.")

    recommendations_block = "\n".join(f"{idx}. {text}" for idx, text in enumerate(recommendations[:3], start=1))

    if trend_weeks_count >= 2:
        rate_line_en = f"Rate of progress (trend last {trend_weeks_count} weeks): {_format_number(weekly_weight_change)} kg/week"
        rate_line_ar_fusha = f"معدل التقدم (اتجاه آخر {trend_weeks_count} أسابيع): {_format_number(weekly_weight_change)} كغ/أسبوع"
        rate_line_ar_jordanian = f"معدل التقدم (اتجاه آخر {trend_weeks_count} أسابيع): {_format_number(weekly_weight_change)} كيلو/أسبوع"
        trend_details_en = f"Recent weekly changes: {trend_series_text} kg/week\n"
        trend_details_ar_fusha = f"تغيرات الأسابيع الأخيرة: {trend_series_text} كغ/أسبوع\n"
        trend_details_ar_jordanian = f"تغيرات آخر الأسابيع: {trend_series_text} كيلو/أسبوع\n"
    else:
        rate_line_en = f"Rate of progress: {_format_number(weekly_weight_change)} kg/week"
        rate_line_ar_fusha = f"معدل التقدم: {_format_number(weekly_weight_change)} كغ/أسبوع"
        rate_line_ar_jordanian = f"معدل التقدم: {_format_number(weekly_weight_change)} كيلو/أسبوع"
        trend_details_en = ""
        trend_details_ar_fusha = ""
        trend_details_ar_jordanian = ""

    if trend_weeks_count == 0:
        if weekly_weight_change_point is not None:
            trend_details_en = "Rate source: single weekly point.\n"
            trend_details_ar_fusha = "مصدر المعدل: نقطة أسبوعية واحدة.\n"
            trend_details_ar_jordanian = "مصدر المعدل: نقطة أسبوعية وحدة.\n"
        elif monthly_weight_change is not None:
            trend_details_en = "Rate source: monthly change divided by 4.\n"
            trend_details_ar_fusha = "مصدر المعدل: التغير الشهري مقسوم على 4.\n"
            trend_details_ar_jordanian = "مصدر المعدل: التغير الشهري مقسوم على 4.\n"

    return _lang_reply(
        language,
        (
            f"Status: {status_text}\n"
            + rate_line_en
            + (f" | Strength: {_format_number(strength_increase_monthly)}%/month" if strength_increase_monthly is not None else "")
            + "\n"
            + trend_details_en
            + (
                f"Remaining weight difference: {_format_number(remaining_weight)} kg\n"
                if remaining_weight is not None
                else ""
            )
            + f"Estimated time to target: {weeks_text} weeks\n"
            + f"Consistency: {_format_number(consistency_percent, 1)}% | Workout adherence: {workout_adherence_line}\n"
            + (
                f"Calories: avg {_format_number(avg_calories, 0)} kcal"
                + (f" vs target {_format_number(calorie_target, 0)} ({_format_number(calorie_delta, 0)} delta)" if calorie_target is not None and calorie_delta is not None else "")
                + "\n"
                if avg_calories is not None
                else ""
            )
            + "Recommendations:\n"
            + recommendations_block
        ),
        (
            f"الحالة: {status_text}\n"
            + rate_line_ar_fusha
            + (f" | القوة: {_format_number(strength_increase_monthly)}%/شهر" if strength_increase_monthly is not None else "")
            + "\n"
            + trend_details_ar_fusha
            + (
                f"فرق الوزن المتبقي: {_format_number(remaining_weight)} كغ\n"
                if remaining_weight is not None
                else ""
            )
            + f"الوقت المتوقع للوصول للهدف: {weeks_text} أسبوع\n"
            + f"نسبة الالتزام: {_format_number(consistency_percent, 1)}% | التزام التمرين: {workout_adherence_line}\n"
            + (
                f"السعرات: متوسط {_format_number(avg_calories, 0)} سعرة"
                + (f" مقابل الهدف {_format_number(calorie_target, 0)} (فرق {_format_number(calorie_delta, 0)})" if calorie_target is not None and calorie_delta is not None else "")
                + "\n"
                if avg_calories is not None
                else ""
            )
            + "التوصيات:\n"
            + recommendations_block
        ),
        (
            f"الحالة: {status_text}\n"
            + rate_line_ar_jordanian
            + (f" | القوة: {_format_number(strength_increase_monthly)}%/شهر" if strength_increase_monthly is not None else "")
            + "\n"
            + trend_details_ar_jordanian
            + (
                f"فرق الوزن المتبقي: {_format_number(remaining_weight)} كيلو\n"
                if remaining_weight is not None
                else ""
            )
            + f"الوقت المتوقع توصل للهدف: {weeks_text} أسبوع\n"
            + f"الالتزام: {_format_number(consistency_percent, 1)}% | التزام التمرين: {workout_adherence_line}\n"
            + (
                f"السعرات: متوسط {_format_number(avg_calories, 0)}"
                + (f" مقابل الهدف {_format_number(calorie_target, 0)} (فرق {_format_number(calorie_delta, 0)})" if calorie_target is not None and calorie_delta is not None else "")
                + "\n"
                if avg_calories is not None
                else ""
            )
            + "التوصيات:\n"
            + recommendations_block
        ),
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
    def _detect_user_mood(text: str) -> str:
        normalized = normalize_text(text or "")
        if not normalized:
            return "neutral"
        tired_tokens = {"tired", "exhausted", "fatigued", "sleepy", "مرهق", "تعبان", "تعبانة", "مجهد", "نعسان"}
        discouraged_tokens = {"frustrated", "down", "sad", "demotivated", "discouraged", "محبط", "زعلان", "حاسس تعبان", "مخنوق"}
        motivated_tokens = {"motivated", "excited", "ready", "energetic", "متحمس", "جاهز", "نشاط"}
        injured_tokens = {"injured", "pain", "hurt", "injury", "اصابة", "وجع", "الم", "انصبت"}
        if _contains_any(normalized, injured_tokens):
            return "injured"
        if _contains_any(normalized, discouraged_tokens):
            return "discouraged"
        if _contains_any(normalized, tired_tokens):
            return "tired"
        if _contains_any(normalized, motivated_tokens):
            return "motivated"
        return "neutral"

    def _dashboard_summary(tracking: Optional[dict[str, Any]]) -> str:
        if not isinstance(tracking, dict):
            return ""
        weekly_stats = tracking.get("weekly_stats") if isinstance(tracking.get("weekly_stats"), dict) else {}
        monthly_stats = tracking.get("monthly_stats") if isinstance(tracking.get("monthly_stats"), dict) else {}
        workouts_week = _to_float(_dict_get_any(weekly_stats, ["workout_days", "completed_workouts", "sessions"]))
        streak = _to_float(_dict_get_any(tracking, ["streak_days", "current_streak", "streak"]))
        calories_burned = _to_float(
            _dict_get_any(weekly_stats, ["calories_burned", "avg_calories_burned", "calories_burned_avg"])
        )
        if calories_burned is None:
            calories_burned = _to_float(_dict_get_any(monthly_stats, ["avg_calories_burned", "calories_burned"]))
        weekly_summary = []
        if workouts_week is not None:
            weekly_summary.append(f"workouts/week: {int(workouts_week)}")
        if streak is not None:
            weekly_summary.append(f"streak: {int(streak)} days")
        if calories_burned is not None:
            weekly_summary.append(f"calories burned: {int(calories_burned)}")
        if not weekly_summary:
            return ""
        return " | ".join(weekly_summary)

    def _notification_suggestions(lang: str) -> str:
        if lang == "ar_jordanian":
            return "نوتيفكيشن يومي للتمرين، ملخص أسبوعي، ودَفعة تحفيز بأوقات النشاط."
        if lang == "ar_fusha":
            return "إشعارات يومية للتمارين، ملخص أسبوعي، ورسالة تحفيزية في أوقات النشاط."
        return "Daily workout reminder, weekly summary, and motivational boost at peak engagement time."

    def _extract_style_profile(profile_data: dict[str, Any]) -> dict[str, Any] | None:
        style_keys = (
            "speaking_style",
            "response_style",
            "style",
            "chat_style",
            "json_style",
            "tone_profile",
        )
        # direct keys
        for key in style_keys:
            value = profile_data.get(key)
            if isinstance(value, dict):
                return value
            if isinstance(value, str) and value.strip().startswith("{"):
                try:
                    return json.loads(value)
                except Exception:
                    continue
        # nested preferences
        prefs = profile_data.get("preferences")
        if isinstance(prefs, dict):
            for key in style_keys:
                value = prefs.get(key)
                if isinstance(value, dict):
                    return value
                if isinstance(value, str) and value.strip().startswith("{"):
                    try:
                        return json.loads(value)
                    except Exception:
                        continue
        return None

    def _style_blob(style_profile: dict[str, Any] | None) -> str:
        if not style_profile:
            return ""
        try:
            return json.dumps(style_profile, ensure_ascii=False)
        except Exception:
            return ""

    def _style_prefers_emojis(style_profile: dict[str, Any] | None) -> bool:
        if not style_profile:
            return False
        value = style_profile.get("emoji_usage") if isinstance(style_profile, dict) else None
        if value is None:
            value = style_profile.get("emojiUsage") if isinstance(style_profile, dict) else None
        if value is None:
            value = style_profile.get("emojis") if isinstance(style_profile, dict) else None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"low", "medium", "high", "yes", "true"}
        return False

    def _style_guidelines(style_profile: dict[str, Any] | None) -> str:
        if not isinstance(style_profile, dict) or not style_profile:
            return ""

        def _pick(keys: tuple[str, ...]) -> Optional[str]:
            for key in keys:
                value = style_profile.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()
            return None

        tone = _pick(("tone", "style_tone", "response_tone"))
        sentence_len = _pick(("sentenceLength", "sentence_length", "length"))
        emoji_usage = _pick(("emojiUsage", "emoji_usage", "emojis"))
        motivation = _pick(("motivationLevel", "motivation_level", "motivation"))

        lines: list[str] = []
        if tone == "friendly":
            lines.append("Tone: friendly, warm, supportive.")
        elif tone == "neutral":
            lines.append("Tone: calm, professional, and concise.")
        elif tone == "tough":
            lines.append("Tone: direct, no-nonsense, and motivating.")

        if sentence_len == "short":
            lines.append("Sentence length: short (1-2 sentences).")
        elif sentence_len == "medium":
            lines.append("Sentence length: medium (3-5 sentences).")
        elif sentence_len == "long":
            lines.append("Sentence length: long (6-9 sentences).")

        if emoji_usage == "none":
            lines.append("Emojis: none.")
        elif emoji_usage == "low":
            lines.append("Emojis: low (max 1 emoji).")
        elif emoji_usage == "medium":
            lines.append("Emojis: medium (1-2 emojis).")
        elif emoji_usage == "high":
            lines.append("Emojis: high (2-4 emojis).")

        if motivation == "low":
            lines.append("Motivation: gentle encouragement.")
        elif motivation == "medium":
            lines.append("Motivation: balanced encouragement.")
        elif motivation == "high":
            lines.append("Motivation: energetic and high-intensity encouragement.")

        return "\n".join(lines)

    def _ensure_motivational_opening(
        text: str,
        lang: str,
        style_profile: dict[str, Any] | None,
        mood: str = "neutral",
    ) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return text
        lowered = cleaned.lower()
        motivational_prefixes = {
            "en": [
                "great job",
                "awesome",
                "well done",
                "you got this",
                "nice work",
                "excellent",
            ],
            "ar_fusha": [
                "أحسنت",
                "عمل رائع",
                "ممتاز",
                "أنت قادر",
            ],
            "ar_jordanian": [
                "شغل ممتاز",
                "أحسنت",
                "ممتاز",
                "انت قدها",
            ],
        }
        prefixes = motivational_prefixes.get(lang, motivational_prefixes["en"])
        if any(lowered.startswith(p) for p in prefixes):
            return cleaned
        emoji = " 💪" if _style_prefers_emojis(style_profile) else ""
        if mood == "discouraged":
            default_openings = {
                "en": f"You've done great so far{emoji}.",
                "ar_fusha": f"لقد أحسنت حتى الآن{emoji}.",
                "ar_jordanian": f"شغلك ممتاز لهلأ{emoji}.",
            }
        elif mood == "tired":
            default_openings = {
                "en": f"Easy pace is still progress{emoji}.",
                "ar_fusha": f"الخطى الهادئة ما زالت تقدّمًا{emoji}.",
                "ar_jordanian": f"حتى الوتيرة الهادية بتقدم{emoji}.",
            }
        else:
            default_openings = {
                "en": f"Great effort{emoji}!",
                "ar_fusha": f"أحسنت{emoji}!",
                "ar_jordanian": f"شغل ممتاز{emoji}!",
            }
        opening = default_openings.get(lang, default_openings["en"])
        return f"{opening}\n{cleaned}"

    language_instructions = {
        "en": "Reply in clear English.",
        "ar_fusha": "رد باللغة العربية الفصحى.",
        "ar_jordanian": "احكِ باللهجة الأردنية بشكل واضح.",
    }.get(language, "Reply in English.")

    display_name = _profile_display_name(profile)
    state = state or {}
    plan_snapshot = state.get("plan_snapshot", {})
    coach_memory = state.get("coach_memory") if isinstance(state, dict) else None
    rag_relevant = (
        _is_workout_plan_request(user_message)
        or _is_nutrition_plan_request(user_message)
        or _is_nutrition_knowledge_query(user_message)
        or _contains_any(user_message, PROGRESS_KEYWORDS | PERFORMANCE_ANALYSIS_KEYWORDS)
    )
    nutrition_kb_context = _nutrition_kb_context(user_message, profile, top_k=2) if rag_relevant else ""
    rag_context = _build_chat_rag_context(user_message, profile) if rag_relevant else ""

    style_profile = _extract_style_profile(profile)
    style_json = _style_blob(style_profile)
    style_guidelines = _style_guidelines(style_profile)
    detected_mood = _detect_user_mood(user_message)
    stats = compute_stats(tracking_summary)
    analytics_summary = dashboard_summary(stats)
    insights = generate_insights(stats, language)
    memory_summary = _truncate_text(summarize_memory((coach_memory or {}).get("items", [])), 700)
    active_mode = state.get("active_mode", CHAT_MODE)

    combined_rag = _truncate_text("\n".join([c for c in [nutrition_kb_context, rag_context] if c]), 1600)
    system_prompt = build_system_prompt(
        language=language,
        profile=profile,
        memory_summary=memory_summary,
        rag_context=combined_rag,
        analytics_summary=analytics_summary,
        mode=active_mode,
        sentiment=detected_mood,
        style_json=style_json,
    )
    if style_guidelines:
        system_prompt += f"\nStyle rules:\n{style_guidelines}\n"

    context_lines = [
        f"User name: {display_name or 'Unknown'}",
        f"Tracking summary: {_compact_tracking_summary_for_prompt(tracking_summary)}",
        f"Plan snapshot: {plan_snapshot or {}}",
        f"Plans recently deleted flag: {bool(state.get('plans_recently_deleted', False))}",
        f"Detected mood: {detected_mood}",
    ]
    if insights:
        context_lines.append(f"Analytics insights: {insights}")
    messages = [{"role": "system", "content": system_prompt + '\n'.join(context_lines)}]

    external_history = _normalize_recent_messages(recent_messages)
    if external_history:
        messages.extend(external_history[-10:])
    else:
        messages.extend(memory.get_conversation_history()[-8:])

    last_history_text = normalize_text(messages[-1]["content"]) if len(messages) > 1 else ""
    if last_history_text != normalize_text(user_message):
        messages.append({"role": "user", "content": user_message})
    reply = LLM.chat_completion(messages, max_tokens=CHAT_LLM_MAX_TOKENS)
    reply = _ensure_motivational_opening(str(reply), language, style_profile, detected_mood)
    return post_process_response(reply, language, profile)


def _build_chat_rag_context(user_message: str, profile: dict[str, Any]) -> str:
    rag_lines: list[str] = []
    if RAG_SERVICE:
        try:
            hits = RAG_SERVICE.query(user_message, top_k=2)
            if hits:
                rag_lines.append("FAISS RAG hits:")
                for hit in hits:
                    src = hit.get("source")
                    score = hit.get("score")
                    text = hit.get("text")
                    rag_lines.append(f"[{src} | score={score:.3f}] {text}")
        except Exception as exc:
            logger.warning("FAISS RAG query failed: %s", exc)
    if _training_pipeline_ready():
        try:
            context = training_pipeline.build_rag_context(user_message, profile)
            if context:
                rag_lines.append(context)
        except Exception as exc:
            logger.warning("Training pipeline RAG context failed: %s", exc)
    try:
        fallback_context = _get_rag_builder().build(user_message, profile, top_k=2)
        if fallback_context:
            rag_lines.append(fallback_context)
    except Exception:
        pass
    return "\n".join([line for line in rag_lines if line])


@app.get("/health")
def health() -> dict[str, Any]:
    dataset_summary = DATASET_REGISTRY.summary()
    return {
        "status": "ok",
        "provider": LLM.active_provider,
        "model": LLM.active_model,
        "chat_response_mode": CHAT_RESPONSE_MODE,
        "response_dataset_source": str(RESPONSE_DATASET_DIR),
        "nutrition_knowledge_loaded": NUTRITION_KB.ready,
        "nutrition_knowledge_source": str(NUTRITION_KB.data_path),
        "dataset_registry_files": dataset_summary.get("files_count", 0),
        "dataset_registry_generated_at": dataset_summary.get("generated_at"),
        "training_pipeline_status": TRAINING_PIPELINE_STATUS,
        "rag_status": RAG_STATUS,
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
            "tracking_data_extraction",
            "deterministic_performance_analysis",
            "four_week_trend_scoring",
            "ml_goal_prediction",
            "ml_success_prediction",
            "ml_plan_intent_prediction",
            "logic_engine_metrics",
            "dataset_registry_all_files",
        ],
    }


@app.post("/ai/personalized-plan")
async def get_personalized_plan(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a complete personalized fitness & nutrition plan using multi-dataset training.
    
    Args:
        user_profile: User profile with goals, fitness level, health conditions, etc.
        
    Returns:
        Complete personalized plan with workouts, nutrition, expectations
    """
    global training_pipeline
    
    if training_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Training pipeline not initialized. Using standard recommender instead."
        )
    
    try:
        plan = training_pipeline.get_personalized_plan(user_profile)
        return {
            "status": "success",
            "plan": plan,
            "source": "multi_dataset_training_system"
        }
    except Exception as e:
        logger.error(f"Error generating personalized plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/personalized-exercises")
async def get_personalized_exercises(
    user_profile: Dict[str, Any],
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """
    Get personalized exercise recommendations ranked by suitability.
    
    Args:
        user_profile: User profile
        limit: Max number of recommendations (1-50)
        
    Returns:
        List of personalized exercises with suitability scores
    """
    global training_pipeline
    
    if training_pipeline is None:
        raise HTTPException(status_code=503, detail="Training pipeline not available")
    
    try:
        exercises = training_pipeline.get_personalized_exercises(user_profile, limit)
        return {
            "status": "success",
            "count": len(exercises),
            "exercises": exercises,
            "source": "multi_dataset_training_system"
        }
    except Exception as e:
        logger.error(f"Error getting personalized exercises: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/personalized-foods")
async def get_personalized_foods(
    user_profile: Dict[str, Any],
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get personalized food recommendations ranked by suitability.
    
    Args:
        user_profile: User profile
        limit: Max number of recommendations (1-100)
        
    Returns:
        List of personalized foods with nutritional info and suitability scores
    """
    global training_pipeline
    
    if training_pipeline is None:
        raise HTTPException(status_code=503, detail="Training pipeline not available")
    
    try:
        foods = training_pipeline.get_personalized_foods(user_profile, limit)
        return {
            "status": "success",
            "count": len(foods),
            "foods": foods,
            "source": "multi_dataset_training_system"
        }
    except Exception as e:
        logger.error(f"Error getting personalized foods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/rag-context")
async def build_rag_context(query: str, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build RAG (Retrieval-Augmented Generation) context from training data.
    Use this to enhance LLM responses with relevant dataset information.
    
    Args:
        query: User's query/question
        user_profile: Optional user profile for personalization
        
    Returns:
        Rich context for LLM integration
    """
    global training_pipeline
    
    if training_pipeline is None:
        raise HTTPException(status_code=503, detail="Training pipeline not available")
    
    try:
        context = training_pipeline.build_rag_context(query, user_profile)
        return {
            "status": "success",
            "context": context,
            "source": "multi_dataset_training_system"
        }
    except Exception as e:
        logger.error(f"Error building RAG context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ai/training-status")
async def training_status() -> Dict[str, Any]:
    """Get training system status and statistics."""
    global training_pipeline
    
    if training_pipeline is None:
        return {
            "status": "not_initialized",
            "trained": False,
            "message": "Training pipeline not available"
        }
    
    try:
        summary = training_pipeline.get_summary()
        return {
            "status": "ready",
            "trained": summary["trained"],
            **summary
        }
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/datasets/summary")
def datasets_summary() -> dict[str, Any]:
    return {"status": "ok", "summary": DATASET_REGISTRY.summary()}


@app.get("/datasets/search")
def datasets_search(q: str = Query(..., min_length=1), top_k: int = Query(10, ge=1, le=100)) -> dict[str, Any]:
    results = DATASET_REGISTRY.search(q, top_k=top_k)
    return {"status": "ok", "query": q, "count": len(results), "results": results}


@app.get("/datasets/tag/{tag}")
def datasets_by_tag(tag: str) -> dict[str, Any]:
    items = DATASET_REGISTRY.tagged_files(tag)
    slim = [
        {
            "relative_path": item.get("relative_path"),
            "category": item.get("category"),
            "extension": item.get("extension"),
            "size_bytes": item.get("size_bytes"),
            "tags": item.get("tags", []),
        }
        for item in items
    ]
    return {"status": "ok", "tag": tag, "count": len(slim), "files": slim}


@app.post("/ml/predict-goal")
def ml_predict_goal(req: GoalPredictionRequest) -> dict[str, Any]:
    try:
        payload = req.model_dump()
        result = predict_goal(payload)
        return {"status": "ok", "prediction": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=f"Goal model unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Goal prediction failed: {exc}") from exc


@app.post("/ml/predict-success")
def ml_predict_success(req: SuccessPredictionRequest) -> dict[str, Any]:
    try:
        payload = req.model_dump()
        result = predict_success(payload)
        return {"status": "ok", "prediction": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=f"Success model unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Success prediction failed: {exc}") from exc


@app.post("/ml/predict-plan-intent")
def ml_predict_plan_intent(req: PlanIntentPredictionRequest) -> dict[str, Any]:
    try:
        result = predict_plan_intent(req.message)
        return {"status": "ok", "prediction": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=f"Plan-intent model unavailable: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Plan-intent prediction failed: {exc}") from exc


@app.post("/logic/evaluate")
def logic_evaluate(req: LogicEvaluationRequest) -> dict[str, Any]:
    try:
        metrics = evaluate_logic_metrics(
            start_value=req.start_value,
            current_value=req.current_value,
            target_value=req.target_value,
            direction=req.direction,
            weight_history=req.weight_history,
            previous_value=req.previous_value,
            elapsed_weeks=req.elapsed_weeks,
        )
        return {"status": "ok", "metrics": metrics.__dict__}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Logic evaluation failed: {exc}") from exc


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    user_id = _normalize_user_id(req.user_id)
    conversation_id = _normalize_conversation_id(req.conversation_id, user_id)
    state = _get_user_state(user_id)
    _load_coach_memory(user_id, state)
    incoming_profile = req.user_profile if isinstance(req.user_profile, dict) else {}
    db_context = _get_supabase_user_context(user_id, state)
    db_profile_payload = db_context.get("profile_payload") if isinstance(db_context, dict) else {}
    db_tracking_summary = db_context.get("tracking_summary") if isinstance(db_context, dict) else None
    db_plan_snapshot = db_context.get("plan_snapshot") if isinstance(db_context, dict) else None

    effective_profile_payload: dict[str, Any] = {}
    if isinstance(db_profile_payload, dict):
        effective_profile_payload.update(db_profile_payload)
    if isinstance(incoming_profile, dict):
        effective_profile_payload.update(incoming_profile)

    effective_tracking_summary = db_tracking_summary if isinstance(db_tracking_summary, dict) else {}
    if isinstance(req.tracking_summary, dict):
        effective_tracking_summary = _merge_tracking_summaries(effective_tracking_summary, req.tracking_summary)

    effective_plan_snapshot = req.plan_snapshot if isinstance(req.plan_snapshot, dict) else db_plan_snapshot

    explicit_profile = incoming_profile
    explicit_keys = set(explicit_profile.keys())
    if "chronicConditions" in explicit_keys:
        explicit_keys.add("chronic_diseases")
    if "fitnessLevel" in explicit_keys:
        explicit_keys.add("fitness_level")
    if "trainingDaysPerWeek" in explicit_keys:
        explicit_keys.add("training_days_per_week")
    if "activityLevel" in explicit_keys:
        explicit_keys.add("activity_level")
    if "equipment" in explicit_keys:
        explicit_keys.add("available_equipment")
    if "dietaryPreferences" in explicit_keys:
        explicit_keys.add("dietary_preferences")
    profile = _build_profile(req, state, profile_payload=effective_profile_payload)
    language = _detect_language(req.language or "en", req.message, profile)
    recent_messages = _normalize_recent_messages(req.recent_messages)

    _persist_profile_context(profile, state, explicit_keys)
    if effective_tracking_summary:
        state["last_progress_summary"] = _merge_tracking_summaries(
            state.get("last_progress_summary"),
            effective_tracking_summary,
        )
    _update_plan_snapshot_state(state, effective_plan_snapshot)
    tracking_summary = state.get("last_progress_summary")

    user_input = _repair_mojibake(req.message.strip())
    memory = _get_memory_session(user_id, conversation_id)

    def _rewrite_with_llm(draft: str, hint: str = "") -> str:
        draft_clean = _sanitize_dataset_template_text(draft, language, profile)
        if not draft_clean:
            return draft_clean
        instruction = (
            "Rewrite and enhance the assistant reply in a natural coaching voice. "
            "Do not add new facts. Do not create new workout or nutrition plans. "
            "Preserve any numbers, names, and plan details exactly. "
            "If the draft is a redirection, keep it polite and in-domain. "
            "Never output raw placeholders or template tokens."
        )
        if hint:
            instruction = f"{instruction} Additional constraints: {hint}"
        prompt = f"{instruction}\n\nUser message: {user_input}\nDraft reply:\n{draft_clean}"
        rewritten = _general_llm_reply(
            user_message=prompt,
            language=language,
            profile=profile,
            tracking_summary=tracking_summary,
            memory=memory,
            state=state,
            recent_messages=recent_messages,
        )
        if rewritten.startswith("Ollama error:") or rewritten.startswith("Ollama is not reachable"):
            return draft_clean
        return _sanitize_dataset_template_text(rewritten, language, profile)

    def _finalize(text: str, source: str = "system", hint: str = "") -> str:
        final_text = _sanitize_dataset_template_text(text, language, profile)
        rewrite_block_hints = (
            "ask only for the missing field",
            "preserve all plan details exactly",
            "confirm approval briefly",
            "acknowledge rejection",
        )
        allow_llm_rewrite = FORCE_LLM_RESPONSE and source != "llm"
        if hint and any(token in hint.lower() for token in rewrite_block_hints):
            allow_llm_rewrite = False
        if allow_llm_rewrite:
            final_text = _rewrite_with_llm(text, hint=hint)
        final_text = _sanitize_dataset_template_text(final_text, language, profile)
        final_text = post_process_response(final_text, language, profile)
        return _sanitize_dataset_template_text(final_text, language, profile)

    if not user_input:
        if CHAT_RESPONSE_MODE == "dataset_only":
            reply = _dataset_intent_response("out_of_scope", language, seed="empty") or _dataset_fallback_reply(
                language, seed="empty"
            )
        else:
            reply = "Please send a valid message." if language == "en" else "أرسل رسالة واضحة."
        reply = _finalize(reply, hint="Keep it short and polite.")
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
        )

    # Update profile context from free-text (injuries, allergies, goals, etc.)
    extracted_updates = _extract_profile_updates_from_message(user_input)
    if extracted_updates:
        for key, value in extracted_updates.items():
            state[key] = value
        profile = _build_profile(req, state, profile_payload=effective_profile_payload)
        _persist_profile_context(profile, state)

    message_tracking_summary = _extract_tracking_summary_from_message(user_input, profile)
    if message_tracking_summary:
        tracking_summary = _merge_tracking_summaries(tracking_summary, message_tracking_summary)
        state["last_progress_summary"] = tracking_summary

    # Persist coach memory snapshot for long-term personalization
    _persist_coach_memory(user_id, _build_coach_memory_update(profile, tracking_summary), state)

    memory.add_user_message(user_input)
    _, has_bad_words = MODERATION.filter_content(user_input, language=language)
    if has_bad_words:
        if CHAT_RESPONSE_MODE == "dataset_only":
            fallback = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
                language, seed=user_input
            )
        else:
            fallback = MODERATION.get_safe_fallback(language)
        fallback = _finalize(fallback)
        memory.add_assistant_message(fallback)
        return ChatResponse(reply=fallback, conversation_id=conversation_id, language=language)

    lowered = normalize_text(user_input)

    # If user asks for more options after a recommendation
    if _contains_any(user_input, PLAN_REFRESH_KEYWORDS) and state.get("last_plan_candidates"):
        candidates = state.get("last_plan_candidates") or []
        plan_type = state.get("last_plan_type") or "workout"
        options = candidates[:5]
        if options:
            state["pending_plan_options"] = {
                "plan_type": plan_type,
                "options": options,
                "conversation_id": conversation_id,
            }
            reply = _format_plan_options_preview(plan_type, options, language)
            reply = _finalize(reply, hint="Preserve all plan details exactly.")
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="choose_plan",
                data={"plan_type": plan_type, "options_count": len(options)},
            )

    pending_options_payload = state.get("pending_plan_options")
    if pending_options_payload:
        pending_conv = pending_options_payload.get("conversation_id")
        if pending_conv and pending_conv != conversation_id:
            state["pending_plan_options"] = None
            pending_options_payload = None
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
            reply = _finalize(reply, hint="Preserve all plan details exactly.")
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="ask_plan",
                data={"plan_id": plan_id, "plan_type": pending_options_type, "plan": selected_plan},
            )

        if _contains_any(user_input, PLAN_REFRESH_KEYWORDS):
            profile = _build_profile(req, state, profile_payload=effective_profile_payload)
            if pending_options_type == "nutrition":
                refreshed_options = _generate_nutrition_plan_options(profile, language, count=5)
            else:
                refreshed_options = _generate_workout_plan_options(profile, language, count=5)
            state["pending_plan_options"] = {
                "plan_type": pending_options_type,
                "options": refreshed_options,
                "conversation_id": conversation_id,
            }
            reply = _format_plan_options_preview(pending_options_type, refreshed_options, language)
            reply = _finalize(reply, hint="Preserve all plan details exactly.")
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="choose_plan",
                data={"plan_type": pending_options_type, "options_count": len(refreshed_options)},
            )

        reply = _format_plan_options_preview(pending_options_type, pending_options, language)
        reply = _finalize(reply, hint="Preserve all plan details exactly.")
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="choose_plan",
            data={"plan_type": pending_options_type, "options_count": len(pending_options)},
        )

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
            reply = _finalize(reply, hint="Confirm approval briefly and stay in-domain.")
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
            reply = _finalize(reply, hint="Acknowledge rejection and ask what to change.")
            memory.add_assistant_message(reply)
            return ChatResponse(
                reply=reply,
                conversation_id=conversation_id,
                language=language,
                action="plan_rejected",
                data={"plan_id": latest_plan_id},
            )

    pending_field = state.get("pending_field")
    pending_field_conversation_id = state.get("pending_field_conversation_id")
    if pending_field and pending_field_conversation_id and pending_field_conversation_id != conversation_id:
        pending_field = None
        state["pending_field"] = None
        state["pending_field_conversation_id"] = None
        state["pending_plan_type"] = None
    if pending_field:
        if _apply_profile_answer(pending_field, user_input, state):
            state["pending_field"] = None
            state["pending_field_conversation_id"] = None
            pending_plan_type = state.get("pending_plan_type")
            profile = _build_profile(req, state, profile_payload=effective_profile_payload)
            if pending_plan_type:
                missing = _missing_fields_for_plan(pending_plan_type, profile)
                if missing:
                    state["pending_field"] = missing[0]
                    state["pending_field_conversation_id"] = conversation_id
                    question = _missing_field_question(missing[0], language)
                    question = _finalize(question, hint=f"Ask only for the missing field: {missing[0]}.")
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
                reply = _finalize(reply, hint="Preserve all plan details exactly.")
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
            question = _finalize(question, hint=f"Ask only for the missing field: {pending_field}.")
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
        if not diag_in_domain or CHAT_RESPONSE_MODE == "dataset_only":
            state["pending_diagnostic"] = None
            state["pending_diagnostic_conversation_id"] = None
            out_reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
                language, seed=user_input
            )
            out_reply = _finalize(out_reply, hint="Keep it a polite fitness/nutrition redirection only.")
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
        diagnostic_reply = _finalize(diagnostic_reply, source="llm")
        memory.add_assistant_message(diagnostic_reply)
        return ChatResponse(reply=diagnostic_reply, conversation_id=conversation_id, language=language)

    # Strict dataset mode:
    # - Chat replies are sourced only from conversation_intents.json.
    # - Plan options are sourced only from workout_programs.json / nutrition_programs.json.
    # - Legacy non-dataset flows are disabled.
    state["pending_field"] = None
    state["pending_field_conversation_id"] = None
    state["pending_plan_type"] = None
    state["pending_diagnostic"] = None
    state["pending_diagnostic_conversation_id"] = None

    requested_plan_type, plan_intent_meta = _resolve_plan_type_from_message(user_input)
    if requested_plan_type in {"workout", "nutrition"}:
        inferred_goal, inferred_confidence, inferred_by_ml = _infer_goal_for_plan(profile, tracking_summary)
        plan_profile = dict(profile)
        plan_profile["goal"] = inferred_goal
        missing = _missing_fields_for_plan(requested_plan_type, plan_profile)
        if missing:
            state["pending_field"] = missing[0]
            state["pending_field_conversation_id"] = conversation_id
            state["pending_plan_type"] = requested_plan_type
            question = _missing_field_question(missing[0], language)
            question = _finalize(question, hint=f"Ask only for the missing field: {missing[0]}.")
            memory.add_assistant_message(question)
            return ChatResponse(
                reply=question,
                conversation_id=conversation_id,
                language=language,
                action="ask_profile",
                data={"missing_field": missing[0], "plan_type": requested_plan_type},
            )

        best_plan, ranked = _recommend_best_plan(
            requested_plan_type,
            plan_profile,
            language,
            user_id,
            tracking_summary,
        )
        if not best_plan:
            reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
                language, seed=user_input
            )
            reply = _finalize(reply, hint="Keep it a polite fitness/nutrition redirection only.")
            memory.add_assistant_message(reply)
            return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

        plan_id = best_plan["id"]
        PENDING_PLANS[plan_id] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "plan_type": requested_plan_type,
            "plan": best_plan,
            "approved": False,
            "created_at": datetime.utcnow().isoformat(),
        }
        state["last_pending_plan_id"] = plan_id
        state["last_plan_candidates"] = ranked
        state["last_plan_type"] = requested_plan_type
        if inferred_by_ml:
            state["inferred_goal"] = inferred_goal

        reply = _format_recommended_plan(requested_plan_type, best_plan, language)

        info_lines: list[str] = []
        if inferred_by_ml:
            goal_label = _profile_goal_label(inferred_goal, language)
            conf_text = (
                f" ({_format_number((inferred_confidence or 0.0) * 100, 1)}%)"
                if inferred_confidence is not None
                else ""
            )
            info_lines.append(
                _lang_reply(
                    language,
                    f"Auto-inferred goal from training data: {goal_label}{conf_text}.",
                    f"تم استنتاج الهدف تلقائيًا من بيانات التدريب: {goal_label}{conf_text}.",
                    f"استنتجت هدفك تلقائيًا من بيانات التدريب: {goal_label}{conf_text}.",
                )
            )

        if plan_intent_meta:
            predicted_intent = str(plan_intent_meta.get("predicted_intent", requested_plan_type))
            intent_confidence = _to_float(plan_intent_meta.get("confidence"))
            conf_text = (
                f" ({_format_number((intent_confidence or 0.0) * 100, 1)}%)"
                if intent_confidence is not None
                else ""
            )
            if _is_generic_plan_request(user_input):
                info_lines.append(
                    _lang_reply(
                        language,
                        f"Detected plan type automatically: {predicted_intent}{conf_text}.",
                        f"تم تحديد نوع الخطة تلقائيًا: {predicted_intent}{conf_text}.",
                        f"حددّت نوع الخطة تلقائيًا: {predicted_intent}{conf_text}.",
                    )
                )

        if info_lines:
            reply = "\n".join(info_lines + [reply])

        reply = _finalize(reply, hint="Preserve all plan details exactly.")
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="ask_plan",
            data={
                "plan_id": plan_id,
                "plan_type": requested_plan_type,
                "plan": best_plan,
                "inferred_goal": inferred_goal,
                "inferred_goal_confidence": inferred_confidence,
                "plan_intent_prediction": plan_intent_meta or {},
            },
        )

    if CHAT_RESPONSE_MODE == "dataset_only":
        dataset_reply = _dataset_conversation_reply(user_input, language)
        if dataset_reply:
            dataset_reply = _finalize(dataset_reply)
            memory.add_assistant_message(dataset_reply)
            return ChatResponse(reply=dataset_reply, conversation_id=conversation_id, language=language)

        out_reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
            language, seed=user_input
        )
        out_reply = _finalize(out_reply, hint="Keep it a polite fitness/nutrition redirection only.")
        memory.add_assistant_message(out_reply)
        return ChatResponse(reply=out_reply, conversation_id=conversation_id, language=language)

    ml_prediction_payload = _ml_prediction_chat_response(user_input, language, profile, tracking_summary)
    if ml_prediction_payload:
        ml_reply, ml_data = ml_prediction_payload
        state["last_ml_prediction"] = ml_data
        ml_reply = _finalize(ml_reply)
        memory.add_assistant_message(ml_reply)
        return ChatResponse(
            reply=ml_reply,
            conversation_id=conversation_id,
            language=language,
            action="ml_prediction",
            data=ml_data,
        )

    # Handle numeric progress/performance analysis before routing decisions.
    if _is_performance_analysis_request(user_input, message_tracking_summary):
        performance_reply = _performance_analysis_reply(language, profile, tracking_summary)
        performance_reply = _finalize(performance_reply)
        memory.add_assistant_message(performance_reply)
        return ChatResponse(reply=performance_reply, conversation_id=conversation_id, language=language)

    social_reply = _social_reply(user_input, language, profile)
    if social_reply:
        social_reply = _finalize(social_reply)
        memory.add_assistant_message(social_reply)
        return ChatResponse(reply=social_reply, conversation_id=conversation_id, language=language)

    # Intelligent routing decision (dataset vs LLM vs hybrid)
    dataset_reply = _dataset_conversation_reply(user_input, language)
    route_decision = SMART_ROUTER.route(user_input, profile, dataset_match=bool(dataset_reply))
    state["active_mode"] = route_decision.mode
    if route_decision.response_type == "dataset" and dataset_reply:
        dataset_reply = _finalize(dataset_reply)
        memory.add_assistant_message(dataset_reply)
        return ChatResponse(reply=dataset_reply, conversation_id=conversation_id, language=language)

    if CHAT_RESPONSE_MODE != "dataset_only":
        in_domain, _score = ROUTER.is_in_domain(user_input, language=language)
        if (not in_domain) and _contains_any(user_input, STRONG_DOMAIN_KEYWORDS):
            in_domain = True
        if not in_domain:
            out_reply = _strict_out_of_scope_reply(language)
            out_reply = _finalize(out_reply, hint="Keep it a polite fitness/nutrition redirection only.")
            memory.add_assistant_message(out_reply)
            return ChatResponse(reply=out_reply, conversation_id=conversation_id, language=language)

        # Keep deterministic short conversational replies for very short inputs.
        if dataset_reply and len(normalize_text(user_input).split()) <= 4:
            dataset_reply = _finalize(dataset_reply)
            memory.add_assistant_message(dataset_reply)
            return ChatResponse(reply=dataset_reply, conversation_id=conversation_id, language=language)

        if route_decision.mode == ANALYTICS_MODE:
            stats = compute_stats(tracking_summary)
            insights = generate_insights(stats, language)
            if insights:
                reply = "\n".join(insights)
            else:
                reply = _tracking_reply(language, tracking_summary)
            reply = _finalize(reply)
            memory.add_assistant_message(reply)
            return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

        llm_reply = _general_llm_reply(
            user_message=user_input,
            language=language,
            profile=profile,
            tracking_summary=tracking_summary,
            memory=memory,
            state=state,
            recent_messages=recent_messages,
        )
        if llm_reply.startswith("Ollama error:") or llm_reply.startswith("Ollama is not reachable"):
            llm_reply = _lang_reply(
                language,
                "Local AI is unavailable. This project runs free with Ollama. Start Ollama, run `ollama pull llama3.2:3b`, then retry.",
                "الذكاء المحلي غير متاح حالياً. هذا المشروع مجاني عبر Ollama. شغّل Ollama ثم نفّذ `ollama pull llama3.2:3b` وبعدها أعد المحاولة.",
                "الذكاء المحلي واقف حالياً. المشروع مجاني على Ollama. شغّل Ollama واعمل `ollama pull llama3.2:3b` وجرّب مرة ثانية.",
            )

        if route_decision.response_type == "hybrid" and dataset_reply:
            llm_reply = f"{dataset_reply}\n\n{llm_reply}"

        filtered_reply, _ = MODERATION.filter_content(llm_reply, language=language)
        filtered_reply = _finalize(filtered_reply, source="llm")
        memory.add_assistant_message(filtered_reply)
        return ChatResponse(reply=filtered_reply, conversation_id=conversation_id, language=language)

    dataset_reply = _dataset_conversation_reply(user_input, language)
    if dataset_reply:
        dataset_reply = _finalize(dataset_reply)
        memory.add_assistant_message(dataset_reply)
        return ChatResponse(reply=dataset_reply, conversation_id=conversation_id, language=language)

    out_reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
        language, seed=user_input
    )
    out_reply = _finalize(out_reply, hint="Keep it a polite fitness/nutrition redirection only.")
    memory.add_assistant_message(out_reply)
    return ChatResponse(reply=out_reply, conversation_id=conversation_id, language=language)

    # Strict dataset mode:
    # - Conversational replies must come from conversation_intents.json
    # - Plan content must come from workout_programs.json / nutrition_programs.json
    # - Any unmatched general message gets out_of_scope from the dataset.
    is_plan_request = _is_workout_plan_request(user_input) or _is_nutrition_plan_request(user_input)
    if not is_plan_request:
        dataset_reply = _dataset_conversation_reply(user_input, language)
        if dataset_reply:
            memory.add_assistant_message(dataset_reply)
            return ChatResponse(reply=dataset_reply, conversation_id=conversation_id, language=language)

        out_reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
            language, seed=user_input
        )
        memory.add_assistant_message(out_reply)
        return ChatResponse(reply=out_reply, conversation_id=conversation_id, language=language)

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
        social_reply = _finalize(social_reply)
        memory.add_assistant_message(social_reply)
        return ChatResponse(reply=social_reply, conversation_id=conversation_id, language=language)

    profile_reply = _profile_query_reply(user_input, language, profile, tracking_summary)
    if profile_reply:
        profile_reply = _finalize(profile_reply)
        memory.add_assistant_message(profile_reply)
        return ChatResponse(reply=profile_reply, conversation_id=conversation_id, language=language)

    if _contains_any(lowered, PLAN_STATUS_KEYWORDS):
        status_reply = _plan_status_reply(language, state.get("plan_snapshot"))
        status_reply = _finalize(status_reply)
        memory.add_assistant_message(status_reply)
        return ChatResponse(reply=status_reply, conversation_id=conversation_id, language=language)

    if _is_performance_analysis_request(user_input, message_tracking_summary):
        performance_reply = _performance_analysis_reply(language, profile, tracking_summary)
        performance_reply = _finalize(performance_reply)
        memory.add_assistant_message(performance_reply)
        return ChatResponse(reply=performance_reply, conversation_id=conversation_id, language=language)

    if _contains_any(lowered, PROGRESS_CONCERN_KEYWORDS):
        state["pending_diagnostic"] = "progress"
        state["pending_diagnostic_conversation_id"] = conversation_id
        response = _progress_diagnostic_reply(language, profile, tracking_summary)
        response = _finalize(response)
        memory.add_assistant_message(response)
        return ChatResponse(reply=response, conversation_id=conversation_id, language=language)

    if _contains_any(lowered, TROUBLESHOOT_KEYWORDS):
        state["pending_diagnostic"] = "exercise"
        state["pending_diagnostic_conversation_id"] = conversation_id
        response = _exercise_diagnostic_reply(language)
        response = _finalize(response)
        memory.add_assistant_message(response)
        return ChatResponse(reply=response, conversation_id=conversation_id, language=language)

    in_domain, _score = ROUTER.is_in_domain(user_input, language=language)
    if not in_domain:
        out_reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
            language, seed=user_input
        )
        out_reply = _finalize(out_reply, hint="Keep it a polite fitness/nutrition redirection only.")
        memory.add_assistant_message(out_reply)
        return ChatResponse(reply=out_reply, conversation_id=conversation_id, language=language)

    if _is_workout_plan_request(user_input):
        state["pending_plan_type"] = "workout"
        profile = _build_profile(req, state, profile_payload=effective_profile_payload)
        missing = _missing_fields_for_plan("workout", profile)
        if missing:
            state["pending_field"] = missing[0]
            state["pending_field_conversation_id"] = conversation_id
            question = _missing_field_question(missing[0], language)
            question = _finalize(question, hint=f"Ask only for the missing field: {missing[0]}.")
            memory.add_assistant_message(question)
            return ChatResponse(
                reply=question,
                conversation_id=conversation_id,
                language=language,
                action="ask_profile",
                data={"missing_field": missing[0], "plan_type": "workout"},
            )

        best_plan, ranked = _recommend_best_plan("workout", profile, language, user_id, tracking_summary)
        if not best_plan:
            reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
                language, seed=user_input
            )
            reply = _finalize(reply, hint="Keep it a polite fitness/nutrition redirection only.")
            memory.add_assistant_message(reply)
            return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

        plan_id = best_plan["id"]
        PENDING_PLANS[plan_id] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "plan_type": "workout",
            "plan": best_plan,
            "approved": False,
            "created_at": datetime.utcnow().isoformat(),
        }
        state["last_pending_plan_id"] = plan_id
        state["last_plan_candidates"] = ranked
        state["last_plan_type"] = "workout"
        state["pending_plan_type"] = None

        reply = _format_recommended_plan("workout", best_plan, language)
        reply = _finalize(reply, hint="Preserve all plan details exactly.")
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="ask_plan",
            data={"plan_id": plan_id, "plan_type": "workout", "plan": best_plan},
        )

    if _is_nutrition_plan_request(user_input):
        state["pending_plan_type"] = "nutrition"
        profile = _build_profile(req, state, profile_payload=effective_profile_payload)
        missing = _missing_fields_for_plan("nutrition", profile)
        if missing:
            state["pending_field"] = missing[0]
            state["pending_field_conversation_id"] = conversation_id
            question = _missing_field_question(missing[0], language)
            question = _finalize(question, hint=f"Ask only for the missing field: {missing[0]}.")
            memory.add_assistant_message(question)
            return ChatResponse(
                reply=question,
                conversation_id=conversation_id,
                language=language,
                action="ask_profile",
                data={"missing_field": missing[0], "plan_type": "nutrition"},
            )

        best_plan, ranked = _recommend_best_plan("nutrition", profile, language, user_id, tracking_summary)
        if not best_plan:
            reply = _dataset_intent_response("out_of_scope", language, seed=user_input) or _dataset_fallback_reply(
                language, seed=user_input
            )
            reply = _finalize(reply, hint="Keep it a polite fitness/nutrition redirection only.")
            memory.add_assistant_message(reply)
            return ChatResponse(reply=reply, conversation_id=conversation_id, language=language)

        plan_id = best_plan["id"]
        PENDING_PLANS[plan_id] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "plan_type": "nutrition",
            "plan": best_plan,
            "approved": False,
            "created_at": datetime.utcnow().isoformat(),
        }
        state["last_pending_plan_id"] = plan_id
        state["last_plan_candidates"] = ranked
        state["last_plan_type"] = "nutrition"
        state["pending_plan_type"] = None

        reply = _format_recommended_plan("nutrition", best_plan, language)
        reply = _finalize(reply, hint="Preserve all plan details exactly.")
        memory.add_assistant_message(reply)
        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            language=language,
            action="ask_plan",
            data={"plan_id": plan_id, "plan_type": "nutrition", "plan": best_plan},
        )

    if _contains_any(lowered, PROGRESS_KEYWORDS):
        reply = _tracking_reply(language, tracking_summary)
        reply = _finalize(reply)
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
        reply = _finalize(reply)
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
    filtered_reply = _finalize(filtered_reply, source="llm")
    memory.add_assistant_message(filtered_reply)
    return ChatResponse(reply=filtered_reply, conversation_id=conversation_id, language=language)


async def _voice_llm_responder(
    transcript: str,
    language: str,
    user_id: Optional[str],
    conversation_id: Optional[str],
) -> tuple[str, Optional[str]]:
    chat_req = ChatRequest(
        message=transcript,
        user_id=user_id,
        conversation_id=conversation_id,
        language=language,
    )
    chat_resp = await chat(chat_req)
    return chat_resp.reply, chat_resp.conversation_id


@app.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    language: str = Form("en"),
    user_id: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
) -> VoiceChatResponse:
    uid = _normalize_user_id(user_id)
    conv_id = _normalize_conversation_id(conversation_id, uid)
    lang = "ar" if (language or "").lower().startswith("ar") else "en"

    if audio.content_type and not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an audio format.")

    suffix = Path(audio.filename or "").suffix.lower() or ".wav"
    input_audio_path = STATIC_AUDIO_DIR / f"input_{uuid.uuid4().hex}{suffix}"

    try:
        with input_audio_path.open("wb") as out_file:
            shutil.copyfileobj(audio.file, out_file)

        result: VoicePipelineResult = await VOICE_PIPELINE.run(
            audio_path=input_audio_path,
            language=lang,
            user_id=uid,
            conversation_id=conv_id,
            llm_responder=_voice_llm_responder,
        )

        return VoiceChatResponse(
            transcript=result.transcript,
            reply=result.reply_text,
            audio_path=result.audio_url,
            conversation_id=result.conversation_id or conv_id,
            language=lang,
        )
    except VoicePipelineError as exc:
        logger.warning("VOICE_CHAT_PIPELINE_ERROR user=%s conv=%s msg=%s", uid, conv_id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("VOICE_CHAT_UNKNOWN_ERROR user=%s conv=%s", uid, conv_id)
        raise HTTPException(status_code=500, detail="Voice chat failed unexpectedly.") from exc
    finally:
        try:
            audio.file.close()
        except Exception:
            pass
        try:
            input_audio_path.unlink(missing_ok=True)
        except Exception:
            pass


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


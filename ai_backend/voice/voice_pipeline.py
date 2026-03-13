from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Optional, Tuple

from llm_client import LLMClient
from utils_logger import log_error, log_event
from voice.stt import STTError, WhisperSTT
from voice.tts import LocalTTS, TTSError


class VoicePipelineError(RuntimeError):
    """Raised when any stage in the voice pipeline fails."""


@dataclass
class VoicePipelineResult:
    transcript: str
    reply_text: str
    audio_file_path: str
    audio_url: str
    conversation_id: Optional[str] = None


LLMResponder = Callable[[str, str, Optional[str], Optional[str]], Awaitable[Tuple[str, Optional[str]]]]


class VoicePipeline:
    """Audio -> Text -> LLM -> Text -> Audio pipeline."""

    def __init__(
        self,
        stt_engine: WhisperSTT,
        tts_engine: LocalTTS,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        self.llm_client = llm_client or LLMClient()

    async def run(
        self,
        audio_path: str | Path,
        language: str = "en",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        llm_responder: Optional[LLMResponder] = None,
    ) -> VoicePipelineResult:
        try:
            transcript = await asyncio.to_thread(self.stt_engine.transcribe, audio_path, language)
        except STTError as exc:
            raise VoicePipelineError(str(exc)) from exc
        except Exception as exc:
            log_error("VOICE_PIPELINE_STT_ERROR", user_id, exc, {"audio_path": str(audio_path)})
            raise VoicePipelineError("Speech-to-Text stage failed.") from exc

        if llm_responder is not None:
            try:
                reply_text, resolved_conversation_id = await llm_responder(
                    transcript,
                    language,
                    user_id,
                    conversation_id,
                )
            except Exception as exc:
                log_error(
                    "VOICE_PIPELINE_LLM_CALLBACK_ERROR",
                    user_id,
                    exc,
                    {"conversation_id": conversation_id, "language": language},
                )
                raise VoicePipelineError("LLM stage failed.") from exc
        else:
            reply_text = await asyncio.to_thread(self._default_llm_reply, transcript, language)
            resolved_conversation_id = conversation_id

        if not (reply_text or "").strip():
            raise VoicePipelineError("LLM returned an empty response.")

        try:
            audio_output_path = await asyncio.to_thread(self.tts_engine.synthesize, reply_text, language)
        except TTSError as exc:
            raise VoicePipelineError(str(exc)) from exc
        except Exception as exc:
            log_error(
                "VOICE_PIPELINE_TTS_ERROR",
                user_id,
                exc,
                {"reply_chars": len(reply_text or "")},
            )
            raise VoicePipelineError("Text-to-Speech stage failed.") from exc

        audio_url = f"/static/audio/{audio_output_path.name}"
        log_event(
            "VOICE_PIPELINE_OK",
            user_id,
            {
                "conversation_id": resolved_conversation_id,
                "language": language,
                "transcript_chars": len(transcript),
                "reply_chars": len(reply_text),
                "audio_url": audio_url,
            },
        )

        return VoicePipelineResult(
            transcript=transcript,
            reply_text=reply_text,
            audio_file_path=str(audio_output_path),
            audio_url=audio_url,
            conversation_id=resolved_conversation_id,
        )

    def _default_llm_reply(self, transcript: str, language: str) -> str:
        if (language or "").lower().startswith("ar"):
            system_prompt = (
                "أنت مدرب لياقة متخصص."
                "تجيب فقط عن: التمارين، التغذية، التعافي، تركيب الجسم، وتتبع التقدم."
                "أي سؤال خارج هذا النطاق: ارفض باختصار وأعد التوجيه لمجال اللياقة."
            )
        else:
            system_prompt = (
                "You are a specialized fitness coach. "
                "Answer only workouts, nutrition, recovery, body composition, and progress tracking. "
                "If user asks outside this scope, refuse briefly and redirect to fitness topics."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ]
        return self.llm_client.chat_completion(messages, max_tokens=450)

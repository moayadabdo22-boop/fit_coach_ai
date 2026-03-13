from __future__ import annotations

import os
import shutil
from pathlib import Path
from threading import Lock
from typing import Optional

from utils_logger import log_error, log_event


class STTError(RuntimeError):
    """Raised when Speech-to-Text fails."""


class WhisperSTT:
    """Local Whisper STT wrapper using transformers pipeline."""

    def __init__(self, model_name: str = "openai/whisper-base", device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        self._pipeline = None
        self._load_lock = Lock()

    def _ensure_ffmpeg_available(self) -> None:
        # transformers ASR pipeline reads audio files using ffmpeg when input is a path.
        if shutil.which("ffmpeg"):
            return

        try:
            import imageio_ffmpeg

            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as exc:
            raise STTError(
                "ffmpeg is required for Whisper STT. Install ffmpeg or `imageio-ffmpeg`."
            ) from exc

        ffmpeg_dir = str(Path(ffmpeg_exe).resolve().parent)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path

        if not shutil.which("ffmpeg"):
            raise STTError(
                "ffmpeg is still not discoverable on PATH after imageio-ffmpeg fallback."
            )

    def _ensure_loaded(self) -> None:
        if self._pipeline is not None:
            return

        with self._load_lock:
            if self._pipeline is not None:
                return

            try:
                from transformers import pipeline
            except Exception as exc:  # pragma: no cover - environment issue
                raise STTError(
                    "Whisper dependencies missing. Install transformers + torch in backend environment."
                ) from exc

            try:
                self._ensure_ffmpeg_available()
                device_index = 0 if self.device.startswith("cuda") else -1
                self._pipeline = pipeline(
                    task="automatic-speech-recognition",
                    model=self.model_name,
                    device=device_index,
                )
                log_event(
                    "VOICE_STT_MODEL_LOADED",
                    None,
                    {"model": self.model_name, "device": self.device},
                )
            except Exception as exc:
                log_error(
                    "VOICE_STT_MODEL_LOAD_ERROR",
                    None,
                    exc,
                    {"model": self.model_name, "device": self.device},
                )
                raise STTError(f"Unable to load Whisper model: {self.model_name}") from exc

    def transcribe(self, audio_file: str | Path, language: Optional[str] = None) -> str:
        path = Path(audio_file)
        if not path.exists() or not path.is_file():
            raise STTError(f"Audio file not found: {path}")

        self._ensure_loaded()

        generate_kwargs: dict[str, str] = {"task": "transcribe"}
        lang = (language or "").lower().strip()
        if lang.startswith("ar"):
            generate_kwargs["language"] = "arabic"
        elif lang.startswith("en"):
            generate_kwargs["language"] = "english"

        try:
            result = self._pipeline(str(path), generate_kwargs=generate_kwargs)
        except Exception as exc:
            log_error(
                "VOICE_STT_TRANSCRIBE_ERROR",
                None,
                exc,
                {"file": str(path), "language": lang, "model": self.model_name},
            )
            raise STTError("Whisper transcription failed. Ensure supported audio format and ffmpeg availability.") from exc

        if isinstance(result, dict):
            text = str(result.get("text", "")).strip()
        else:
            text = str(result).strip()

        if not text:
            raise STTError("No speech detected in audio.")

        log_event(
            "VOICE_STT_OK",
            None,
            {"file": path.name, "chars": len(text), "language": lang or "auto"},
        )
        return text

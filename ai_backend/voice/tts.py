from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from threading import Lock

from utils_logger import log_error, log_event


class TTSError(RuntimeError):
    """Raised when Text-to-Speech fails."""


class LocalTTS:
    """Local TTS wrapper supporting Piper (default) and optional Coqui TTS."""

    def __init__(self, output_dir: str | Path, engine: str | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.engine = (engine or os.getenv("VOICE_TTS_ENGINE", "piper")).strip().lower()
        self.piper_bin = os.getenv("PIPER_BIN", "piper")

        # You can set one shared model or per-language models.
        self.piper_model_path = os.getenv("PIPER_MODEL_PATH", "")
        self.piper_model_path_en = os.getenv("PIPER_MODEL_PATH_EN", "")
        self.piper_model_path_ar = os.getenv("PIPER_MODEL_PATH_AR", "")
        self.piper_config_path = os.getenv("PIPER_CONFIG_PATH", "")

        self.coqui_model_name = os.getenv("COQUI_TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC")
        self._coqui_tts = None
        self._coqui_lock = Lock()

    def _select_piper_model(self, language: str) -> str:
        lang = (language or "").lower().strip()
        if lang.startswith("ar") and self.piper_model_path_ar:
            return self.piper_model_path_ar
        if lang.startswith("en") and self.piper_model_path_en:
            return self.piper_model_path_en
        return self.piper_model_path

    def synthesize(self, text: str, language: str = "en") -> Path:
        clean_text = (text or "").strip()
        if not clean_text:
            raise TTSError("Cannot synthesize empty text.")

        output_path = self.output_dir / f"reply_{uuid.uuid4().hex}.wav"

        if self.engine == "coqui":
            self._synthesize_with_coqui(clean_text, output_path)
        else:
            self._synthesize_with_piper(clean_text, output_path, language)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise TTSError("TTS did not generate a valid audio file.")

        log_event(
            "VOICE_TTS_OK",
            None,
            {
                "engine": self.engine,
                "output": str(output_path),
                "bytes": output_path.stat().st_size,
            },
        )
        return output_path

    def _synthesize_with_piper(self, text: str, output_path: Path, language: str) -> None:
        model_path = self._select_piper_model(language)
        if not model_path:
            raise TTSError(
                "Piper model path is not configured. Set PIPER_MODEL_PATH (or PIPER_MODEL_PATH_EN / PIPER_MODEL_PATH_AR)."
            )

        cmd = [self.piper_bin, "--model", model_path, "--output_file", str(output_path)]
        if self.piper_config_path:
            cmd.extend(["--config", self.piper_config_path])

        try:
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except FileNotFoundError as exc:
            raise TTSError(
                f"Piper binary not found: {self.piper_bin}. Set PIPER_BIN to full executable path."
            ) from exc
        except Exception as exc:
            log_error("VOICE_TTS_PIPER_EXEC_ERROR", None, exc, {"cmd": cmd})
            raise TTSError("Piper execution failed.") from exc

        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="ignore").strip()
            raise TTSError(f"Piper synthesis failed: {stderr or 'Unknown error'}")

    def _synthesize_with_coqui(self, text: str, output_path: Path) -> None:
        if self._coqui_tts is None:
            with self._coqui_lock:
                if self._coqui_tts is None:
                    try:
                        from TTS.api import TTS
                    except Exception as exc:  # pragma: no cover - optional dependency
                        raise TTSError("Coqui TTS is not installed. Install package `TTS` or use Piper engine.") from exc
                    try:
                        self._coqui_tts = TTS(model_name=self.coqui_model_name, progress_bar=False, gpu=False)
                    except Exception as exc:
                        log_error(
                            "VOICE_TTS_COQUI_LOAD_ERROR",
                            None,
                            exc,
                            {"model": self.coqui_model_name},
                        )
                        raise TTSError(f"Unable to load Coqui model: {self.coqui_model_name}") from exc

        try:
            self._coqui_tts.tts_to_file(text=text, file_path=str(output_path))
        except Exception as exc:
            log_error(
                "VOICE_TTS_COQUI_SYNTH_ERROR",
                None,
                exc,
                {"model": self.coqui_model_name, "output": str(output_path)},
            )
            raise TTSError("Coqui synthesis failed.") from exc

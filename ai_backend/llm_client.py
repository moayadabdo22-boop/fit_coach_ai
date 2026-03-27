from __future__ import annotations

import json
import os
from typing import Any, Iterator

import requests
try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in Ollama-only setups
    OpenAI = None

from config import (
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_GPU,
    OLLAMA_TIMEOUT_SECONDS,
    OPENAI_API_KEY,
)
from utils_logger import log_error


class LLMClient:
    """LLM wrapper supporting OpenAI and local Ollama."""

    def __init__(self, model: str = LLM_MODEL, temperature: float = LLM_TEMPERATURE):
        self.model = model
        self.temperature = temperature
        self.provider = (LLM_PROVIDER or "auto").lower()
        self.has_openai_key = bool(OPENAI_API_KEY) and (OpenAI is not None)
        self._openai_client = OpenAI(api_key=OPENAI_API_KEY) if self.has_openai_key else None
        self._ollama_model_candidates: list[str] = []
        self._ollama_model = self._select_ollama_model()

    @property
    def active_provider(self) -> str:
        if self.provider in {"openai", "ollama"}:
            return self.provider
        # auto mode: prefer OpenAI when key exists, otherwise Ollama.
        return "openai" if self.has_openai_key else "ollama"

    @property
    def active_model(self) -> str:
        if self.active_provider == "ollama":
            return self._ollama_model
        return self.model

    def _select_ollama_model(self) -> str:
        """Pick the strongest installed local model (auto-upgrade by default)."""
        preferred_model = (OLLAMA_MODEL or "llama3.2:3b").strip()
        auto_best = str(os.getenv("OLLAMA_AUTO_BEST_MODEL", "true")).strip().lower() in {"1", "true", "yes", "on"}

        default_fallback = "qwen2.5:14b-instruct,qwen2.5:7b-instruct,llama3.1:8b,mistral:7b-instruct,llama3.2:3b"
        if OLLAMA_NUM_GPU == 0:
            default_fallback = "llama3.2:3b,llama3.1:8b,qwen2.5:7b-instruct,mistral:7b-instruct"
        fallback_env = os.getenv("OLLAMA_FALLBACK_MODELS", default_fallback)
        fallback_candidates = [m.strip() for m in fallback_env.split(",") if m.strip()]

        try:
            response = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=min(10, OLLAMA_TIMEOUT_SECONDS))
            if response.status_code >= 400:
                self._ollama_model_candidates = [preferred_model]
                return preferred_model
            payload = response.json()
            models = payload.get("models") if isinstance(payload, dict) else []
            installed = {
                str((item or {}).get("name", "")).strip()
                for item in models
                if isinstance(item, dict) and str((item or {}).get("name", "")).strip()
            }

            if auto_best:
                ordered = fallback_candidates + [preferred_model]
            else:
                ordered = [preferred_model] + fallback_candidates

            ranked_installed: list[str] = []
            for candidate in ordered:
                if candidate in installed and candidate not in ranked_installed:
                    ranked_installed.append(candidate)
            for candidate in sorted(installed):
                if candidate not in ranked_installed:
                    ranked_installed.append(candidate)
            self._ollama_model_candidates = ranked_installed
            if ranked_installed:
                return ranked_installed[0]
        except Exception:
            self._ollama_model_candidates = [preferred_model]
            return preferred_model
        self._ollama_model_candidates = [preferred_model]
        return preferred_model

    def _should_retry_ollama_model(self, response: requests.Response) -> bool:
        detail = ""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = str(payload.get("error") or payload.get("message") or "").lower()
        except Exception:
            detail = (response.text or "").lower()
        markers = (
            "runner process has terminated",
            "insufficient memory",
            "out of memory",
            "failed to create context",
            "cuda",
            "mmap",
        )
        return any(marker in detail for marker in markers)

    def _next_ollama_model(self, current_model: str) -> str | None:
        if not self._ollama_model_candidates:
            return None
        try:
            idx = self._ollama_model_candidates.index(current_model)
        except ValueError:
            return self._ollama_model_candidates[0]
        if idx + 1 >= len(self._ollama_model_candidates):
            return None
        return self._ollama_model_candidates[idx + 1]

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        provider = self.active_provider
        if provider == "openai":
            return self._chat_openai(messages, temperature, max_tokens, tools)
        return self._chat_ollama(messages, temperature, max_tokens)

    def chat_completion_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        provider = self.active_provider
        if provider == "openai":
            yield from self._chat_openai_stream(messages, temperature, max_tokens)
            return
        yield from self._chat_ollama_stream(messages, temperature, max_tokens)

    def _chat_openai(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None,
        max_tokens: int | None,
        tools: list[dict[str, Any]] | None,
    ) -> str:
        if not self.has_openai_key or self._openai_client is None:
            return (
                "OpenAI key is not configured. "
                "Use OPENAI_API_KEY or switch to Ollama (LLM_PROVIDER=ollama)."
            )

        try:
            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature if temperature is None else temperature,
            }
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            response = self._openai_client.chat.completions.create(**params)
            choice = response.choices[0]
            return choice.message.content or ""
        except Exception as exc:
            log_error("LLM_OPENAI_COMPLETION_ERROR", None, exc, {"messages": len(messages)})
            return "I hit a temporary AI error. Please try again."

    def _chat_openai_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None,
        max_tokens: int | None,
    ) -> Iterator[str]:
        if not self.has_openai_key or self._openai_client is None:
            yield (
                "OpenAI key is not configured. "
                "Use OPENAI_API_KEY or switch to Ollama (LLM_PROVIDER=ollama)."
            )
            return

        try:
            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature if temperature is None else temperature,
                "stream": True,
            }
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            stream = self._openai_client.chat.completions.create(**params)
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            log_error("LLM_OPENAI_STREAM_ERROR", None, exc, {"messages": len(messages)})
            yield "I hit a temporary AI streaming error. Please try again."

    def _chat_ollama(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None,
        max_tokens: int | None,
    ) -> str:
        current_model = self._ollama_model
        while True:
            payload = {
                "model": current_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature if temperature is None else temperature,
                    "num_gpu": OLLAMA_NUM_GPU,
                },
            }
            if max_tokens is not None:
                payload["options"]["num_predict"] = max_tokens

            try:
                response = requests.post(
                    f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                    json=payload,
                    timeout=OLLAMA_TIMEOUT_SECONDS,
                )
                if response.status_code == 404:
                    # Older Ollama builds expose /api/generate only.
                    self._ollama_model = current_model
                    return self._chat_ollama_generate(messages, temperature, max_tokens)
                if response.status_code >= 400:
                    if self._should_retry_ollama_model(response):
                        next_model = self._next_ollama_model(current_model)
                        if next_model:
                            current_model = next_model
                            self._ollama_model = next_model
                            continue
                    return self._format_ollama_http_error(response)
                response.raise_for_status()
                data = response.json()
                self._ollama_model = current_model
                return str(data.get("message", {}).get("content", "")).strip()
            except Exception as exc:
                log_error(
                    "LLM_OLLAMA_COMPLETION_ERROR",
                    None,
                    exc,
                    {"base_url": OLLAMA_BASE_URL, "model": current_model},
                )
                return (
                    "Ollama is not reachable. Start Ollama and pull a model, for example:\n"
                    "ollama pull llama3.2:3b\n"
                    "Then keep Ollama running on http://127.0.0.1:11434."
                )

    def _chat_ollama_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None,
        max_tokens: int | None,
    ) -> Iterator[str]:
        payload = {
            "model": self._ollama_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature if temperature is None else temperature,
                "num_gpu": OLLAMA_NUM_GPU,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        try:
            with requests.post(
                f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                json=payload,
                timeout=OLLAMA_TIMEOUT_SECONDS,
                stream=True,
            ) as response:
                if response.status_code == 404:
                    yield from self._chat_ollama_generate_stream(messages, temperature, max_tokens)
                    return
                if response.status_code >= 400:
                    yield self._format_ollama_http_error(response)
                    return
                response.raise_for_status()
                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    try:
                        line = json.loads(raw_line)
                    except Exception:
                        continue
                    text = str(line.get("message", {}).get("content", ""))
                    if text:
                        yield text
        except Exception as exc:
            log_error(
                "LLM_OLLAMA_STREAM_ERROR",
                None,
                exc,
                {"base_url": OLLAMA_BASE_URL, "model": self._ollama_model},
            )
            yield "Ollama streaming is unavailable right now. Please retry."

    @staticmethod
    def _messages_to_prompt(messages: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for msg in messages:
            role = str(msg.get("role", "user")).strip().lower()
            content = str(msg.get("content", "")).strip()
            if not content:
                continue
            if role == "system":
                lines.append(f"System: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            else:
                lines.append(f"User: {content}")
        lines.append("Assistant:")
        return "\n\n".join(lines)

    def _chat_ollama_generate(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None,
        max_tokens: int | None,
    ) -> str:
        payload = {
            "model": self._ollama_model,
            "prompt": self._messages_to_prompt(messages),
            "stream": False,
            "options": {
                "temperature": self.temperature if temperature is None else temperature,
                "num_gpu": OLLAMA_NUM_GPU,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        response = requests.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            return self._format_ollama_http_error(response)
        response.raise_for_status()
        data = response.json()
        return str(data.get("response", "")).strip()

    def _chat_ollama_generate_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None,
        max_tokens: int | None,
    ) -> Iterator[str]:
        payload = {
            "model": self._ollama_model,
            "prompt": self._messages_to_prompt(messages),
            "stream": True,
            "options": {
                "temperature": self.temperature if temperature is None else temperature,
                "num_gpu": OLLAMA_NUM_GPU,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        with requests.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
            stream=True,
        ) as response:
            if response.status_code >= 400:
                yield self._format_ollama_http_error(response)
                return
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                try:
                    line = json.loads(raw_line)
                except Exception:
                    continue
                text = str(line.get("response", ""))
                if text:
                    yield text

    def _format_ollama_http_error(self, response: requests.Response) -> str:
        detail = ""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = str(payload.get("error", "")).strip()
        except Exception:
            detail = (response.text or "").strip()

        if detail:
            return (
                f"Ollama error: {detail}\n"
                f"Check your local model runtime with: ollama run {self._ollama_model}\n"
                "Then retry your message."
            )
        return (
            f"Ollama request failed with status {response.status_code}.\n"
            f"Check your local model runtime with: ollama run {self._ollama_model}"
        )

    @staticmethod
    def create_tool_definition(
        name: str,
        description: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters.get("properties", {}),
                    "required": parameters.get("required", []),
                },
            },
        }

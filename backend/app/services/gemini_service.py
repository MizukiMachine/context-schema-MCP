from __future__ import annotations

import json
import re
import time
from typing import Any

import google.api_core.exceptions as google_exceptions
import google.generativeai as genai

from app.config import Settings, get_settings


class GeminiService:
    """Wrapper around the Gemini API with retry and rate limiting."""

    DEFAULT_MODEL = "gemini-2.0-flash-exp"
    MAX_RETRIES = 3
    DEFAULT_REQUESTS_PER_MINUTE = 60
    _JSON_BLOCK_PATTERN = re.compile(r"^```(?:json)?\s*(?P<body>.*)\s*```$", re.DOTALL)

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required.")

        self.api_key = api_key
        self.model = model
        self._time_func = time.monotonic
        self._sleep_func = time.sleep
        self._min_request_interval = 60.0 / self.DEFAULT_REQUESTS_PER_MINUTE
        self._last_request_at: float | None = None

        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(model_name=model)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate plain text from Gemini."""
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        response = self._request_with_retry(
            prompt=prompt,
            generation_config=generation_config,
        )
        return self._extract_text(response)

    def generate_json(self, prompt: str) -> dict[str, Any]:
        """Generate a JSON object and parse it."""
        json_prompt = (
            f"{prompt}\n\n"
            "Return only a valid JSON object. Do not include code fences or explanatory text."
        )
        response = self._request_with_retry(
            prompt=json_prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json",
            },
        )
        payload = self._parse_json(self._extract_text(response))
        if not isinstance(payload, dict):
            raise ValueError("Gemini JSON response must be an object.")
        return payload

    def analyze_content(self, content: str, analysis_type: str) -> dict[str, Any]:
        """Analyze content and return structured JSON."""
        prompt = (
            "Analyze the provided content and return a JSON object with the keys "
            "`analysis_type`, `summary`, `key_points`, and `risks`.\n\n"
            f"analysis_type: {analysis_type}\n"
            f"content:\n{content}"
        )
        result = self.generate_json(prompt)
        result.setdefault("analysis_type", analysis_type)
        return result

    def _request_with_retry(
        self,
        *,
        prompt: str,
        generation_config: dict[str, Any],
    ) -> Any:
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            self._apply_rate_limit()
            try:
                return self._client.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
            except self._retryable_errors() as exc:
                last_error = exc
                if attempt >= self.MAX_RETRIES:
                    break
                self._sleep_func(float(2**attempt))
            except Exception:
                raise

        assert last_error is not None
        raise last_error

    def _apply_rate_limit(self) -> None:
        if self._last_request_at is None:
            self._last_request_at = self._time_func()
            return

        elapsed = self._time_func() - self._last_request_at
        remaining = self._min_request_interval - elapsed
        if remaining > 0:
            self._sleep_func(remaining)
        self._last_request_at = self._time_func()

    def _extract_text(self, response: Any) -> str:
        try:
            text = getattr(response, "text", None)
        except Exception:
            text = None

        if isinstance(text, str) and text.strip():
            return text.strip()

        candidates = getattr(response, "candidates", None) or []
        parts: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str) and part_text.strip():
                    parts.append(part_text.strip())

        if parts:
            return "\n".join(parts)

        raise ValueError("Gemini response did not contain text.")

    def _parse_json(self, payload: str) -> dict[str, Any] | list[Any]:
        cleaned = payload.strip()
        match = self._JSON_BLOCK_PATTERN.match(cleaned)
        if match:
            cleaned = match.group("body").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse Gemini JSON response.") from exc

    @staticmethod
    def _retryable_errors() -> tuple[type[Exception], ...]:
        return (
            google_exceptions.ResourceExhausted,
            google_exceptions.TooManyRequests,
            google_exceptions.ServiceUnavailable,
            google_exceptions.InternalServerError,
            google_exceptions.DeadlineExceeded,
        )


def get_gemini_service(settings: Settings | None = None) -> GeminiService:
    """Create a Gemini service instance from application settings."""
    app_settings = settings or get_settings()
    if not app_settings.gemini_api_key:
        raise ValueError("Gemini API key is not configured.")
    return GeminiService(
        api_key=app_settings.gemini_api_key,
        model=app_settings.gemini_model,
    )


__all__ = ["GeminiService", "get_gemini_service"]

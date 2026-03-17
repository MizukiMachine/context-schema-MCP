from __future__ import annotations

from types import SimpleNamespace

import google.api_core.exceptions as google_exceptions

from app.services.gemini_service import GeminiService


class FakeModel:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.calls: list[dict[str, object]] = []

    def generate_content(self, prompt: str, generation_config: dict[str, object]) -> object:
        self.calls.append(
            {
                "prompt": prompt,
                "generation_config": generation_config,
            }
        )
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_generate_basic(monkeypatch) -> None:
    configured: dict[str, str] = {}
    fake_model = FakeModel([SimpleNamespace(text="basic response")])

    monkeypatch.setattr(
        "app.services.gemini_service.genai.configure",
        lambda *, api_key: configured.update({"api_key": api_key}),
    )
    monkeypatch.setattr(
        "app.services.gemini_service.genai.GenerativeModel",
        lambda model_name: fake_model,
    )

    service = GeminiService(api_key="test-key")
    result = service.generate("hello gemini")

    assert result == "basic response"
    assert configured == {"api_key": "test-key"}
    assert fake_model.calls[0]["prompt"] == "hello gemini"


def test_generate_json(monkeypatch) -> None:
    fake_model = FakeModel([SimpleNamespace(text='```json\n{"status":"ok","count":2}\n```')])

    monkeypatch.setattr("app.services.gemini_service.genai.configure", lambda *, api_key: None)
    monkeypatch.setattr(
        "app.services.gemini_service.genai.GenerativeModel",
        lambda model_name: fake_model,
    )

    service = GeminiService(api_key="test-key")
    result = service.generate_json("Return a status payload")

    assert result == {"status": "ok", "count": 2}
    assert fake_model.calls[0]["generation_config"]["response_mime_type"] == "application/json"


def test_retry_on_error(monkeypatch) -> None:
    fake_model = FakeModel(
        [
            google_exceptions.ServiceUnavailable("try again later"),
            google_exceptions.ServiceUnavailable("still unavailable"),
            SimpleNamespace(text="recovered"),
        ]
    )
    sleep_calls: list[float] = []

    monkeypatch.setattr("app.services.gemini_service.genai.configure", lambda *, api_key: None)
    monkeypatch.setattr(
        "app.services.gemini_service.genai.GenerativeModel",
        lambda model_name: fake_model,
    )

    service = GeminiService(api_key="test-key")
    service._sleep_func = lambda seconds: sleep_calls.append(seconds)
    service._min_request_interval = 0

    result = service.generate("retry please")

    assert result == "recovered"
    assert len(fake_model.calls) == 3
    assert sleep_calls == [1.0, 2.0]


def test_rate_limit(monkeypatch) -> None:
    fake_model = FakeModel(
        [
            SimpleNamespace(text="first"),
            SimpleNamespace(text="second"),
        ]
    )
    current_time = [0.0]
    sleep_calls: list[float] = []

    monkeypatch.setattr("app.services.gemini_service.genai.configure", lambda *, api_key: None)
    monkeypatch.setattr(
        "app.services.gemini_service.genai.GenerativeModel",
        lambda model_name: fake_model,
    )

    service = GeminiService(api_key="test-key")
    service._time_func = lambda: current_time[0]
    service._sleep_func = lambda seconds: (sleep_calls.append(seconds), current_time.__setitem__(0, current_time[0] + seconds))
    service._min_request_interval = 1.0

    assert service.generate("first prompt") == "first"
    assert service.generate("second prompt") == "second"
    assert sleep_calls == [1.0]

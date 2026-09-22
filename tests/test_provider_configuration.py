from providers.gemini import (
    GEMINI_TIMEOUT_MS,
    GeminiProvider,
)
from providers.groq import (
    GROQ_MAX_RETRIES,
    GROQ_TIMEOUT_SECONDS,
    GroqProvider,
)


def test_gemini_provider_configures_request_timeout(
    monkeypatch,
):
    captured = {}

    class FakeClient:
        pass

    def fake_client(**kwargs):
        captured.update(
            kwargs
        )

        return FakeClient()

    monkeypatch.setattr(
        "providers.gemini.genai.Client",
        fake_client,
    )

    GeminiProvider(
        api_key="fake-key",
        model="fake-model",
    )

    assert (
        captured["http_options"].timeout
        == GEMINI_TIMEOUT_MS
    )

    assert GEMINI_TIMEOUT_MS == 90_000


def test_groq_provider_configures_timeout_and_retries(
    monkeypatch,
):
    captured = {}

    class FakeClient:
        pass

    def fake_client(**kwargs):
        captured.update(
            kwargs
        )

        return FakeClient()

    monkeypatch.setattr(
        "providers.groq.Groq",
        fake_client,
    )

    GroqProvider(
        api_key="fake-key",
        model="fake-model",
    )

    assert captured["timeout"] == GROQ_TIMEOUT_SECONDS
    assert captured["max_retries"] == GROQ_MAX_RETRIES

    assert GROQ_TIMEOUT_SECONDS == 60.0
    assert GROQ_MAX_RETRIES == 4
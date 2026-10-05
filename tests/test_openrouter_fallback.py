from providers.base import (
    AIProviderUnavailableError,
)
from reviewer import generate_review


class FakeUnavailableProvider:
    def __init__(
        self,
        name: str,
        calls: list[str],
    ):
        self._name = name
        self._calls = calls

    @property
    def name(self) -> str:
        return self._name

    def generate_review(
        self,
        prompt: str,
    ) -> str:
        self._calls.append(
            self._name
        )

        raise AIProviderUnavailableError(
            f"{self._name} unavailable"
        )


class FakeSuccessfulProvider:
    def __init__(
        self,
        name: str,
        calls: list[str],
    ):
        self._name = name
        self._calls = calls

    @property
    def name(self) -> str:
        return self._name

    def generate_review(
        self,
        prompt: str,
    ) -> str:
        self._calls.append(
            self._name
        )

        return "OpenRouter review succeeded."


def test_falls_back_from_gemini_to_groq_to_openrouter(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        "reviewer.GeminiProvider",
        lambda **kwargs: FakeUnavailableProvider(
            "gemini",
            calls,
        ),
    )

    monkeypatch.setattr(
        "reviewer.GroqProvider",
        lambda **kwargs: FakeUnavailableProvider(
            "groq",
            calls,
        ),
    )

    monkeypatch.setattr(
        "reviewer.OpenRouterProvider",
        lambda **kwargs: FakeSuccessfulProvider(
            "openrouter",
            calls,
        ),
    )

    review = generate_review(
        gemini_api_key="fake-gemini-key",
        groq_api_key="fake-groq-key",
        openrouter_api_key="fake-openrouter-key",
        openrouter_model="openrouter/free",
        rules="Test rules.",
        diff="Test diff.",
    )

    assert review == (
        "OpenRouter review succeeded."
    )

    assert calls == [
        "gemini",
        "groq",
        "openrouter",
    ]
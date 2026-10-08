import httpx
import pytest
from groq import APIStatusError

from providers.base import AIProviderUnavailableError
from providers.groq import GroqProvider


class FakeCompletions:
    def __init__(self, error):
        self._error = error

    def create(self, **kwargs):
        raise self._error


class FakeChat:
    def __init__(self, error):
        self.completions = FakeCompletions(error)


class FakeClient:
    def __init__(self, error):
        self.chat = FakeChat(error)


def build_status_error(status_code: int) -> APIStatusError:
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
    )

    response = httpx.Response(
        status_code,
        request=request,
    )

    return APIStatusError(
        f"HTTP {status_code}",
        response=response,
        body=None,
    )


def test_http_413_allows_next_provider():
    provider = GroqProvider(
        api_key="fake-key",
        model="fake-model",
    )

    provider._client = FakeClient(
        build_status_error(413)
    )

    with pytest.raises(AIProviderUnavailableError):
        provider.generate_review(
            "Review this pull request."
        )


def test_http_400_remains_a_permanent_failure():
    provider = GroqProvider(
        api_key="fake-key",
        model="fake-model",
    )

    provider._client = FakeClient(
        build_status_error(400)
    )

    with pytest.raises(
        RuntimeError,
        match="HTTP 400",
    ):
        provider.generate_review(
            "Review this pull request."
        )

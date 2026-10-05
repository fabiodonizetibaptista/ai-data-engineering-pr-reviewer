import json
from urllib.error import HTTPError

import pytest

from providers.base import (
    AIProviderUnavailableError,
)
from providers.openrouter import (
    OpenRouterProvider,
)


class FakeResponse:
    def __init__(
        self,
        body: dict,
    ):
        self._body = json.dumps(
            body
        ).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False


def test_openrouter_returns_review(
    monkeypatch,
):
    response = {
        "choices": [
            {
                "message": {
                    "content": "No blockers found."
                }
            }
        ]
    }

    monkeypatch.setattr(
        "providers.openrouter.urlopen",
        lambda *args, **kwargs: FakeResponse(
            response
        ),
    )

    provider = OpenRouterProvider(
        api_key="fake-key",
        model="fake-model",
    )

    review = provider.generate_review(
        "Review this code."
    )

    assert review == "No blockers found."


def test_openrouter_transient_error_allows_fallback(
    monkeypatch,
):
    def fail(*args, **kwargs):
        raise HTTPError(
            url="https://example.test",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(
        "providers.openrouter.urlopen",
        fail,
    )

    provider = OpenRouterProvider(
        api_key="fake-key",
        model="fake-model",
    )

    with pytest.raises(
        AIProviderUnavailableError
    ):
        provider.generate_review(
            "Review this code."
        )


def test_openrouter_rate_limit_allows_fallback(
    monkeypatch,
):
    def fail(*args, **kwargs):
        raise HTTPError(
            url="https://example.test",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(
        "providers.openrouter.urlopen",
        fail,
    )

    provider = OpenRouterProvider(
        api_key="fake-key",
        model="fake-model",
    )

    with pytest.raises(
        AIProviderUnavailableError
    ):
        provider.generate_review(
            "Review this code."
        )


def test_openrouter_permanent_error_is_not_hidden(
    monkeypatch,
):
    def fail(*args, **kwargs):
        raise HTTPError(
            url="https://example.test",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(
        "providers.openrouter.urlopen",
        fail,
    )

    provider = OpenRouterProvider(
        api_key="fake-key",
        model="fake-model",
    )

    with pytest.raises(
        RuntimeError,
        match="HTTP 401",
    ):
        provider.generate_review(
            "Review this code."
        )


def test_openrouter_rejects_empty_response(
    monkeypatch,
):
    response = {
        "choices": [
            {
                "message": {
                    "content": ""
                }
            }
        ]
    }

    monkeypatch.setattr(
        "providers.openrouter.urlopen",
        lambda *args, **kwargs: FakeResponse(
            response
        ),
    )

    provider = OpenRouterProvider(
        api_key="fake-key",
        model="fake-model",
    )

    with pytest.raises(
        RuntimeError,
        match="empty review",
    ):
        provider.generate_review(
            "Review this code."
        )
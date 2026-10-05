import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from providers.base import (
    AIProvider,
    AIProviderUnavailableError,
)


OPENROUTER_CHAT_COMPLETIONS_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

OPENROUTER_TIMEOUT_SECONDS = 60

TRANSIENT_HTTP_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}


class OpenRouterProvider(AIProvider):
    """
    AI provider backed by OpenRouter.

    OpenRouter is used as the third provider in the fallback chain.

    Only operational/transient failures are converted to
    AIProviderUnavailableError. Permanent errors remain visible
    so configuration or programming problems are not silently hidden.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
    ):
        if not api_key:
            raise ValueError(
                "OpenRouter API key is required."
            )

        if not model:
            raise ValueError(
                "OpenRouter model is required."
            )

        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "openrouter"

    def generate_review(
        self,
        prompt: str,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        request = Request(
            url=OPENROUTER_CHAT_COMPLETIONS_URL,
            data=json.dumps(
                payload
            ).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": (
                    f"Bearer {self._api_key}"
                ),
                "Content-Type": "application/json",
            },
        )

        try:
            with urlopen(
                request,
                timeout=OPENROUTER_TIMEOUT_SECONDS,
            ) as response:
                raw_response = response.read()

        except HTTPError as exc:
            if exc.code in TRANSIENT_HTTP_STATUS_CODES:
                raise AIProviderUnavailableError(
                    "OpenRouter is temporarily unavailable."
                ) from None

            raise RuntimeError(
                "OpenRouter review generation failed "
                f"(HTTP {exc.code})."
            ) from None

        except (
            URLError,
            TimeoutError,
            socket.timeout,
        ):
            raise AIProviderUnavailableError(
                "OpenRouter is temporarily unavailable."
            ) from None

        try:
            response_body = json.loads(
                raw_response.decode("utf-8")
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            raise RuntimeError(
                "OpenRouter returned an invalid response."
            ) from None

        try:
            review = (
                response_body["choices"][0]
                ["message"]["content"]
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ):
            raise RuntimeError(
                "OpenRouter returned an unexpected "
                "response format."
            ) from None

        if (
            not isinstance(review, str)
            or not review.strip()
        ):
            raise RuntimeError(
                "OpenRouter returned an empty review."
            )

        return review.strip()
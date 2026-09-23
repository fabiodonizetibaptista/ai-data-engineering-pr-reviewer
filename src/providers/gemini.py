from google import genai
from google.genai import types

from providers.base import (
    AIProvider,
    AIProviderUnavailableError,
)


GEMINI_TIMEOUT_MS = 90_000

TRANSIENT_HTTP_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}

TRANSIENT_EXCEPTION_NAMES = {
    "APIConnectionError",
    "APITimeoutError",
    "ConnectError",
    "ConnectTimeout",
    "ReadError",
    "ReadTimeout",
    "TimeoutError",
}


class GeminiProvider(AIProvider):
    """
    Provider responsável por gerar reviews utilizando Gemini.

    Falhas transitórias são convertidas para
    AIProviderUnavailableError para permitir fallback.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
    ):
        self._model = model

        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=GEMINI_TIMEOUT_MS,
            ),
        )

    @property
    def name(self) -> str:
        return "gemini"

    def generate_review(
        self,
        prompt: str,
    ) -> str:
        try:
            interaction = self._client.interactions.create(
                model=self._model,
                input=prompt,
            )

        except Exception as exc:
            status_code = (
                getattr(exc, "status_code", None)
                or getattr(exc, "code", None)
            )

            exception_name = type(exc).__name__

            if (
                status_code in TRANSIENT_HTTP_STATUS_CODES
                or exception_name in TRANSIENT_EXCEPTION_NAMES
            ):
                raise AIProviderUnavailableError(
                    "Gemini is temporarily unavailable."
                ) from None

            raise RuntimeError(
                "Gemini review generation failed "
                f"({exception_name})."
            ) from None

        review = interaction.output_text

        if not review:
            raise RuntimeError(
                "Gemini returned an empty review."
            )

        return review.strip()
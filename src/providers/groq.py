from groq import (
    APIConnectionError,
    APIStatusError,
    Groq,
    InternalServerError,
    RateLimitError,
)

from providers.base import (
    AIProvider,
    AIProviderUnavailableError,
)


GROQ_TIMEOUT_SECONDS = 60.0
GROQ_MAX_RETRIES = 4


class GroqProvider(AIProvider):
    """
    Provider responsável por gerar reviews utilizando Groq.

    Falhas transitórias permitem fallback para outro provider.
    Erros permanentes continuam sendo propagados como RuntimeError.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
    ):
        self._model = model

        self._client = Groq(
            api_key=api_key,
            timeout=GROQ_TIMEOUT_SECONDS,
            max_retries=GROQ_MAX_RETRIES,
        )

    @property
    def name(self) -> str:
        return "groq"

    def generate_review(
        self,
        prompt: str,
    ) -> str:
        try:
            completion = (
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )
            )

        except (
            APIConnectionError,
            RateLimitError,
            InternalServerError,
        ):
            raise AIProviderUnavailableError(
                "Groq is temporarily unavailable."
            ) from None

        except APIStatusError as exc:
            raise RuntimeError(
                "Groq review generation failed "
                f"(HTTP {exc.status_code})."
            ) from None

        review = completion.choices[0].message.content

        if not review:
            raise RuntimeError(
                "Groq returned an empty review."
            )

        return review.strip()
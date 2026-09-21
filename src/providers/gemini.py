from google import genai
from google.genai import types

from providers.base import AIProvider, AIProviderUnavailableError


class GeminiProvider(AIProvider):
    """
    Implementação do AIProvider utilizando a API da Gemini.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
    ) -> None:
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "gemini"

    def generate_review(self, prompt: str) -> str:
        """
        Envia o prompt para a Gemini e retorna o conteúdo gerado.
        """

        client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    attempts=4,
                    initial_delay=2.0,
                    max_delay=20.0,
                    exp_base=2.0,
                    http_status_codes=[
                        408,
                        429,
                        500,
                        502,
                        503,
                        504,
                    ],
                )
            ),
        )

        try:
            interaction = client.interactions.create(
                model=self._model,
                input=prompt,
            )

        except Exception as exc:
            status_code = getattr(exc, "code", None)

            # Esses códigos representam falhas que podem ser temporárias.
            # Depois que os retries do SDK se esgotarem, permitimos que
            # outro provider seja utilizado como fallback.
            if status_code in {
                408,
                429,
                500,
                502,
                503,
                504,
            }:
                raise AIProviderUnavailableError(
                    f"Gemini temporarily unavailable "
                    f"(HTTP {status_code})."
                ) from None

            # Salvaguarda para o RateLimitError observado na execução
            # real do GitHub Actions.
            if type(exc).__name__ == "RateLimitError":
                raise AIProviderUnavailableError(
                    "Gemini rate limit remained unavailable after retries."
                ) from None

            raise RuntimeError(
                f"Gemini review generation failed "
                f"({type(exc).__name__})."
            ) from None

        review = interaction.output_text

        if not review or not review.strip():
            raise RuntimeError(
                "Gemini returned an empty Pull Request review."
            )

        return review
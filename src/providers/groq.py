import groq
from groq import Groq

from providers.base import AIProvider, AIProviderUnavailableError


class GroqProvider(AIProvider):
    """
    Implementação do AIProvider utilizando a API da Groq.
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
        return "groq"

    def generate_review(self, prompt: str) -> str:
        """
        Envia o prompt para a Groq e retorna o conteúdo gerado.
        """

        client = Groq(
            api_key=self._api_key,
            max_retries=4,
        )

        try:
            completion = client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

        except groq.APIConnectionError:
            raise AIProviderUnavailableError(
                "Groq API connection failed after retries."
            ) from None

        except groq.RateLimitError:
            raise AIProviderUnavailableError(
                "Groq rate limit remained unavailable after retries."
            ) from None

        except groq.InternalServerError as exc:
            raise AIProviderUnavailableError(
                f"Groq temporarily unavailable "
                f"(HTTP {exc.status_code})."
            ) from None

        except groq.APIStatusError as exc:
            raise RuntimeError(
                f"Groq review generation failed "
                f"(HTTP {exc.status_code})."
            ) from None

        review = completion.choices[0].message.content

        if not review or not review.strip():
            raise RuntimeError(
                "Groq returned an empty Pull Request review."
            )

        return review
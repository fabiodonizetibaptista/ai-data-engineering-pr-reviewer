from providers.base import AIProvider, AIProviderUnavailableError


class FallbackProvider(AIProvider):
    """
    Executa uma cadeia ordenada de provedores de IA.

    Se um provider estiver temporariamente indisponível,
    tenta automaticamente o próximo.

    Erros que não representam indisponibilidade temporária
    continuam sendo propagados, pois podem indicar problemas
    reais de configuração ou implementação.
    """

    def __init__(
        self,
        providers: list[AIProvider],
    ) -> None:
        if not providers:
            raise ValueError(
                "At least one AI provider must be configured."
            )

        self._providers = providers

    @property
    def name(self) -> str:
        return "fallback"

    def generate_review(self, prompt: str) -> str:
        """
        Tenta cada provider na ordem configurada.

        Retorna assim que um provider gerar o review com sucesso.
        """

        unavailable_providers = []

        for provider in self._providers:
            try:
                print(
                    f"Trying AI provider: {provider.name}"
                )

                review = provider.generate_review(prompt)

                print(
                    f"AI provider succeeded: {provider.name}"
                )

                return review

            except AIProviderUnavailableError:
                unavailable_providers.append(provider.name)

                print(
                    f"AI provider unavailable: {provider.name}. "
                    "Trying next provider."
                )

        provider_names = ", ".join(unavailable_providers)

        raise AIProviderUnavailableError(
            "All configured AI providers are unavailable: "
            f"{provider_names}."
        )
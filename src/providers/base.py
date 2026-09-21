from abc import ABC, abstractmethod


class AIProviderUnavailableError(RuntimeError):
    """
    Indica indisponibilidade temporária de um provedor de IA.

    Exemplos:
    - rate limit;
    - indisponibilidade temporária da API;
    - falha transitória após as tentativas de retry.
    """

    pass


class AIProvider(ABC):
    """
    Contrato base para provedores de IA utilizados pelo reviewer.

    Cada implementação concreta, como Gemini ou Groq, deve saber apenas
    como receber um prompt e devolver o review gerado.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nome identificador do provedor.
        """

        pass

    @abstractmethod
    def generate_review(self, prompt: str) -> str:
        """
        Envia o prompt ao provedor e retorna o review gerado.
        """

        pass
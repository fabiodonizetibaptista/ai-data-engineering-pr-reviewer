import os
from pathlib import Path

from google import genai


# O workflow gera o diff do Pull Request neste arquivo temporário.
# Mantemos o conteúdo fora dos logs para evitar exposição acidental
# de código ou informações sensíveis.
DIFF_PATH = Path("/tmp/pr.diff")

# O repositório central do reviewer é baixado para a pasta .ai-reviewer.
# As regras de revisão ficam versionadas separadamente do código Python.
RULES_PATH = Path(".ai-reviewer/rules/data-engineering.md")

# Modelo utilizado pelo reviewer.
MODEL = "gemini-3.8-flash"


def check_gemini_connection(api_key: str) -> None:
    """
    Executa uma chamada mínima à Gemini para validar:

    - autenticação;
    - disponibilidade da API;
    - disponibilidade do modelo configurado.

    Nesta etapa nenhum código do Pull Request é enviado ao modelo.
    """

    client = genai.Client(api_key=api_key)

    try:
        interaction = client.interactions.create(
            model=MODEL,
            input="Reply only with OK.",
        )
    except Exception as exc:
        # Não exibimos a mensagem completa da exceção para reduzir o risco
        # de informações sensíveis aparecerem nos logs do workflow.
        raise RuntimeError(
            f"Gemini API health check failed ({type(exc).__name__})."
        ) from None

    if not interaction.output_text:
        raise RuntimeError(
            "Gemini API health check returned an empty response."
        )

    print("Gemini API connection: OK")


def main() -> None:
    """
    Valida os insumos necessários para o reviewer e testa a conexão
    com a Gemini.

    Nesta etapa ainda NÃO enviamos o diff ou as regras para a IA.
    """

    if not DIFF_PATH.exists():
        raise FileNotFoundError(
            f"Pull Request diff not found at: {DIFF_PATH}"
        )

    diff = DIFF_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    if not RULES_PATH.exists():
        raise FileNotFoundError(
            f"Review rules not found at: {RULES_PATH}"
        )

    rules = RULES_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not available."
        )

    diff_lines = len(diff.splitlines())
    diff_size_bytes = DIFF_PATH.stat().st_size

    print("AI reviewer initialized successfully.")
    print(f"Diff available: {bool(diff.strip())}")
    print(f"Diff lines: {diff_lines}")
    print(f"Diff size (bytes): {diff_size_bytes}")
    print(f"Review rules available: {bool(rules.strip())}")
    print("Gemini API key available: True")

    check_gemini_connection(gemini_api_key)


if __name__ == "__main__":
    main()
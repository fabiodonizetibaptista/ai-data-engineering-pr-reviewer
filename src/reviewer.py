import os
from pathlib import Path


# O workflow gera o diff do Pull Request neste arquivo temporário.
# Mantemos o conteúdo fora dos logs para evitar exposição acidental
# de código ou informações sensíveis.
DIFF_PATH = Path("/tmp/pr.diff")

# O repositório central do reviewer é baixado para a pasta .ai-reviewer.
# As regras de revisão ficam versionadas separadamente do código Python.
RULES_PATH = Path(".ai-reviewer/rules/data-engineering.md")


def main() -> None:
    """
    Valida se os insumos necessários para o reviewer estão disponíveis.

    Nesta etapa ainda não executamos nenhuma chamada de IA.
    Apenas confirmamos que o programa consegue acessar:
    1. o diff do Pull Request;
    2. as regras de revisão;
    3. a chave da API da Gemini via variável de ambiente.
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


if __name__ == "__main__":
    main()
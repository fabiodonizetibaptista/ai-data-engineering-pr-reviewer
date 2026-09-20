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
    Valida se o diff do Pull Request e as regras de revisão estão
    disponíveis para o reviewer.

    Nesta etapa ainda não executamos nenhuma análise com IA.
    Apenas confirmamos que o programa consegue acessar com segurança
    os dois insumos principais da futura revisão:
    1. o que mudou no Pull Request;
    2. quais critérios devem ser usados na avaliação.
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

    diff_lines = len(diff.splitlines())
    diff_size_bytes = DIFF_PATH.stat().st_size

    print("AI reviewer initialized successfully.")
    print(f"Diff available: {bool(diff.strip())}")
    print(f"Diff lines: {diff_lines}")
    print(f"Diff size (bytes): {diff_size_bytes}")
    print(f"Review rules available: {bool(rules.strip())}")


if __name__ == "__main__":
    main()
from pathlib import Path


# O workflow gera o diff do Pull Request neste arquivo temporário.
# Mantemos o conteúdo fora dos logs para evitar exposição acidental
# de código ou informações sensíveis.
DIFF_PATH = Path("/tmp/pr.diff")


def main() -> None:
    """
    Valida se o diff do Pull Request está disponível para o reviewer.

    Nesta primeira versão, não analisamos o conteúdo.
    Apenas confirmamos que o Python consegue acessá-lo com segurança.
    """

    if not DIFF_PATH.exists():
        raise FileNotFoundError(
            f"Pull Request diff not found at: {DIFF_PATH}"
        )

    diff = DIFF_PATH.read_text(
        encoding="utf-8",
        errors="replace",
    )

    diff_lines = len(diff.splitlines())
    diff_size_bytes = DIFF_PATH.stat().st_size

    print("AI reviewer initialized successfully.")
    print(f"Diff available: {bool(diff.strip())}")
    print(f"Diff lines: {diff_lines}")
    print(f"Diff size (bytes): {diff_size_bytes}")


if __name__ == "__main__":
    main()
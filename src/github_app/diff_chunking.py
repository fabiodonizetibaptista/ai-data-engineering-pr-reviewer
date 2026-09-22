import re
from dataclasses import dataclass


MAX_CHUNK_BYTES = 20_000
MAX_REVIEW_CHUNKS = 8


@dataclass(frozen=True)
class DiffChunkPlan:
    """
    Plano de divisão do diff para revisão por IA.

    total_chunks representa quantos chunks seriam necessários
    para revisar todo o diff.

    omitted_chunks e omitted_bytes deixam explícito quando
    o limite operacional impediu cobertura completa.
    """

    chunks: tuple[str, ...]
    total_chunks: int
    omitted_chunks: int
    omitted_bytes: int

    @property
    def is_partial(self) -> bool:
        return self.omitted_chunks > 0


def _byte_length(text: str) -> int:
    return len(text.encode("utf-8"))


def _split_by_byte_budget(
    text: str,
    max_bytes: int,
) -> list[str]:
    """
    Divide um texto que sozinho excede o budget.

    Esse é o fallback para arquivos/hunks muito grandes.
    Mantém UTF-8 válido mesmo quando o corte ocorre próximo
    a um caractere multibyte.
    """

    raw = text.encode("utf-8")
    chunks: list[str] = []

    while raw:
        candidate = raw[:max_bytes]

        while candidate:
            try:
                decoded = candidate.decode("utf-8")
                break
            except UnicodeDecodeError as exc:
                candidate = candidate[:exc.start]

        if not candidate:
            raise RuntimeError(
                "Unable to split diff while preserving UTF-8."
            )

        chunks.append(decoded)

        consumed = len(candidate)
        raw = raw[consumed:]

    return chunks


def _split_diff_into_file_sections(
    diff: str,
) -> list[str]:
    """
    Separa o diff preferencialmente pelas fronteiras:

        diff --git ...

    Isso evita misturar arquivos desnecessariamente
    durante a análise.
    """

    sections = re.split(
        r"(?=^diff --git )",
        diff,
        flags=re.MULTILINE,
    )

    return [
        section
        for section in sections
        if section
    ]


def chunk_pull_request_diff(
    diff: str,
    max_chunk_bytes: int = MAX_CHUNK_BYTES,
    max_chunks: int = MAX_REVIEW_CHUNKS,
) -> DiffChunkPlan:
    """
    Divide o diff em chunks adequados para envio aos providers.

    Estratégia:

    - preserva fronteiras de arquivos sempre que possível;
    - agrupa arquivos pequenos dentro do mesmo chunk;
    - divide arquivos muito grandes somente quando necessário;
    - limita o número máximo de chamadas por PR;
    - nunca oculta que parte do diff ficou de fora.
    """

    if max_chunk_bytes <= 0:
        raise ValueError(
            "max_chunk_bytes must be greater than zero."
        )

    if max_chunks <= 0:
        raise ValueError(
            "max_chunks must be greater than zero."
        )

    if not diff:
        return DiffChunkPlan(
            chunks=("",),
            total_chunks=1,
            omitted_chunks=0,
            omitted_bytes=0,
        )

    file_sections = _split_diff_into_file_sections(
        diff
    )

    pieces: list[str] = []

    for section in file_sections:
        if _byte_length(section) <= max_chunk_bytes:
            pieces.append(section)
            continue

        pieces.extend(
            _split_by_byte_budget(
                section,
                max_chunk_bytes,
            )
        )

    packed_chunks: list[str] = []
    current_chunk = ""

    for piece in pieces:
        candidate = current_chunk + piece

        if (
            current_chunk
            and _byte_length(candidate) > max_chunk_bytes
        ):
            packed_chunks.append(current_chunk)
            current_chunk = piece
        else:
            current_chunk = candidate

    if current_chunk:
        packed_chunks.append(current_chunk)

    total_chunks = len(packed_chunks)

    selected_chunks = packed_chunks[:max_chunks]
    omitted = packed_chunks[max_chunks:]

    return DiffChunkPlan(
        chunks=tuple(selected_chunks),
        total_chunks=total_chunks,
        omitted_chunks=len(omitted),
        omitted_bytes=sum(
            _byte_length(chunk)
            for chunk in omitted
        ),
    )
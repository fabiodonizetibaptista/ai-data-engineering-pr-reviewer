from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewResult:
    """Resultado verific?vel de uma execu??o de revis?o."""

    status: str
    published: bool
    completed_chunks: int
    total_chunks: int
    reason: str

    @property
    def coverage_pct(self) -> float:
        if self.total_chunks <= 0:
            return 0.0
        return round(100 * self.completed_chunks / self.total_chunks, 2)

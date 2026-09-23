import os
import time
from pathlib import Path

from github_app.authentication import (
    create_installation_access_token,
    generate_app_jwt,
    get_authenticated_app_slug,
    load_github_app_credentials,
)
from github_app.diff_chunking import (
    DiffChunkPlan,
    chunk_pull_request_diff,
)
from github_app.events import PullRequestEvent
from github_app.github_client import (
    get_pull_request_diff,
    publish_or_update_pull_request_comment,
)
from providers.base import AIProviderUnavailableError
from reviewer import generate_review


RULES_PATH = (
    Path(__file__).resolve().parents[2]
    / "rules"
    / "data-engineering.md"
)


def _build_chunk_rules(
    rules: str,
    chunk_number: int,
    review_chunk_count: int,
    plan: DiffChunkPlan,
) -> str:
    """
    Acrescenta contexto de cobertura às regras sem alterar
    permanentemente o documento normativo do reviewer.
    """

    coverage = (
        "\n\n"
        "## Runtime Review Context\n\n"
        f"You are reviewing chunk {chunk_number} "
        f"of {review_chunk_count} supplied to the AI reviewer.\n\n"
        "This chunk is not necessarily representative of the entire pull request.\n"
        "Do not infer the absence of tests, logging, validation, documentation, "
        "error handling or other functionality from this chunk alone.\n"
        "Limit this chunk review to the strongest findings supported by visible code.\n"
        "Prefer at most 5 findings for this chunk.\n"
    )

    if plan.is_partial:
        coverage += (
            "\nThe reviewer could not process the entire pull request within "
            "the configured execution budget. "
            f"{plan.omitted_chunks} chunk(s) were omitted. "
            "Do not claim complete pull request coverage.\n"
        )

    return rules + coverage


def _strip_review_title(
    review: str,
) -> str:
    """
    Remove apenas o título repetitivo do review parcial,
    preservando todo o restante da resposta do provider.
    """

    lines = review.strip().splitlines()

    if not lines:
        return ""

    first_line = (
        lines[0]
        .replace("#", "")
        .strip()
        .lower()
    )

    if first_line == "ai data engineering review":
        lines = lines[1:]

    return "\n".join(lines).strip()


def combine_chunk_reviews(
    reviews: list[str],
    plan: DiffChunkPlan,
) -> str:
    """
    Consolidação determinística inicial dos reviews parciais.

    Nesta etapa evitamos uma chamada extra ao LLM.
    A futura saída estruturada permitirá deduplicação
    semântica mais sofisticada.
    """

    if not reviews:
        raise ValueError(
            "At least one chunk review is required."
        )

    if len(reviews) == 1 and not plan.is_partial:
        return reviews[0]

    reviewed_count = len(reviews)

    if plan.is_partial:
        coverage_message = (
            f"> Review coverage: {reviewed_count} of "
            f"{plan.total_chunks} generated chunks were analyzed. "
            f"{plan.omitted_chunks} chunk(s) were omitted due to "
            "the configured execution budget."
        )
    else:
        coverage_message = (
            f"> Review coverage: the pull request was analyzed "
            f"in {reviewed_count} chunks."
        )

    sections = [
        "# AI Data Engineering Review",
        "",
        coverage_message,
    ]

    for index, review in enumerate(
        reviews,
        start=1,
    ):
        sections.extend(
            [
                "",
                "---",
                "",
                f"## Partial Review {index} of {reviewed_count}",
                "",
                _strip_review_title(review),
            ]
        )

    return "\n".join(sections).strip()


def process_pull_request_event(
    event: PullRequestEvent,
) -> bool:
    """
    Executa o pipeline completo de análise do pull request.
    """

    credentials = load_github_app_credentials()

    app_jwt = generate_app_jwt(
        app_id=credentials.app_id,
        private_key=credentials.private_key,
        current_time=int(time.time()),
    )

    app_slug = get_authenticated_app_slug(
        app_jwt=app_jwt,
    )

    bot_login = f"{app_slug}[bot]"

    installation_token = create_installation_access_token(
        app_jwt=app_jwt,
        installation_id=event.installation_id,
    )

    diff = get_pull_request_diff(
        installation_token=installation_token,
        repository_full_name=event.repository_full_name,
        pull_request_number=event.pull_request_number,
    )

    plan = chunk_pull_request_diff(
        diff
    )

    rules = RULES_PATH.read_text(
        encoding="utf-8",
    )

    gemini_api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    groq_api_key = os.getenv(
        "GROQ_API_KEY"
    )

    chunk_reviews: list[str] = []

    try:
        for index, chunk in enumerate(
            plan.chunks,
            start=1,
        ):
            chunk_rules = _build_chunk_rules(
                rules=rules,
                chunk_number=index,
                review_chunk_count=len(plan.chunks),
                plan=plan,
            )

            review = generate_review(
                gemini_api_key=gemini_api_key,
                groq_api_key=groq_api_key,
                rules=chunk_rules,
                diff=chunk,
            )

            chunk_reviews.append(
                review
            )

    except AIProviderUnavailableError:
        return False

    final_review = combine_chunk_reviews(
        reviews=chunk_reviews,
        plan=plan,
    )

    publish_or_update_pull_request_comment(
        installation_token=installation_token,
        repository_full_name=event.repository_full_name,
        pull_request_number=event.pull_request_number,
        review=final_review,
        bot_login=bot_login,
    )

    return True
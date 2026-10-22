import logging

from github_app.events import PullRequestEvent
from github_app.processor import process_pull_request_event


logger = logging.getLogger("uvicorn.error")


def run_pull_request_review_safely(
    event: PullRequestEvent,
) -> None:
    """
    Executa o processamento do review sem permitir que uma falha
    do pipeline escape para o lifecycle HTTP do FastAPI.

    Informações sensíveis, payloads, diffs, tokens e mensagens
    completas de exceção não são registradas.
    """

    logger.info(
        "review.started repo=%s pr=%s",
        event.repository_full_name,
        event.pull_request_number,
    )

    try:
        published = process_pull_request_event(
            event
        )

        if published:
            logger.info(
                "AI pull request review completed successfully. "
                "review.finished status=success repo=%s pr=%s",
                event.repository_full_name,
                event.pull_request_number,
            )
        else:
            logger.warning(
                "AI pull request review was not published "
                "because all providers were unavailable. "
                "review.finished status=providers_unavailable "
                "repo=%s pr=%s",
                event.repository_full_name,
                event.pull_request_number,
            )

    except Exception as exc:
        logger.error(
            "review.finished status=error repo=%s pr=%s "
            "error_type=%s",
            event.repository_full_name,
            event.pull_request_number,
            type(exc).__name__,
        )
import logging

from github_app.events import PullRequestEvent
from github_app.processor import process_pull_request_event


logger = logging.getLogger(__name__)


def run_pull_request_review_safely(
    event: PullRequestEvent,
) -> None:
    """
    Executa o processamento do review sem permitir que uma falha
    do pipeline escape para o lifecycle HTTP do FastAPI.

    Informações sensíveis, payloads, diffs, tokens e mensagens
    completas de exceção não são registradas.
    """

    try:
        published = process_pull_request_event(
            event
        )

        if published:
            logger.info(
                "AI pull request review completed successfully."
            )
        else:
            logger.warning(
                "AI pull request review was not published "
                "because all providers were unavailable."
            )

    except Exception as exc:
        logger.error(
            "AI pull request review failed. error_type=%s",
            type(exc).__name__,
        )
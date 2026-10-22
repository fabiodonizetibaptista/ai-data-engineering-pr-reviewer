import logging

from github_app.events import PullRequestEvent
from github_app.processor import process_pull_request_event


logger = logging.getLogger("uvicorn.error")


def run_pull_request_review_safely(event: PullRequestEvent) -> None:
    """Executa o processamento sem expor dados sens?veis em logs."""
    logger.info(
        "review.started repo=%s pr=%s",
        event.repository_full_name,
        event.pull_request_number,
    )

    try:
        result = process_pull_request_event(event)
        message = (
            "review.finished status=%s published=%s "
            "completed_chunks=%s total_chunks=%s coverage_pct=%.2f "
            "reason=%s repo=%s pr=%s"
        )
        args = (
            result.status,
            str(result.published).lower(),
            result.completed_chunks,
            result.total_chunks,
            result.coverage_pct,
            result.reason,
            event.repository_full_name,
            event.pull_request_number,
        )
        if result.status == "complete":
            logger.info(message, *args)
        else:
            logger.warning(message, *args)
    except Exception as exc:
        # Nunca registrar a mensagem da exce??o: pode conter segredos.
        logger.error(
            "review.finished status=error repo=%s pr=%s error_type=%s",
            event.repository_full_name,
            event.pull_request_number,
            type(exc).__name__,
        )

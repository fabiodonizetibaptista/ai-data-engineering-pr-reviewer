import os
import time
from pathlib import Path

from github_app.authentication import (
    create_installation_access_token,
    generate_app_jwt,
    get_authenticated_app_slug,
    load_github_app_credentials,
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

MAX_REVIEW_DIFF_BYTES = 20_000

TRUNCATION_NOTICE = (
    "\n\n"
    "[DIFF TRUNCATED BY REVIEWER]\n"
    "The pull request diff exceeded the current review input budget. "
    "Review only the visible portion and do not make claims about omitted code."
)


def limit_diff_for_review(diff: str) -> str:
    """
    Limita o diff enviado ao provider para evitar requests excessivamente
    grandes durante a análise.

    A truncagem ocorre por bytes UTF-8, preservando texto válido.
    O aviso explícito impede que o modelo trate a amostra como o PR completo.
    """

    encoded_diff = diff.encode("utf-8")

    if len(encoded_diff) <= MAX_REVIEW_DIFF_BYTES:
        return diff

    truncated_diff = encoded_diff[
        :MAX_REVIEW_DIFF_BYTES
    ].decode(
        "utf-8",
        errors="ignore",
    )

    return truncated_diff + TRUNCATION_NOTICE


def process_pull_request_event(
    event: PullRequestEvent,
) -> bool:
    """
    Executa o pipeline completo de análise de um pull request.
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

    diff = limit_diff_for_review(diff)

    rules = RULES_PATH.read_text(
        encoding="utf-8",
    )

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    try:
        review = generate_review(
            gemini_api_key=gemini_api_key,
            groq_api_key=groq_api_key,
            rules=rules,
            diff=diff,
        )
    except AIProviderUnavailableError:
        return False

    publish_or_update_pull_request_comment(
        installation_token=installation_token,
        repository_full_name=event.repository_full_name,
        pull_request_number=event.pull_request_number,
        review=review,
        bot_login=bot_login,
    )

    return True
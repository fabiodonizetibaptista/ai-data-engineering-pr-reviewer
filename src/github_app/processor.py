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
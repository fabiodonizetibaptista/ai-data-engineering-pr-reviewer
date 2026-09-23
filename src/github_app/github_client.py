import json
from urllib.parse import quote
from urllib.request import Request, urlopen


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"

REVIEW_MARKER = "<!-- ai-data-engineering-reviewer -->"


def _parse_repository_full_name(
    repository_full_name: str,
) -> tuple[str, str]:

    try:
        owner, repository = repository_full_name.split("/", maxsplit=1)
    except ValueError as exc:
        raise ValueError(
            "repository_full_name must use the format 'owner/repository'."
        ) from exc

    if not owner or not repository:
        raise ValueError(
            "repository_full_name must use the format 'owner/repository'."
        )

    return (
        quote(owner, safe=""),
        quote(repository, safe=""),
    )


def _github_headers(
    installation_token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {installation_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def get_pull_request_diff(
    installation_token: str,
    repository_full_name: str,
    pull_request_number: int,
) -> str:

    owner, repository = _parse_repository_full_name(
        repository_full_name
    )

    url = (
        f"{GITHUB_API_BASE_URL}/repos/"
        f"{owner}/{repository}/pulls/{pull_request_number}"
    )

    request = Request(
        url=url,
        method="GET",
        headers={
            "Authorization": f"Bearer {installation_token}",
            "Accept": "application/vnd.github.diff",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
    )

    with urlopen(
        request,
        timeout=15,
    ) as response:
        return response.read().decode("utf-8")


def find_existing_review_comment(
    installation_token: str,
    repository_full_name: str,
    pull_request_number: int,
    bot_login: str,
) -> int | None:
    """
    Localiza um review anterior criado pelo próprio GitHub App.

    São exigidos simultaneamente:
    - marker exclusivo do reviewer;
    - login exato do bot do GitHub App.

    Isso evita atualizar comentários de terceiros.
    """

    owner, repository = _parse_repository_full_name(
        repository_full_name
    )

    page = 1

    while True:
        url = (
            f"{GITHUB_API_BASE_URL}/repos/"
            f"{owner}/{repository}/issues/"
            f"{pull_request_number}/comments"
            f"?per_page=100&page={page}"
        )

        request = Request(
            url=url,
            method="GET",
            headers=_github_headers(
                installation_token
            ),
        )

        with urlopen(
            request,
            timeout=15,
        ) as response:
            comments = json.loads(
                response.read().decode("utf-8")
            )

        for comment in comments:
            body = comment.get("body") or ""
            user = comment.get("user") or {}

            if (
                REVIEW_MARKER in body
                and user.get("login") == bot_login
            ):
                comment_id = comment.get("id")

                if isinstance(comment_id, int):
                    return comment_id

        if len(comments) < 100:
            return None

        page += 1


def publish_or_update_pull_request_comment(
    installation_token: str,
    repository_full_name: str,
    pull_request_number: int,
    review: str,
    bot_login: str,
) -> int:
    """
    Cria o comentário do reviewer ou atualiza o comentário
    anterior pertencente ao próprio GitHub App.
    """

    owner, repository = _parse_repository_full_name(
        repository_full_name
    )

    comment_body = f"{REVIEW_MARKER}\n\n{review}"

    request_body = json.dumps(
        {
            "body": comment_body,
        }
    ).encode("utf-8")

    existing_comment_id = find_existing_review_comment(
        installation_token=installation_token,
        repository_full_name=repository_full_name,
        pull_request_number=pull_request_number,
        bot_login=bot_login,
    )

    if existing_comment_id is None:
        url = (
            f"{GITHUB_API_BASE_URL}/repos/"
            f"{owner}/{repository}/issues/"
            f"{pull_request_number}/comments"
        )

        method = "POST"

    else:
        url = (
            f"{GITHUB_API_BASE_URL}/repos/"
            f"{owner}/{repository}/issues/comments/"
            f"{existing_comment_id}"
        )

        method = "PATCH"

    request = Request(
        url=url,
        data=request_body,
        method=method,
        headers={
            **_github_headers(
                installation_token
            ),
            "Content-Type": "application/json",
        },
    )

    with urlopen(
        request,
        timeout=15,
    ) as response:
        response_body = json.loads(
            response.read().decode("utf-8")
        )

    comment_id = response_body.get("id")

    if not isinstance(comment_id, int):
        raise RuntimeError(
            "GitHub did not return the review comment id."
        )

    return comment_id
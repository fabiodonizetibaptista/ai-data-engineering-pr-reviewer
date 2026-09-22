from urllib.parse import quote
from urllib.request import Request, urlopen


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"


def get_pull_request_diff(
    installation_token: str,
    repository_full_name: str,
    pull_request_number: int,
) -> str:
    """
    Obtém o diff de um pull request usando o token da instalação.

    O token é enviado somente no header Authorization
    e nunca deve ser registrado em logs.
    """

    try:
        owner, repository = repository_full_name.split("/", maxsplit=1)
    except ValueError as exc:
        raise ValueError(
            "repository_full_name must use the format 'owner/repository'."
        ) from exc

    owner = quote(owner, safe="")
    repository = quote(repository, safe="")

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
import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

import jwt


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"


@dataclass(frozen=True)
class GitHubAppCredentials:
    """
    Credenciais necessárias para autenticar o GitHub App.

    A chave privada é mantida apenas em memória
    e nunca deve ser registrada em logs.
    """

    app_id: str
    private_key: bytes


def load_github_app_credentials() -> GitHubAppCredentials:
    """
    Carrega o App ID e a chave privada do GitHub App
    a partir das configurações do ambiente.
    """

    app_id = os.getenv("GITHUB_APP_ID")
    private_key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")

    if not app_id:
        raise RuntimeError(
            "GITHUB_APP_ID environment variable is not available."
        )

    if not private_key_path:
        raise RuntimeError(
            "GITHUB_APP_PRIVATE_KEY_PATH environment variable is not available."
        )

    private_key = Path(private_key_path).read_bytes()

    return GitHubAppCredentials(
        app_id=app_id,
        private_key=private_key,
    )


def generate_app_jwt(
    app_id: str,
    private_key: bytes,
    current_time: int,
) -> str:
    """
    Gera o JWT usado para autenticar o GitHub App.
    """

    payload = {
        "iat": current_time - 60,
        "exp": current_time + 600,
        "iss": app_id,
    }

    return jwt.encode(
        payload=payload,
        key=private_key,
        algorithm="RS256",
    )


def get_authenticated_app_slug(
    app_jwt: str,
) -> str:
    """
    Obtém o slug oficial do GitHub App autenticado.

    O slug será usado para identificar com segurança
    o comentário pertencente ao próprio bot.
    """

    request = Request(
        url=f"{GITHUB_API_BASE_URL}/app",
        method="GET",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
    )

    with urlopen(
        request,
        timeout=10,
    ) as response:
        response_body = json.loads(
            response.read().decode("utf-8")
        )

    slug = response_body.get("slug")

    if not slug:
        raise RuntimeError(
            "GitHub did not return the authenticated app slug."
        )

    return slug


def create_installation_access_token(
    app_jwt: str,
    installation_id: int,
) -> str:
    """
    Troca o JWT do GitHub App por um Installation Access Token.
    """

    url = (
        f"{GITHUB_API_BASE_URL}/app/installations/"
        f"{installation_id}/access_tokens"
    )

    request = Request(
        url=url,
        data=b"",
        method="POST",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
    )

    with urlopen(
        request,
        timeout=10,
    ) as response:
        response_body = json.loads(
            response.read().decode("utf-8")
        )

    token = response_body.get("token")

    if not token:
        raise RuntimeError(
            "GitHub did not return an installation access token."
        )

    return token
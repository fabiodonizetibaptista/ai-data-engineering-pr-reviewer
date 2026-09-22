import os
from dataclasses import dataclass
from pathlib import Path

import jwt


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

    Variáveis esperadas:
    - GITHUB_APP_ID
    - GITHUB_APP_PRIVATE_KEY_PATH
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

    O token é assinado com RS256 e contém:
    - iat: instante de emissão, com pequena margem para clock skew.
    - exp: expiração do token.
    - iss: identificador do GitHub App.
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
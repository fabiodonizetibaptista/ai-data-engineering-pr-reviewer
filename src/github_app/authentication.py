import jwt


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
import hashlib
import hmac


def verify_webhook_signature(
    payload: bytes,
    signature: str | None,
    secret: str,
) -> bool:
    """
    Valida a assinatura HMAC-SHA256 enviada pelo GitHub.

    O GitHub envia a assinatura no header X-Hub-Signature-256
    no formato:

        sha256=<hash>

    A comparação utiliza hmac.compare_digest para evitar
    comparações vulneráveis a timing attacks.
    """

    if not signature:
        return False

    expected_signature = (
        "sha256="
        + hmac.new(
            key=secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(
        expected_signature,
        signature,
    )
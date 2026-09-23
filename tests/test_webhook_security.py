import hashlib
import hmac

from github_app.security import verify_webhook_signature


def test_accepts_valid_webhook_signature():
    """
    Deve aceitar uma assinatura válida gerada com o mesmo secret.
    """

    payload = b'{"action":"opened"}'
    secret = "test-secret"

    signature = (
        "sha256="
        + hmac.new(
            key=secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )

    assert verify_webhook_signature(
        payload=payload,
        signature=signature,
        secret=secret,
    ) is True


def test_rejects_invalid_webhook_signature():
    """
    Deve rejeitar uma assinatura que não corresponde ao payload.
    """

    payload = b'{"action":"opened"}'
    secret = "test-secret"

    assert verify_webhook_signature(
        payload=payload,
        signature="sha256=invalid-signature",
        secret=secret,
    ) is False


def test_rejects_missing_webhook_signature():
    """
    Deve rejeitar requisições sem assinatura.
    """

    payload = b'{"action":"opened"}'

    assert verify_webhook_signature(
        payload=payload,
        signature=None,
        secret="test-secret",
    ) is False
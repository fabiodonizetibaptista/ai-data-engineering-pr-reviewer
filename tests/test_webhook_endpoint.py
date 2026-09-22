import hashlib
import hmac

from fastapi.testclient import TestClient

from github_app.webhook import app


client = TestClient(app)


def build_signature(
    payload: bytes,
    secret: str,
) -> str:
    """
    Gera uma assinatura HMAC-SHA256 válida para os testes.
    """

    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def test_accepts_webhook_with_valid_signature(monkeypatch):
    """
    Um webhook corretamente assinado e referente a um pull_request
    deve ser aceito.
    """

    secret = "test-secret"
    payload = b'{"action":"opened"}'

    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        secret,
    )

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": build_signature(
                payload=payload,
                secret=secret,
            ),
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-id",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
    }


def test_rejects_webhook_with_invalid_signature(monkeypatch):
    """
    Um webhook com assinatura inválida deve ser rejeitado.
    """

    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        "test-secret",
    )

    response = client.post(
        "/webhook",
        content=b'{"action":"opened"}',
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-id",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid webhook signature.",
    }


def test_ignores_non_pull_request_event(monkeypatch):
    """
    Eventos que não sejam pull_request devem ser aceitos pelo endpoint,
    mas ignorados pelo reviewer.
    """

    secret = "test-secret"
    payload = b'{"action":"created"}'

    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        secret,
    )

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": build_signature(
                payload=payload,
                secret=secret,
            ),
            "X-GitHub-Event": "installation",
            "X-GitHub-Delivery": "test-delivery-id",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
    }

def test_ignores_unsupported_pull_request_action(monkeypatch):
    """
    Eventos pull_request com ações que não exigem nova análise
    devem ser aceitos, mas ignorados pelo reviewer.
    """

    secret = "test-secret"
    payload = b'{"action":"closed"}'

    monkeypatch.setenv(
        "GITHUB_WEBHOOK_SECRET",
        secret,
    )

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": build_signature(
                payload=payload,
                secret=secret,
            ),
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-id",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
    }
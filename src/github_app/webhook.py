import json
import os

from fastapi import FastAPI, Header, HTTPException, Request

from github_app.events import parse_pull_request_event
from github_app.security import verify_webhook_signature


app = FastAPI(
    title="AI Data Engineering PR Reviewer",
    version="0.1.0",
)


SUPPORTED_PULL_REQUEST_ACTIONS = {
    "opened",
    "synchronize",
    "reopened",
}


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Endpoint simples de health check.

    Serve para validar que o backend do GitHub App
    está em execução e respondendo corretamente.
    """

    return {
        "status": "healthy",
    }


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(
        default=None,
        alias="X-Hub-Signature-256",
    ),
    x_github_event: str | None = Header(
        default=None,
        alias="X-GitHub-Event",
    ),
) -> dict[str, str]:
    """
    Recebe eventos enviados pelo GitHub App.

    O fluxo é:

    1. Obtém o payload bruto.
    2. Valida a assinatura HMAC enviada pelo GitHub.
    3. Ignora eventos que não sejam pull_request.
    4. Ignora ações de pull_request que não exigem nova revisão.
    5. Valida os metadados obrigatórios do pull request.
    6. Aceita somente eventos que possam seguir para o reviewer.
    """

    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")

    if not webhook_secret:
        raise RuntimeError(
            "GITHUB_WEBHOOK_SECRET environment variable is not available."
        )

    payload = await request.body()

    is_valid_signature = verify_webhook_signature(
        payload=payload,
        signature=x_hub_signature_256,
        secret=webhook_secret,
    )

    if not is_valid_signature:
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature.",
        )

    if x_github_event != "pull_request":
        return {
            "status": "ignored",
        }

    event_payload = json.loads(payload)

    action = event_payload.get("action")

    if action not in SUPPORTED_PULL_REQUEST_ACTIONS:
        return {
            "status": "ignored",
        }

    try:
        parse_pull_request_event(event_payload)
    except (KeyError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid pull request payload.",
        )

    return {
        "status": "accepted",
    }
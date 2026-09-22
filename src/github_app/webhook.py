import os

from fastapi import FastAPI, Header, HTTPException, Request

from github_app.security import verify_webhook_signature


app = FastAPI(
    title="AI Data Engineering PR Reviewer",
    version="0.1.0",
)


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
) -> dict[str, str]:
    """
    Recebe eventos enviados pelo GitHub App.

    Antes de processar qualquer conteúdo, valida a assinatura
    criptográfica enviada pelo GitHub.
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

    return {
        "status": "accepted",
    }
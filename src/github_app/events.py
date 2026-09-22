from dataclasses import dataclass


@dataclass(frozen=True)
class PullRequestEvent:
    """
    Representa apenas os metadados necessários
    para processar um evento de pull request.
    """

    action: str
    pull_request_number: int
    repository_full_name: str
    installation_id: int


def parse_pull_request_event(payload: dict) -> PullRequestEvent:
    """
    Extrai do payload do GitHub apenas os dados necessários
    para o fluxo do reviewer.

    Evitamos carregar ou propagar o payload inteiro
    para reduzir acoplamento e exposição desnecessária de dados.
    """

    return PullRequestEvent(
        action=payload["action"],
        pull_request_number=payload["number"],
        repository_full_name=payload["repository"]["full_name"],
        installation_id=payload["installation"]["id"],
    )
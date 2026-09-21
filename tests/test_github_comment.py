import json

import reviewer


class FakeResponse:
    """
    Simula uma resposta HTTP retornada pela API do GitHub.

    Isso permite testar a lógica sem fazer chamadas reais
    à internet ou consumir a API do GitHub.
    """

    def __init__(
        self,
        data: list[dict],
        status: int = 200,
    ) -> None:
        self._data = data
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self._data).encode("utf-8")


def test_finds_existing_ai_review_comment(monkeypatch):
    """
    Deve retornar o ID do comentário quando ele contém
    o marker do reviewer e pertence ao github-actions bot.
    """

    comments = [
        {
            "id": 100,
            "body": "Regular developer comment.",
            "user": {
                "login": "developer",
            },
        },
        {
            "id": 200,
            "body": (
                f"{reviewer.REVIEW_MARKER}\n\n"
                "# AI Data Engineering Review"
            ),
            "user": {
                "login": "github-actions[bot]",
            },
        },
    ]

    def fake_urlopen(request, timeout):
        return FakeResponse(comments)

    monkeypatch.setattr(
        reviewer.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    comment_id = reviewer.find_existing_review_comment(
        github_token="fake-token",
        repository="owner/repository",
        pull_request_number=123,
    )

    assert comment_id == 200

def test_ignores_marker_from_non_bot_author(monkeypatch):
    """
    Um comentário com o marker correto não deve ser considerado
    pertencente ao reviewer se tiver sido criado por outro usuário.
    """

    responses = [
        [
            {
                "id": 300,
                "body": (
                    f"{reviewer.REVIEW_MARKER}\n\n"
                    "Fake AI review."
                ),
                "user": {
                    "login": "developer",
                },
            },
        ],
        [],
    ]

    call_count = 0

    def fake_urlopen(request, timeout):
        nonlocal call_count

        response = FakeResponse(
            responses[call_count]
        )

        call_count += 1

        return response

    monkeypatch.setattr(
        reviewer.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    comment_id = reviewer.find_existing_review_comment(
        github_token="fake-token",
        repository="owner/repository",
        pull_request_number=123,
    )

    assert comment_id is None
    assert call_count == 2

def test_creates_comment_when_no_existing_review_comment(
    monkeypatch,
    tmp_path,
):
    """
    Se ainda não existir comentário do AI reviewer,
    deve criar um novo comentário usando POST.
    """

    event_file = tmp_path / "event.json"

    event_file.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": 123,
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "GITHUB_REPOSITORY",
        "owner/repository",
    )

    monkeypatch.setenv(
        "GITHUB_EVENT_PATH",
        str(event_file),
    )

    monkeypatch.setattr(
        reviewer,
        "find_existing_review_comment",
        lambda **kwargs: None,
    )

    captured_request = {}

    def fake_urlopen(request, timeout):
        captured_request["method"] = request.get_method()
        captured_request["url"] = request.full_url
        captured_request["body"] = json.loads(
            request.data.decode("utf-8")
        )

        return FakeResponse(
            data=[],
            status=201,
        )

    monkeypatch.setattr(
        reviewer.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    reviewer.publish_pull_request_review(
        github_token="fake-token",
        review="# AI Data Engineering Review",
    )

    assert captured_request["method"] == "POST"

    assert captured_request["url"] == (
        "https://api.github.com/repos/owner/repository"
        "/issues/123/comments"
    )

    assert (
        reviewer.REVIEW_MARKER
        in captured_request["body"]["body"]
    )

    assert (
        "# AI Data Engineering Review"
        in captured_request["body"]["body"]
    )

def test_updates_existing_review_comment(
    monkeypatch,
    tmp_path,
):
    """
    Se já existir comentário do AI reviewer,
    deve atualizar o mesmo comentário usando PATCH.
    """

    event_file = tmp_path / "event.json"

    event_file.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": 123,
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "GITHUB_REPOSITORY",
        "owner/repository",
    )

    monkeypatch.setenv(
        "GITHUB_EVENT_PATH",
        str(event_file),
    )

    monkeypatch.setattr(
        reviewer,
        "find_existing_review_comment",
        lambda **kwargs: 456,
    )

    captured_request = {}

    def fake_urlopen(request, timeout):
        captured_request["method"] = request.get_method()
        captured_request["url"] = request.full_url
        captured_request["body"] = json.loads(
            request.data.decode("utf-8")
        )

        return FakeResponse(
            data=[],
            status=200,
        )

    monkeypatch.setattr(
        reviewer.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    reviewer.publish_pull_request_review(
        github_token="fake-token",
        review="# Updated AI Data Engineering Review",
    )

    assert captured_request["method"] == "PATCH"

    assert captured_request["url"] == (
        "https://api.github.com/repos/owner/repository"
        "/issues/comments/456"
    )

    assert (
        reviewer.REVIEW_MARKER
        in captured_request["body"]["body"]
    )

    assert (
        "# Updated AI Data Engineering Review"
        in captured_request["body"]["body"]
    )
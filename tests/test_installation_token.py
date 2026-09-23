from github_app.authentication import create_installation_access_token


class FakeResponse:
    """
    Simula apenas a parte da resposta HTTP necessária para o teste.
    """

    def __init__(self):
        self.status = 201

    def read(self) -> bytes:
        return (
            b'{'
            b'"token":"fake-installation-token",'
            b'"expires_at":"2026-09-22T18:00:00Z"'
            b'}'
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_creates_installation_access_token(monkeypatch):
    """
    Deve trocar o JWT do GitHub App por um token da instalação.

    Nenhuma chamada real ao GitHub é feita.
    """

    captured_request = {}

    def fake_urlopen(request, timeout):
        captured_request["url"] = request.full_url
        captured_request["method"] = request.get_method()
        captured_request["authorization"] = request.get_header(
            "Authorization"
        )
        captured_request["accept"] = request.get_header(
            "Accept"
        )
        captured_request["api_version"] = request.get_header(
            "X-github-api-version"
        )
        captured_request["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        "github_app.authentication.urlopen",
        fake_urlopen,
    )

    token = create_installation_access_token(
        app_jwt="fake-app-jwt",
        installation_id=123456789,
    )

    assert token == "fake-installation-token"

    assert captured_request["url"] == (
        "https://api.github.com/app/installations/"
        "123456789/access_tokens"
    )

    assert captured_request["method"] == "POST"
    assert captured_request["authorization"] == "Bearer fake-app-jwt"
    assert captured_request["accept"] == "application/vnd.github+json"
    assert captured_request["api_version"] == "2026-03-10"
    assert captured_request["timeout"] == 10
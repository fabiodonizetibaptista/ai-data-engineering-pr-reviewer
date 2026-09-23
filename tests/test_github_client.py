from github_app.github_client import get_pull_request_diff


class FakeResponse:
    """
    Resposta HTTP simulada para impedir chamadas reais ao GitHub.
    """

    def read(self) -> bytes:
        return (
            b"diff --git a/example.py b/example.py\n"
            b"--- a/example.py\n"
            b"+++ b/example.py\n"
            b"@@ -1 +1 @@\n"
            b"-old_value = 1\n"
            b"+new_value = 2\n"
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_gets_pull_request_diff(monkeypatch):
    """
    Deve buscar o diff do PR utilizando o token da instalação.
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
        "github_app.github_client.urlopen",
        fake_urlopen,
    )

    diff = get_pull_request_diff(
        installation_token="fake-installation-token",
        repository_full_name="fabiodonizetibaptista/example-repository",
        pull_request_number=42,
    )

    assert "diff --git a/example.py b/example.py" in diff
    assert "+new_value = 2" in diff

    assert captured_request["url"] == (
        "https://api.github.com/repos/"
        "fabiodonizetibaptista/example-repository/pulls/42"
    )

    assert captured_request["method"] == "GET"
    assert (
        captured_request["authorization"]
        == "Bearer fake-installation-token"
    )
    assert captured_request["accept"] == "application/vnd.github.diff"
    assert captured_request["api_version"] == "2026-03-10"
    assert captured_request["timeout"] == 15


def test_rejects_invalid_repository_full_name():
    """
    O repositório deve obrigatoriamente estar no formato owner/repository.
    """

    try:
        get_pull_request_diff(
            installation_token="fake-token",
            repository_full_name="invalid-repository-name",
            pull_request_number=42,
        )
    except ValueError as exc:
        assert str(exc) == (
            "repository_full_name must use the format 'owner/repository'."
        )
    else:
        raise AssertionError("ValueError was not raised.")
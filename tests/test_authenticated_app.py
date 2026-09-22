from github_app.authentication import (
    get_authenticated_app_slug,
)


class FakeResponse:
    def read(self) -> bytes:
        return b'{"id":123,"slug":"ai-data-engineering-pr-reviewer"}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_gets_authenticated_app_slug(monkeypatch):

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["authorization"] = request.get_header(
            "Authorization"
        )

        return FakeResponse()

    monkeypatch.setattr(
        "github_app.authentication.urlopen",
        fake_urlopen,
    )

    slug = get_authenticated_app_slug(
        app_jwt="fake-app-jwt",
    )

    assert slug == "ai-data-engineering-pr-reviewer"
    assert captured["url"] == "https://api.github.com/app"
    assert captured["method"] == "GET"
    assert captured["authorization"] == "Bearer fake-app-jwt"
from github_app.authentication import GitHubAppCredentials
from github_app.events import PullRequestEvent
from github_app.processor import process_pull_request_event


def test_processes_pull_request_and_publishes_review(
    monkeypatch,
    tmp_path,
):

    rules_path = tmp_path / "data-engineering.md"
    rules_path.write_text(
        "Data Engineering rules for test.",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "github_app.processor.RULES_PATH",
        rules_path,
    )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "fake-gemini-key",
    )

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "fake-groq-key",
    )

    monkeypatch.setattr(
        "github_app.processor.time.time",
        lambda: 1_800_000_000,
    )

    monkeypatch.setattr(
        "github_app.processor.load_github_app_credentials",
        lambda: GitHubAppCredentials(
            app_id="123456",
            private_key=b"fake-private-key",
        ),
    )

    monkeypatch.setattr(
        "github_app.processor.generate_app_jwt",
        lambda **kwargs: "fake-app-jwt",
    )

    monkeypatch.setattr(
        "github_app.processor.get_authenticated_app_slug",
        lambda **kwargs: "ai-reviewer",
    )

    monkeypatch.setattr(
        "github_app.processor.create_installation_access_token",
        lambda **kwargs: "fake-installation-token",
    )

    monkeypatch.setattr(
        "github_app.processor.get_pull_request_diff",
        lambda **kwargs: "fake pull request diff",
    )

    monkeypatch.setattr(
        "github_app.processor.generate_review",
        lambda **kwargs: "Generated AI review",
    )

    captured = {}

    def fake_publish_or_update_pull_request_comment(
        installation_token,
        repository_full_name,
        pull_request_number,
        review,
        bot_login,
    ):
        captured["installation_token"] = installation_token
        captured["repository"] = repository_full_name
        captured["pr"] = pull_request_number
        captured["review"] = review
        captured["bot_login"] = bot_login

        return 987654321

    monkeypatch.setattr(
        "github_app.processor.publish_or_update_pull_request_comment",
        fake_publish_or_update_pull_request_comment,
    )

    event = PullRequestEvent(
        action="synchronize",
        pull_request_number=42,
        repository_full_name="owner/repository",
        installation_id=123456789,
    )

    result = process_pull_request_event(
        event
    )

    assert result is True
    assert captured["installation_token"] == "fake-installation-token"
    assert captured["repository"] == "owner/repository"
    assert captured["pr"] == 42
    assert captured["review"] == "Generated AI review"
    assert captured["bot_login"] == "ai-reviewer[bot]"
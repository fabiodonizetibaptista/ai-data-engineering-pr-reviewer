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

from github_app.processor import (
    MAX_REVIEW_DIFF_BYTES,
    TRUNCATION_NOTICE,
    limit_diff_for_review,
)


def test_keeps_small_diff_unchanged():
    diff = "small diff"

    result = limit_diff_for_review(diff)

    assert result == diff


def test_truncates_large_diff_before_ai_review():
    diff = "x" * (MAX_REVIEW_DIFF_BYTES + 10_000)

    result = limit_diff_for_review(diff)

    assert len(
        result.replace(
            TRUNCATION_NOTICE,
            "",
        ).encode("utf-8")
    ) <= MAX_REVIEW_DIFF_BYTES

    assert TRUNCATION_NOTICE in result
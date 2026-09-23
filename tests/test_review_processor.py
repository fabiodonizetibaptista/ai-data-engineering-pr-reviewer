from github_app.authentication import GitHubAppCredentials
from github_app.diff_chunking import DiffChunkPlan
from github_app.events import PullRequestEvent
from github_app.processor import process_pull_request_event
from providers.base import AIProviderUnavailableError


def configure_common_mocks(
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
        lambda **kwargs: "complete fake diff",
    )


def test_processes_all_diff_chunks_and_publishes_review(
    monkeypatch,
    tmp_path,
):
    configure_common_mocks(
        monkeypatch,
        tmp_path,
    )

    plan = DiffChunkPlan(
        chunks=(
            "chunk one",
            "chunk two",
        ),
        total_chunks=2,
        omitted_chunks=0,
        omitted_bytes=0,
    )

    monkeypatch.setattr(
        "github_app.processor.chunk_pull_request_diff",
        lambda diff: plan,
    )

    reviewed_chunks = []

    def fake_generate_review(
        gemini_api_key,
        groq_api_key,
        rules,
        diff,
    ):
        reviewed_chunks.append(
            diff
        )

        return (
            "# AI Data Engineering Review\n\n"
            f"Review for {diff}"
        )

    monkeypatch.setattr(
        "github_app.processor.generate_review",
        fake_generate_review,
    )

    captured = {}

    def fake_publish_or_update_pull_request_comment(
        installation_token,
        repository_full_name,
        pull_request_number,
        review,
        bot_login,
    ):
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

    assert reviewed_chunks == [
        "chunk one",
        "chunk two",
    ]

    assert "Review for chunk one" in captured["review"]
    assert "Review for chunk two" in captured["review"]
    assert "Partial Review 1 of 2" in captured["review"]
    assert "Partial Review 2 of 2" in captured["review"]
    assert captured["bot_login"] == "ai-reviewer[bot]"


def test_does_not_publish_when_ai_providers_are_unavailable(
    monkeypatch,
    tmp_path,
):
    configure_common_mocks(
        monkeypatch,
        tmp_path,
    )

    plan = DiffChunkPlan(
        chunks=("chunk one",),
        total_chunks=1,
        omitted_chunks=0,
        omitted_bytes=0,
    )

    monkeypatch.setattr(
        "github_app.processor.chunk_pull_request_diff",
        lambda diff: plan,
    )

    def unavailable_provider(**kwargs):
        raise AIProviderUnavailableError(
            "Providers unavailable."
        )

    monkeypatch.setattr(
        "github_app.processor.generate_review",
        unavailable_provider,
    )

    published = {
        "value": False,
    }

    def fake_publish(**kwargs):
        published["value"] = True
        return 123

    monkeypatch.setattr(
        "github_app.processor.publish_or_update_pull_request_comment",
        fake_publish,
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

    assert result is False
    assert published["value"] is False
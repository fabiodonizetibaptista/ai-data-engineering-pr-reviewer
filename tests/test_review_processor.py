import pytest

from github_app.authentication import GitHubAppCredentials
from github_app.diff_chunking import DiffChunkPlan
from github_app.events import PullRequestEvent
from github_app.processor import process_pull_request_event
from github_app.review_result import ReviewResult
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

    monkeypatch.setenv(
        "OPENROUTER_API_KEY",
        "fake-openrouter-key",
    )

    monkeypatch.setenv(
        "OPENROUTER_MODEL",
        "openrouter/free",
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
        openrouter_api_key=None,
        openrouter_model=None,
        unavailable_providers=None,
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

    assert result == ReviewResult("complete", True, 2, 2, "none")

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

    assert result == ReviewResult("failed", False, 0, 1, "providers_unavailable")
    assert published["value"] is False

def test_publishes_explicit_partial_review_after_provider_failure(monkeypatch, tmp_path):
    configure_common_mocks(monkeypatch, tmp_path)
    plan = DiffChunkPlan(
        chunks=("one", "two", "three"),
        total_chunks=3, omitted_chunks=0, omitted_bytes=0,
    )
    monkeypatch.setattr(
        "github_app.processor.chunk_pull_request_diff", lambda diff: plan,
    )
    calls = []
    def fake_review(**kwargs):
        calls.append(kwargs["diff"])
        if len(calls) == 2:
            raise AIProviderUnavailableError("unavailable")
        return "# AI Data Engineering Review\n\nFirst chunk review"
    monkeypatch.setattr("github_app.processor.generate_review", fake_review)
    published = []
    monkeypatch.setattr(
        "github_app.processor.publish_or_update_pull_request_comment",
        lambda **kwargs: published.append(kwargs["review"]),
    )
    event = PullRequestEvent(
        action="synchronize", pull_request_number=4,
        repository_full_name="owner/repo", installation_id=123,
    )
    assert process_pull_request_event(event) == ReviewResult("partial", True, 1, 3, "providers_unavailable")
    assert calls == ["one", "two"]
    assert len(published) == 1
    assert "INCOMPLETE REVIEW" in published[0]
    assert "1 of 3" in published[0]




@pytest.mark.parametrize(
    ("completed", "total", "omitted", "reason"),
    [
        (8, 22, 14, "chunk_limit"),
        (5, 22, 14, "time_budget_exceeded"),
    ],
)
def test_classifies_chunk_limit_and_time_budget(
    monkeypatch, tmp_path, completed, total, omitted, reason
):
    from github_app import processor

    configure_common_mocks(monkeypatch, tmp_path)

    plan = DiffChunkPlan(
        chunks=tuple(f"chunk-{i}" for i in range(1, 9)),
        total_chunks=total,
        omitted_chunks=omitted,
        omitted_bytes=1000,
    )
    monkeypatch.setattr(processor, "chunk_pull_request_diff", lambda diff: plan)

    calls = []
    monkeypatch.setattr(
        processor,
        "generate_review",
        lambda **kwargs: calls.append(kwargs["diff"]) or "Valid review",
    )
    monkeypatch.setattr(
        processor,
        "publish_or_update_pull_request_comment",
        lambda **kwargs: 123,
    )

    if reason == "time_budget_exceeded":
        ticks = iter([0.0] + [0.0] * completed + [181.0])
        monkeypatch.setattr(
            processor.time, "monotonic", lambda: next(ticks, 181.0)
        )

    event = PullRequestEvent(
        action="synchronize",
        pull_request_number=4,
        repository_full_name="owner/repo",
        installation_id=123,
    )
    outcome = processor.process_pull_request_event(event)

    assert outcome.status == "partial"
    assert outcome.published is True
    assert outcome.completed_chunks == completed
    assert outcome.total_chunks == total
    assert outcome.reason == reason
    assert len(calls) == completed

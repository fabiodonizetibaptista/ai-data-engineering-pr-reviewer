import logging

from github_app.background import (
    run_pull_request_review_safely,
)
from github_app.events import PullRequestEvent
from github_app.review_result import ReviewResult


def build_event() -> PullRequestEvent:
    return PullRequestEvent(
        action="synchronize",
        pull_request_number=42,
        repository_full_name="owner/repository",
        installation_id=123456789,
    )


def test_background_processing_completes_successfully(
    monkeypatch,
    caplog,
):
    monkeypatch.setattr(
        "github_app.background.process_pull_request_event",
        lambda event: ReviewResult("complete", True, 1, 1, "none"),
    )

    with caplog.at_level(logging.INFO):
        result = run_pull_request_review_safely(
            build_event()
        )

    assert result is None

    assert (
        "review.finished status=complete"
        in caplog.text
    )


def test_background_processing_handles_provider_unavailability(
    monkeypatch,
    caplog,
):
    monkeypatch.setattr(
        "github_app.background.process_pull_request_event",
        lambda event: ReviewResult("failed", False, 0, 1, "providers_unavailable"),
    )

    with caplog.at_level(logging.WARNING):
        result = run_pull_request_review_safely(
            build_event()
        )

    assert result is None

    assert (
        "review.finished status=failed"
        in caplog.text
    )


def test_background_processing_swallows_unexpected_exception(
    monkeypatch,
    caplog,
):
    def fail(event):
        raise RuntimeError(
            "SECRET_VALUE_THAT_MUST_NOT_BE_LOGGED"
        )

    monkeypatch.setattr(
        "github_app.background.process_pull_request_event",
        fail,
    )

    with caplog.at_level(logging.ERROR):
        result = run_pull_request_review_safely(
            build_event()
        )

    assert result is None

    assert (
        "error_type=RuntimeError"
        in caplog.text
    )


def test_background_processing_does_not_log_exception_message(
    monkeypatch,
    caplog,
):
    sensitive_value = (
        "SECRET_VALUE_THAT_MUST_NOT_BE_LOGGED"
    )

    def fail(event):
        raise RuntimeError(
            sensitive_value
        )

    monkeypatch.setattr(
        "github_app.background.process_pull_request_event",
        fail,
    )

    with caplog.at_level(logging.ERROR):
        run_pull_request_review_safely(
            build_event()
        )

    assert sensitive_value not in caplog.text
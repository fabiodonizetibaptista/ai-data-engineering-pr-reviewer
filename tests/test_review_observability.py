import logging
from unittest.mock import Mock

import pytest

from github_app import background
from github_app.review_result import ReviewResult


@pytest.mark.parametrize(
    ("processor_result", "expected_status"),
    [
        (ReviewResult("complete", True, 2, 2, "none"), "status=complete"),
        (ReviewResult("partial", True, 1, 2, "time_budget_exceeded"), "status=partial"),
        (ReviewResult("failed", False, 0, 2, "providers_unavailable"), "status=failed"),
    ],
)
def test_review_lifecycle_result_logging(
    monkeypatch, caplog, processor_result, expected_status
):
    event = Mock()
    event.repository_full_name = "example/safe-repo"
    event.pull_request_number = 123

    monkeypatch.setattr(
        background,
        "process_pull_request_event",
        lambda _event: processor_result,
    )

    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        background.run_pull_request_review_safely(event)

    messages = [record.getMessage() for record in caplog.records]

    assert any("review.started" in msg for msg in messages)
    assert any(expected_status in msg for msg in messages)
    assert any("pr=123" in msg for msg in messages)


def test_review_lifecycle_exception_logging(monkeypatch, caplog):
    event = Mock()
    event.repository_full_name = "example/safe-repo"
    event.pull_request_number = 456

    def failing_processor(_event):
        raise RuntimeError("simulated-secret-must-not-appear")

    monkeypatch.setattr(
        background,
        "process_pull_request_event",
        failing_processor,
    )

    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        background.run_pull_request_review_safely(event)

    messages = [record.getMessage() for record in caplog.records]

    assert any("review.started" in msg for msg in messages)
    assert any("status=error" in msg for msg in messages)
    assert any("error_type=RuntimeError" in msg for msg in messages)
    assert all(
        "simulated-secret-must-not-appear" not in msg
        for msg in messages
    )

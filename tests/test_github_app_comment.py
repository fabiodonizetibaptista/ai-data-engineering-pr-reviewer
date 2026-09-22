import json

from github_app.github_client import (
    REVIEW_MARKER,
    find_existing_review_comment,
    publish_or_update_pull_request_comment,
)


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def read(self) -> bytes:
        return json.dumps(
            self.body
        ).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_finds_existing_review_comment(monkeypatch):

    comments = [
        {
            "id": 111,
            "body": REVIEW_MARKER + "\n\nOld review",
            "user": {
                "login": "ai-reviewer[bot]",
            },
        }
    ]

    monkeypatch.setattr(
        "github_app.github_client.urlopen",
        lambda request, timeout: FakeResponse(comments),
    )

    comment_id = find_existing_review_comment(
        installation_token="fake-token",
        repository_full_name="owner/repository",
        pull_request_number=42,
        bot_login="ai-reviewer[bot]",
    )

    assert comment_id == 111


def test_ignores_marker_from_another_author(monkeypatch):

    comments = [
        {
            "id": 222,
            "body": REVIEW_MARKER + "\n\nSpoofed review",
            "user": {
                "login": "another-user",
            },
        }
    ]

    monkeypatch.setattr(
        "github_app.github_client.urlopen",
        lambda request, timeout: FakeResponse(comments),
    )

    comment_id = find_existing_review_comment(
        installation_token="fake-token",
        repository_full_name="owner/repository",
        pull_request_number=42,
        bot_login="ai-reviewer[bot]",
    )

    assert comment_id is None


def test_creates_comment_when_none_exists(monkeypatch):

    captured = {}
    responses = [
        FakeResponse([]),
        FakeResponse({"id": 333}),
    ]

    def fake_urlopen(request, timeout):
        captured.setdefault(
            "requests",
            [],
        ).append(request)

        return responses.pop(0)

    monkeypatch.setattr(
        "github_app.github_client.urlopen",
        fake_urlopen,
    )

    comment_id = publish_or_update_pull_request_comment(
        installation_token="fake-token",
        repository_full_name="owner/repository",
        pull_request_number=42,
        review="New review",
        bot_login="ai-reviewer[bot]",
    )

    assert comment_id == 333

    publish_request = captured["requests"][1]

    assert publish_request.get_method() == "POST"

    body = json.loads(
        publish_request.data.decode("utf-8")
    )

    assert body["body"] == (
        f"{REVIEW_MARKER}\n\nNew review"
    )


def test_updates_existing_comment(monkeypatch):

    captured = {}

    existing_comments = [
        {
            "id": 444,
            "body": REVIEW_MARKER + "\n\nOld review",
            "user": {
                "login": "ai-reviewer[bot]",
            },
        }
    ]

    responses = [
        FakeResponse(existing_comments),
        FakeResponse({"id": 444}),
    ]

    def fake_urlopen(request, timeout):
        captured.setdefault(
            "requests",
            [],
        ).append(request)

        return responses.pop(0)

    monkeypatch.setattr(
        "github_app.github_client.urlopen",
        fake_urlopen,
    )

    comment_id = publish_or_update_pull_request_comment(
        installation_token="fake-token",
        repository_full_name="owner/repository",
        pull_request_number=42,
        review="Updated review",
        bot_login="ai-reviewer[bot]",
    )

    assert comment_id == 444

    update_request = captured["requests"][1]

    assert update_request.get_method() == "PATCH"

    assert update_request.full_url.endswith(
        "/issues/comments/444"
    )

    body = json.loads(
        update_request.data.decode("utf-8")
    )

    assert body["body"] == (
        f"{REVIEW_MARKER}\n\nUpdated review"
    )
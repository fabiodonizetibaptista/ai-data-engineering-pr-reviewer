from github_app.diff_chunking import (
    chunk_pull_request_diff,
)


def test_keeps_small_diff_in_single_chunk():
    diff = (
        "diff --git a/example.py b/example.py\n"
        "-old\n"
        "+new\n"
    )

    plan = chunk_pull_request_diff(
        diff,
        max_chunk_bytes=1_000,
    )

    assert plan.chunks == (diff,)
    assert plan.total_chunks == 1
    assert plan.is_partial is False


def test_preserves_all_content_across_chunks():
    diff = (
        "diff --git a/a.py b/a.py\n"
        + ("a" * 100)
        + "\n"
        "diff --git a/b.py b/b.py\n"
        + ("b" * 100)
        + "\n"
    )

    plan = chunk_pull_request_diff(
        diff,
        max_chunk_bytes=150,
        max_chunks=10,
    )

    reconstructed = "".join(
        plan.chunks
    )

    assert reconstructed == diff
    assert len(plan.chunks) > 1
    assert plan.is_partial is False


def test_never_exceeds_chunk_byte_budget():
    diff = (
        "diff --git a/large.py b/large.py\n"
        + ("á" * 10_000)
    )

    plan = chunk_pull_request_diff(
        diff,
        max_chunk_bytes=1_000,
        max_chunks=100,
    )

    assert all(
        len(chunk.encode("utf-8")) <= 1_000
        for chunk in plan.chunks
    )


def test_marks_review_as_partial_when_chunk_limit_is_reached():
    diff = (
        "diff --git a/a.py b/a.py\n"
        + ("a" * 500)
        + "\n"
        "diff --git a/b.py b/b.py\n"
        + ("b" * 500)
        + "\n"
        "diff --git a/c.py b/c.py\n"
        + ("c" * 500)
    )

    plan = chunk_pull_request_diff(
        diff,
        max_chunk_bytes=300,
        max_chunks=2,
    )

    assert len(plan.chunks) == 2
    assert plan.total_chunks > 2
    assert plan.omitted_chunks > 0
    assert plan.omitted_bytes > 0
    assert plan.is_partial is True
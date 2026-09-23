from github_app.events import parse_pull_request_event


def test_parses_required_pull_request_metadata():
    """
    Deve extrair somente os metadados necessários para processar o PR.
    """

    payload = {
        "action": "synchronize",
        "number": 42,
        "repository": {
            "full_name": "fabiodonizetibaptista/example-repository",
        },
        "installation": {
            "id": 123456789,
        },
    }

    event = parse_pull_request_event(payload)

    assert event.action == "synchronize"
    assert event.pull_request_number == 42
    assert event.repository_full_name == (
        "fabiodonizetibaptista/example-repository"
    )
    assert event.installation_id == 123456789
import base64

from github_app.authentication import (
    load_github_app_credentials,
)


def test_loads_github_app_credentials_from_environment(
    monkeypatch,
    tmp_path,
):
    """
    Desenvolvimento local pode utilizar arquivo PEM.
    """

    private_key_path = (
        tmp_path
        / "github-app-private-key.pem"
    )

    private_key_path.write_bytes(
        b"fake-private-key-for-test"
    )

    monkeypatch.delenv(
        "GITHUB_APP_PRIVATE_KEY_B64",
        raising=False,
    )

    monkeypatch.setenv(
        "GITHUB_APP_ID",
        "123456",
    )

    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_PATH",
        str(private_key_path),
    )

    credentials = load_github_app_credentials()

    assert credentials.app_id == "123456"

    assert credentials.private_key == (
        b"fake-private-key-for-test"
    )


def test_loads_private_key_from_base64_environment(
    monkeypatch,
):
    """
    Produção pode receber a chave como Secret Base64,
    sem depender de arquivo local.
    """

    private_key = (
        b"fake-private-key-for-production"
    )

    encoded_key = base64.b64encode(
        private_key
    ).decode("ascii")

    monkeypatch.setenv(
        "GITHUB_APP_ID",
        "123456",
    )

    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_B64",
        encoded_key,
    )

    monkeypatch.delenv(
        "GITHUB_APP_PRIVATE_KEY_PATH",
        raising=False,
    )

    credentials = load_github_app_credentials()

    assert credentials.app_id == "123456"
    assert credentials.private_key == private_key


def test_base64_private_key_has_precedence_over_local_path(
    monkeypatch,
    tmp_path,
):
    """
    Quando os dois modos estiverem presentes,
    o Secret de produção deve prevalecer.
    """

    production_key = b"production-key"

    encoded_key = base64.b64encode(
        production_key
    ).decode("ascii")

    local_path = tmp_path / "local.pem"

    local_path.write_bytes(
        b"local-key"
    )

    monkeypatch.setenv(
        "GITHUB_APP_ID",
        "123456",
    )

    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_B64",
        encoded_key,
    )

    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_PATH",
        str(local_path),
    )

    credentials = load_github_app_credentials()

    assert credentials.private_key == production_key
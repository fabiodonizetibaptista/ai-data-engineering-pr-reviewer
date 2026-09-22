from github_app.authentication import load_github_app_credentials


def test_loads_github_app_credentials_from_environment(
    monkeypatch,
    tmp_path,
):
    """
    Deve carregar o App ID e a chave privada usando
    as configurações do ambiente.

    O teste utiliza um arquivo temporário e nunca acessa
    a chave privada real do GitHub App.
    """

    private_key_path = tmp_path / "github-app-private-key.pem"
    private_key_path.write_bytes(b"fake-private-key-for-test")

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
    assert credentials.private_key == b"fake-private-key-for-test"
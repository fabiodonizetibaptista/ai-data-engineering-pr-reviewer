import jwt

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from github_app.authentication import generate_app_jwt


def test_generates_valid_github_app_jwt():
    """
    Deve gerar um JWT RS256 contendo as claims exigidas
    para autenticação de um GitHub App.

    A chave RSA usada aqui é criada apenas para o teste.
    A chave privada real do GitHub App nunca é utilizada.
    """

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    app_id = "123456"
    current_time = 1_800_000_000

    token = generate_app_jwt(
        app_id=app_id,
        private_key=private_key_pem,
        current_time=current_time,
    )

    header = jwt.get_unverified_header(token)

    claims = jwt.decode(
        token,
        public_key_pem,
        algorithms=["RS256"],
        options={
            "verify_exp": False,
            "verify_iat": False,
        },
    )

    assert header["alg"] == "RS256"
    assert claims["iss"] == app_id
    assert claims["iat"] == current_time - 60
    assert claims["exp"] == current_time + 600
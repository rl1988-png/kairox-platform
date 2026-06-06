from kairox_api.core.password import hash_password, verify_password
from kairox_api.core.security import create_access_token, decode_token


def test_password_hash_and_verify() -> None:
    hashed = hash_password("KairoxTest2026")
    assert verify_password("KairoxTest2026", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip() -> None:
    token, _expires = create_access_token("00000000-0000-0000-0000-000000000001")
    payload = decode_token(token, "access")
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["type"] == "access"

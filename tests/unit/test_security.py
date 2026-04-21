import pytest

from app.utils.security import generate_session_token, hash_session_token, verify_session_token


def test_token_is_string():
    token = generate_session_token()
    assert isinstance(token, str)


def test_token_minimum_length():
    token = generate_session_token()
    assert len(token) >= 48


def test_tokens_are_unique():
    t1 = generate_session_token()
    t2 = generate_session_token()
    assert t1 != t2


def test_hash_returns_tuple_of_strings():
    token = generate_session_token()
    hashed, salt = hash_session_token(token)
    assert isinstance(hashed, str)
    assert isinstance(salt, str)


def test_hash_is_64_bytes_hex():
    _, _ = hash_session_token("test")
    hashed, _ = hash_session_token("test")
    assert len(hashed) == 128  # 64 bytes → 128 hex chars


def test_salt_is_32_bytes_hex():
    _, salt = hash_session_token("test")
    assert len(salt) == 64  # 32 bytes → 64 hex chars


def test_same_input_produces_different_salts():
    token = "same_input"
    _, s1 = hash_session_token(token)
    _, s2 = hash_session_token(token)
    assert s1 != s2


def test_same_input_produces_different_hashes():
    token = "same_input"
    h1, _ = hash_session_token(token)
    h2, _ = hash_session_token(token)
    assert h1 != h2


def test_verify_correct_token_returns_true():
    raw = generate_session_token()
    hashed, salt = hash_session_token(raw)
    assert verify_session_token(raw, hashed, salt) is True


def test_verify_wrong_token_returns_false():
    raw = generate_session_token()
    hashed, salt = hash_session_token(raw)
    assert verify_session_token("wrong_token_xyz", hashed, salt) is False


def test_verify_tampered_hash_returns_false():
    raw = generate_session_token()
    hashed, salt = hash_session_token(raw)
    tampered = hashed[:-4] + "0000"
    assert verify_session_token(raw, tampered, salt) is False


def test_verify_wrong_salt_returns_false():
    raw = generate_session_token()
    hashed, salt = hash_session_token(raw)
    _, other_salt = hash_session_token("other")
    assert verify_session_token(raw, hashed, other_salt) is False

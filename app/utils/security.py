import hashlib
import hmac
import os
import secrets


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(raw_token: str) -> tuple[str, str]:
    salt = os.urandom(32)
    salt_hex = salt.hex()
    hashed = hashlib.pbkdf2_hmac("sha512", raw_token.encode(), salt, 100_000, dklen=64)
    return hashed.hex(), salt_hex


def verify_session_token(raw_token: str, stored_hash: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac("sha512", raw_token.encode(), salt, 100_000, dklen=64)
    return hmac.compare_digest(hashed.hex(), stored_hash)

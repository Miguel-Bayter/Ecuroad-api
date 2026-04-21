import hashlib
import re
from app.core.exceptions import SSRFBlockedError, IntegrityCheckError

ALLOWED_ETL_DOMAINS = {
    "snies.mineducacion.gov.co",
    "ole.mineducacion.gov.co",
    "dane.gov.co",
    "spadies3.mineducacion.gov.co",
}

PRIVATE_IP_PATTERN = re.compile(
    r"^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.|0\.|::1$|localhost$)",
    re.IGNORECASE,
)


class ETLIntegrity:
    @staticmethod
    def validate_url(url: str) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if hostname not in ALLOWED_ETL_DOMAINS:
            raise SSRFBlockedError(f"Domain not in allowlist: {hostname}")
        if PRIVATE_IP_PATTERN.match(hostname):
            raise SSRFBlockedError(f"Private/loopback address blocked: {hostname}")
        return url

    @staticmethod
    def check_hash(data: bytes, expected: str | None = None) -> str:
        actual = hashlib.sha256(data).hexdigest()
        if expected and not (actual == expected):
            raise IntegrityCheckError(
                f"SHA-256 mismatch. Expected: {expected}, Got: {actual}"
            )
        return actual

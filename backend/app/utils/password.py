from __future__ import annotations

from hashlib import pbkdf2_hmac, sha256
import hmac
from secrets import token_hex

try:  # pragma: no cover - depends on native cffi wheels in the runtime.
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
except ModuleNotFoundError:  # pragma: no cover - exercised in local Windows env without cffi backend.
    PasswordHasher = None
    VerifyMismatchError = Exception

from ..core.config import settings


password_hasher = PasswordHasher() if PasswordHasher else None
PBKDF2_ITERATIONS = 260_000


def _with_pepper(password: str) -> str:
    return sha256(f"{password}{settings.password_pepper}".encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    prepared = _with_pepper(password)
    if password_hasher:
        return password_hasher.hash(prepared)
    salt = token_hex(16)
    digest = pbkdf2_hmac("sha256", prepared.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    if password_hash.startswith("pbkdf2_sha256$"):
        _, iterations, salt, expected = password_hash.split("$", 3)
        prepared = _with_pepper(password).encode("utf-8")
        actual = pbkdf2_hmac("sha256", prepared, salt.encode("utf-8"), int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    if not password_hasher:
        return False
    try:
        return password_hasher.verify(password_hash, _with_pepper(password))
    except VerifyMismatchError:
        return False

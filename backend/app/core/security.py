"""
Password hashing, token creation and one-time code helpers.

bcrypt is used directly because passlib 1.7.4 is not compatible with
bcrypt 5.x (it crashes while detecting the bcrypt version).
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

JWT_ALGORITHM = "HS256"


def utcnow():
    return datetime.now(timezone.utc)


# ---------- Passwords ----------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# A real bcrypt hash that matches no password. Login compares against it when
# the email is unknown so both cases take a similar amount of time.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


# ---------- JWT tokens ----------

def create_jwt(subject: int, token_type: str, expires_in: timedelta, extra_claims=None) -> str:
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": utcnow(),
        "exp": utcnow() + expires_in,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str, expected_type: str):
    """Return the token payload, or None if the token is invalid, expired or of the wrong type."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def create_access_token(user_id: int) -> str:
    return create_jwt(user_id, "access", timedelta(minutes=settings.access_token_expire_minutes))


# ---------- Random tokens and one-time codes ----------

def generate_url_token() -> str:
    """Long random token for refresh cookies and invitation links."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Tokens are stored as SHA-256 hashes so a database leak does not expose them."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_numeric_code(length: int = 6) -> str:
    return f"{secrets.randbelow(10 ** length):0{length}d}"


def hash_code(code: str) -> str:
    """
    Short numeric codes have few possible values, so a plain hash could be
    brute-forced offline. HMAC with the server SECRET_KEY prevents that.
    """
    return hmac.new(settings.secret_key.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()


def codes_match(stored_hash: str, submitted_code: str) -> bool:
    return hmac.compare_digest(stored_hash, hash_code(submitted_code))

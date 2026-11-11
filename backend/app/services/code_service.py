"""
Six-digit one-time codes for email verification and password reset.

Rules:
- codes are generated with the `secrets` module and stored as HMAC hashes
- each code expires after CODE_LIFETIME_MINUTES
- each code allows MAX_ATTEMPTS wrong guesses, then it is locked
- a new code replaces any older unused code
- a code can be used only once
- users can request a new code at most once per RESEND_COOLDOWN_SECONDS
  and at most MAX_CODES_PER_HOUR times per hour
"""
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import codes_match, generate_numeric_code, hash_code, utcnow
from app.models import AuthCode, User

CODE_LIFETIME_MINUTES = 10
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
MAX_CODES_PER_HOUR = 5


def issue_code(db: Session, user: User, purpose: str) -> str:
    """Create a new code for the user and return it in plain text (only to be emailed)."""
    now = utcnow()
    recent_codes = (
        db.query(AuthCode)
        .filter(AuthCode.user_id == user.id, AuthCode.purpose == purpose, AuthCode.created_at >= now - timedelta(hours=1))
        .order_by(AuthCode.created_at.desc())
        .all()
    )

    if recent_codes:
        seconds_since_last = (now - recent_codes[0].created_at).total_seconds()
        if seconds_since_last < RESEND_COOLDOWN_SECONDS:
            wait = int(RESEND_COOLDOWN_SECONDS - seconds_since_last) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait} seconds before requesting a new code.",
            )
    if len(recent_codes) >= MAX_CODES_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many codes have been requested. Please try again in an hour.",
        )

    # Older unused codes stop working as soon as a new one is issued
    db.query(AuthCode).filter(
        AuthCode.user_id == user.id, AuthCode.purpose == purpose, AuthCode.used_at.is_(None)
    ).update({AuthCode.used_at: now}, synchronize_session=False)

    code = generate_numeric_code()
    db.add(AuthCode(
        user_id=user.id,
        purpose=purpose,
        code_hash=hash_code(code),
        expires_at=now + timedelta(minutes=CODE_LIFETIME_MINUTES),
    ))
    return code


def check_code(db: Session, user: User, purpose: str, submitted_code: str) -> AuthCode:
    """
    Validate a code without consuming it. Wrong guesses are counted and saved
    immediately. The caller sets `used_at` when the action succeeds.
    """
    record = (
        db.query(AuthCode)
        .filter(AuthCode.user_id == user.id, AuthCode.purpose == purpose, AuthCode.used_at.is_(None))
        .order_by(AuthCode.created_at.desc())
        .first()
    )

    def fail(message):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    if record is None:
        fail("This code is invalid or has already been used. Please request a new code.")
    if record.expires_at < utcnow():
        fail("This code has expired. Please request a new code.")
    if record.attempts >= MAX_ATTEMPTS:
        fail("Too many incorrect attempts. Please request a new code.")

    if not codes_match(record.code_hash, submitted_code.strip()):
        record.attempts += 1
        db.commit()
        remaining = MAX_ATTEMPTS - record.attempts
        if remaining <= 0:
            fail("Too many incorrect attempts. Please request a new code.")
        fail(f"Incorrect code. You have {remaining} attempt{'s' if remaining != 1 else ''} left.")

    return record

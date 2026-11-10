"""
Business logic for registration, login, sessions and password reset.
"""
import logging
from datetime import timedelta

from email_validator import EmailNotValidError, EmailUndeliverableError, validate_email
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.constants import CodePurpose, Role
from app.core.permissions import get_user_permissions
from app.core.rate_limit import failed_login_limiter
from app.core.security import (
    DUMMY_PASSWORD_HASH, create_access_token, create_jwt, decode_jwt, generate_url_token,
    hash_password, hash_token, utcnow, verify_password,
)
from app.models import AuthCode, RefreshToken, StudentProfile, User
from app.schemas.auth import AuthResponse, SessionUser, user_with_permissions
from app.services import code_service, email_templates
from app.services.audit_service import record_audit
from app.services.email_service import EmailDeliveryError, send_email

logger = logging.getLogger("zyntra.auth")

RESET_TOKEN_MINUTES = 10


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == normalize_email(email)).first()


def check_email_domain(email: str):
    """
    Check that the email's domain is set up to receive mail (DNS MX/A records).
    This cannot prove the mailbox exists; the verification code does that.
    """
    try:
        validate_email(email, check_deliverability=True)
    except EmailUndeliverableError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email domain does not appear to accept email. Please check the address.",
        )
    except EmailNotValidError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please enter a valid email address.")


def build_auth_response(db: Session, user: User, access_token: str) -> AuthResponse:
    session_user = user_with_permissions(SessionUser, user, get_user_permissions(db, user))
    return AuthResponse(access_token=access_token, user=session_user)


# ---------- Registration and email verification ----------

def _send_verification_code(db: Session, user: User):
    """Issue a code and email it. Rolls back the transaction if sending fails."""
    code = code_service.issue_code(db, user, CodePurpose.EMAIL_VERIFICATION)
    subject, html, text = email_templates.verification_email(
        user.full_name, code, code_service.CODE_LIFETIME_MINUTES
    )
    try:
        send_email(user.email, subject, html, text)
    except EmailDeliveryError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


def register_student(db: Session, full_name: str, email: str, password: str) -> User:
    email = normalize_email(email)
    check_email_domain(email)

    user = get_user_by_email(db, email)
    if user and (user.is_email_verified or user.role != Role.STUDENT):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please log in instead.",
        )

    if user:
        # Unverified account from an earlier attempt: update it and send a new code
        user.full_name = full_name
        user.password_hash = hash_password(password)
    else:
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=Role.STUDENT,
            is_active=True,
            is_email_verified=False,
        )
        db.add(user)
        db.flush()  # assigns user.id
        db.add(StudentProfile(user_id=user.id))
        record_audit(db, user, "account", "user.registered", f"New student registration: {email}", "user", user.id)

    _send_verification_code(db, user)
    db.commit()
    return user


def resend_verification_code(db: Session, email: str):
    user = get_user_by_email(db, email)
    if user is None or user.is_email_verified:
        return  # same response either way
    _send_verification_code(db, user)
    db.commit()


def verify_email(db: Session, email: str, code: str) -> User:
    user = get_user_by_email(db, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This code is invalid or has expired.")
    if user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This email is already verified. Please log in.")

    record = code_service.check_code(db, user, CodePurpose.EMAIL_VERIFICATION, code)
    now = utcnow()
    record.used_at = now
    user.is_email_verified = True
    user.email_verified_at = now
    record_audit(db, user, "account", "user.verified", f"Email verified: {user.email}", "user", user.id)
    db.commit()

    subject, html, text = email_templates.registration_confirmed_email(user.full_name, f"{settings.frontend_url}/login")
    try:
        send_email(user.email, subject, html, text)
    except EmailDeliveryError:
        # The account is already verified; a missing welcome email should not block the user
        logger.warning("Could not send registration confirmation email")
    return user


# ---------- Login and sessions ----------

def authenticate(db: Session, email: str, password: str) -> User:
    email = normalize_email(email)
    failed_login_limiter.check(email)

    user = get_user_by_email(db, email)
    password_ok = verify_password(password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if user is None or not password_ok:
        failed_login_limiter.record(email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact the ZYNTRA administrator.",
        )
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "email_not_verified", "message": "Please verify your email address before logging in."},
        )

    failed_login_limiter.reset(email)
    return user


def create_session(db: Session, user: User) -> tuple[str, str]:
    """Start a login session. Returns (access_token, raw_refresh_token)."""
    raw_refresh_token = generate_url_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh_token),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
    ))
    user.last_login_at = utcnow()
    db.commit()
    return create_access_token(user.id), raw_refresh_token


def rotate_session(db: Session, raw_refresh_token: str) -> tuple[User, str, str]:
    """
    Exchange a valid refresh token for a new access token and a new refresh
    token. The old refresh token is revoked so each one works only once.
    """
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has ended. Please log in again.")
    if not raw_refresh_token:
        raise invalid

    token = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(raw_refresh_token)).first()
    if token is None or token.revoked_at is not None or token.expires_at < utcnow():
        raise invalid

    user = db.get(User, token.user_id)
    if user is None or not user.is_active or not user.is_email_verified:
        raise invalid

    token.revoked_at = utcnow()
    access_token, new_raw_token = create_session(db, user)
    return user, access_token, new_raw_token


def revoke_session(db: Session, raw_refresh_token: str | None):
    if not raw_refresh_token:
        return
    token = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(raw_refresh_token)).first()
    if token and token.revoked_at is None:
        token.revoked_at = utcnow()
        db.commit()


def revoke_all_sessions(db: Session, user: User):
    """Log the user out everywhere (added to the current transaction)."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
    ).update({RefreshToken.revoked_at: utcnow()}, synchronize_session=False)


# ---------- Forgot password ----------

def request_password_reset(db: Session, email: str):
    """
    Always finishes silently so the response never reveals whether an
    account exists for this email.
    """
    user = get_user_by_email(db, email)
    if user is None or not user.is_active or not user.is_email_verified:
        return

    try:
        code = code_service.issue_code(db, user, CodePurpose.PASSWORD_RESET)
    except HTTPException:
        return  # cooldown reached; a recent code is still valid

    subject, html, text = email_templates.password_reset_email(
        user.full_name, code, code_service.CODE_LIFETIME_MINUTES
    )
    try:
        send_email(user.email, subject, html, text)
    except EmailDeliveryError:
        db.rollback()
        logger.warning("Could not send password reset email")
        return
    db.commit()


def verify_reset_code(db: Session, email: str, code: str) -> str:
    """Check the reset code and return a short-lived token that allows setting a new password."""
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This code is invalid or has expired.")

    record = code_service.check_code(db, user, CodePurpose.PASSWORD_RESET, code)
    return create_jwt(user.id, "password_reset", timedelta(minutes=RESET_TOKEN_MINUTES), {"code_id": record.id})


def reset_password(db: Session, reset_token: str, new_password: str):
    expired = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This reset link has expired or was already used. Please start again.",
    )
    payload = decode_jwt(reset_token, expected_type="password_reset")
    if payload is None:
        raise expired

    user = db.get(User, int(payload["sub"]))
    record = db.get(AuthCode, payload.get("code_id"))
    if user is None or record is None or record.user_id != user.id or record.used_at is not None:
        raise expired

    now = utcnow()
    record.used_at = now  # makes the code and the reset token single-use
    user.password_hash = hash_password(new_password)
    revoke_all_sessions(db, user)
    record_audit(db, user, "account", "password.reset", f"Password reset for {user.email}", "user", user.id)
    db.commit()

    subject, html, text = email_templates.password_changed_email(
        user.full_name, now.strftime("%d %B %Y at %H:%M UTC")
    )
    try:
        send_email(user.email, subject, html, text)
    except EmailDeliveryError:
        logger.warning("Could not send password changed email")


# ---------- Root admin (used by the create_root_admin.py command) ----------

def create_root_admin(db: Session, full_name: str, email: str, password: str) -> User:
    email = normalize_email(email)
    if get_user_by_email(db, email):
        raise ValueError("An account with this email already exists.")
    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role=Role.ROOT_ADMIN,
        is_active=True,
        is_email_verified=True,
        email_verified_at=utcnow(),
    )
    db.add(user)
    db.flush()
    record_audit(db, user, "account", "root_admin.created", f"Root admin created from command line: {email}", "user", user.id)
    db.commit()
    return user

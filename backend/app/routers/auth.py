from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from app.config import settings
from app.core.dependencies import get_current_user
from app.core.permissions import get_user_permissions
from app.core.rate_limit import auth_ip_limiter
from app.models import User
from app.schemas.auth import (
    AuthResponse, EmailRequest, LoginRequest, MessageResponse, RegisterRequest, ResetCodeRequest,
    ResetPasswordRequest, ResetTokenResponse, SessionUser, VerifyEmailRequest, user_with_permissions,
)
from app.services import auth_service
from app.services.audit_service import record_audit

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "zyntra_refresh"
REFRESH_COOKIE_PATH = "/api/auth"


def set_refresh_cookie(response: Response, raw_token: str):
    # HttpOnly: JavaScript cannot read the cookie. SameSite=Lax: other sites cannot send it with POST requests.
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def start_session_response(db: Session, user: User, response: Response) -> AuthResponse:
    access_token, raw_refresh_token = auth_service.create_session(db, user)
    set_refresh_cookie(response, raw_refresh_token)
    return auth_service.build_auth_response(db, user, access_token)


@router.post("/register", status_code=201, response_model=MessageResponse, dependencies=[Depends(auth_ip_limiter)])
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    auth_service.register_student(db, data.full_name, data.email, data.password)
    return {"message": "We sent a 6-digit verification code to your email address."}


@router.post("/verify-email", response_model=AuthResponse, dependencies=[Depends(auth_ip_limiter)])
def verify_email(data: VerifyEmailRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.verify_email(db, data.email, data.code)
    return start_session_response(db, user, response)


@router.post("/resend-verification", response_model=MessageResponse, dependencies=[Depends(auth_ip_limiter)])
def resend_verification(data: EmailRequest, db: Session = Depends(get_db)):
    auth_service.resend_verification_code(db, data.email)
    return {"message": "If this email has an unverified account, a new code has been sent."}


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(auth_ip_limiter)])
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, data.email, data.password)
    record_audit(db, user, "account", "user.login", f"{user.email} logged in", "user", user.id)
    return start_session_response(db, user, response)


@router.post("/refresh", response_model=AuthResponse, responses={204: {"description": "No session cookie"}})
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        # Visitor has never logged in (or logged out): nothing to refresh, not an error
        return Response(status_code=204)
    try:
        user, access_token, new_refresh_token = auth_service.rotate_session(db, raw_token)
    except HTTPException as error:
        failed = JSONResponse(status_code=error.status_code, content={"detail": error.detail})
        clear_refresh_cookie(failed)
        return failed
    set_refresh_cookie(response, new_refresh_token)
    return auth_service.build_auth_response(db, user, access_token)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    auth_service.revoke_session(db, request.cookies.get(REFRESH_COOKIE_NAME))
    clear_refresh_cookie(response)
    return {"message": "You have been logged out."}


@router.get("/me", response_model=SessionUser)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_with_permissions(SessionUser, user, get_user_permissions(db, user))


@router.post("/forgot-password", response_model=MessageResponse, dependencies=[Depends(auth_ip_limiter)])
def forgot_password(data: EmailRequest, db: Session = Depends(get_db)):
    auth_service.request_password_reset(db, data.email)
    return {"message": "If an account exists for this email, we have sent a password reset code."}


@router.post("/reset-password/verify-code", response_model=ResetTokenResponse, dependencies=[Depends(auth_ip_limiter)])
def verify_reset_code(data: ResetCodeRequest, db: Session = Depends(get_db)):
    return {"reset_token": auth_service.verify_reset_code(db, data.email, data.code)}


@router.post("/reset-password", response_model=MessageResponse, dependencies=[Depends(auth_ip_limiter)])
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(db, data.reset_token, data.password)
    return {"message": "Your password has been changed. Please log in with your new password."}

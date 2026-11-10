"""
FastAPI dependencies that identify the logged-in user and check their role.

The role is always loaded from the database. Nothing sent by the frontend
(other than the signed access token) is trusted.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from app.constants import Role
from app.core.security import decode_jwt
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    not_authenticated = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please log in to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise not_authenticated

    payload = decode_jwt(credentials.credentials, expected_type="access")
    if payload is None:
        raise not_authenticated

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise not_authenticated
    if not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email address first.")
    return user


def require_roles(*allowed_roles):
    """Create a dependency that only lets users with one of the given roles through."""
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this area.")
        return user
    return dependency


get_current_student = require_roles(Role.STUDENT)
get_current_root_admin = require_roles(Role.ROOT_ADMIN)
get_current_admin_user = require_roles(Role.ROOT_ADMIN, Role.STAFF)

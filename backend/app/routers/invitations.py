"""Public endpoints used by the staff invitation page (/invite/accept?token=...)."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from database import get_db
from app.core.rate_limit import auth_ip_limiter
from app.routers.auth import start_session_response
from app.schemas.auth import AcceptInvitationRequest, AuthResponse, InvitationPreview
from app.services import invitation_service

router = APIRouter(prefix="/api/invitations", tags=["Staff invitations"])


@router.get("/preview", response_model=InvitationPreview, dependencies=[Depends(auth_ip_limiter)])
def preview_invitation(token: str, db: Session = Depends(get_db)):
    invitation = invitation_service.get_valid_invitation(db, token)
    return InvitationPreview(
        full_name=invitation.full_name,
        email=invitation.email,
        expires_at=invitation.expires_at,
        permissions=invitation.permissions,
    )


@router.post("/accept", response_model=AuthResponse, dependencies=[Depends(auth_ip_limiter)])
def accept_invitation(data: AcceptInvitationRequest, response: Response, db: Session = Depends(get_db)):
    user = invitation_service.accept_invitation(db, data.token, data.password)
    return start_session_response(db, user, response)

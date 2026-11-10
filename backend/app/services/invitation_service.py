"""
Staff invitations.

Only the root admin can invite staff. The invitation link contains a random
token; the database stores only its hash. A link is valid for
INVITATION_LIFETIME_HOURS, works once, and stops working if revoked or
replaced by a newer invitation for the same email.
"""
import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.constants import ACCESS_LEVEL_LABELS, CONTENT_MODULES, AccessLevel, Role
from app.core.security import generate_url_token, hash_password, hash_token, utcnow
from app.models import StaffInvitation, StaffPermission, User
from app.services import email_templates
from app.services.audit_service import record_audit
from app.services.auth_service import get_user_by_email, normalize_email
from app.services.email_service import EmailDeliveryError, send_email

logger = logging.getLogger("zyntra.invitations")

INVITATION_LIFETIME_HOURS = 72


def validate_permissions(permissions: dict) -> dict:
    """Keep only known modules and levels; at least one module is required."""
    cleaned = {}
    for module, level in permissions.items():
        if module not in CONTENT_MODULES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown module: {module}")
        if level is None or level == "":
            continue
        if level not in AccessLevel.ALL:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown access level: {level}")
        cleaned[module] = level
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select access for at least one module.")
    return cleaned


def describe_permissions(permissions: dict) -> str:
    return ", ".join(
        f"{CONTENT_MODULES[module]} ({ACCESS_LEVEL_LABELS[level]})" for module, level in permissions.items()
    )


def _send_invitation_email(db: Session, invitation: StaffInvitation, raw_token: str, inviter: User):
    accept_url = f"{settings.frontend_url}/invite/accept?token={raw_token}"
    subject, html, text = email_templates.staff_invitation_email(
        invitation.full_name, inviter.full_name, accept_url, INVITATION_LIFETIME_HOURS,
        describe_permissions(invitation.permissions),
    )
    try:
        send_email(invitation.email, subject, html, text)
    except EmailDeliveryError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


def _revoke_pending_invitations(db: Session, email: str):
    db.query(StaffInvitation).filter(
        StaffInvitation.email == email,
        StaffInvitation.accepted_at.is_(None),
        StaffInvitation.revoked_at.is_(None),
    ).update({StaffInvitation.revoked_at: utcnow()}, synchronize_session=False)


def create_invitation(db: Session, inviter: User, full_name: str, email: str, permissions: dict) -> StaffInvitation:
    email = normalize_email(email)
    permissions = validate_permissions(permissions)
    if get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")

    _revoke_pending_invitations(db, email)

    raw_token = generate_url_token()
    invitation = StaffInvitation(
        full_name=full_name,
        email=email,
        token_hash=hash_token(raw_token),
        permissions=permissions,
        invited_by_id=inviter.id,
        expires_at=utcnow() + timedelta(hours=INVITATION_LIFETIME_HOURS),
    )
    db.add(invitation)
    db.flush()
    record_audit(db, inviter, "account", "staff.invited", f"Invited {email} as staff", "invitation", invitation.id)

    _send_invitation_email(db, invitation, raw_token, inviter)
    db.commit()
    return invitation


def resend_invitation(db: Session, inviter: User, invitation_id: int) -> StaffInvitation:
    """Replace an unaccepted invitation with a fresh link and expiry date."""
    old = db.get(StaffInvitation, invitation_id)
    if old is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")
    if old.accepted_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation was already accepted.")
    return create_invitation(db, inviter, old.full_name, old.email, old.permissions)


def revoke_invitation(db: Session, actor: User, invitation_id: int):
    invitation = db.get(StaffInvitation, invitation_id)
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")
    if invitation.accepted_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation was already accepted.")
    invitation.revoked_at = utcnow()
    record_audit(db, actor, "account", "invitation.revoked", f"Revoked invitation for {invitation.email}",
                 "invitation", invitation.id)
    db.commit()


def get_valid_invitation(db: Session, raw_token: str, lock: bool = False) -> StaffInvitation:
    query = db.query(StaffInvitation).filter(StaffInvitation.token_hash == hash_token(raw_token or ""))
    if lock:
        query = query.with_for_update()  # stops the same link being accepted twice at once
    invitation = query.first()

    if invitation is None or invitation.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This invitation link is invalid. Please ask the administrator for a new one.")
    if invitation.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This invitation has already been used. Please log in instead.")
    if invitation.expires_at < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This invitation has expired. Please ask the administrator to send a new one.")
    return invitation


def accept_invitation(db: Session, raw_token: str, password: str) -> User:
    invitation = get_valid_invitation(db, raw_token, lock=True)
    if get_user_by_email(db, invitation.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    now = utcnow()
    # Opening the emailed link proves the staff member controls this address
    user = User(
        full_name=invitation.full_name,
        email=invitation.email,
        password_hash=hash_password(password),
        role=Role.STAFF,
        is_active=True,
        is_email_verified=True,
        email_verified_at=now,
    )
    db.add(user)
    db.flush()
    for module, level in invitation.permissions.items():
        db.add(StaffPermission(user_id=user.id, module=module, access_level=level))

    invitation.accepted_at = now
    invitation.accepted_user_id = user.id
    record_audit(db, user, "account", "invitation.accepted", f"{user.email} accepted a staff invitation", "user", user.id)
    db.commit()

    subject, html, text = email_templates.staff_welcome_email(user.full_name, f"{settings.frontend_url}/login")
    try:
        send_email(user.email, subject, html, text)
    except EmailDeliveryError:
        logger.warning("Could not send staff welcome email")
    return user

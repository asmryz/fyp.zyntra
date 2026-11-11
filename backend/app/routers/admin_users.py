"""
Dashboard overview, user management, staff permissions, invitations and the
activity log. Everything except the overview is restricted to the root admin.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from app.constants import CONTENT_MODULES, SEARCH_MAX, Role, Status
from app.core.dependencies import get_current_admin_user, get_current_root_admin
from app.core.permissions import get_user_permissions
from app.models import (
    AuditLog, Program, Roadmap, RoadmapNode, Scholarship, SiteContent, StaffInvitation, StaffPermission,
    TestSubject, TestTopic, User,
)
from app.schemas.admin import (
    AuditLogOut, InvitationCreate, InvitationOut, OverviewOut, PermissionsUpdate, StaffOut, UserDetailOut,
    UserListOut, UserUpdate,
)
from app.schemas.auth import MessageResponse, UserOut, user_with_permissions
from app.services import invitation_service
from app.services.audit_service import record_audit
from app.services.auth_service import revoke_all_sessions
from app.services.student_service import build_profile_out

router = APIRouter(prefix="/api/admin", tags=["Admin: users and staff"])


# ---------- Overview ----------

def count(db: Session, model, *conditions) -> int:
    return db.query(func.count(model.id)).filter(*conditions).scalar() or 0


def module_stats(db: Session, module: str) -> dict:
    """Database counts shown on the dashboard for one content module."""
    if module == "programs":
        return {"programs": count(db, Program), "published_programs": count(db, Program, Program.status == Status.PUBLISHED)}
    if module == "scholarships":
        return {"scholarships": count(db, Scholarship),
                "published_scholarships": count(db, Scholarship, Scholarship.status == Status.PUBLISHED)}
    if module == "roadmaps":
        return {"roadmaps": count(db, Roadmap), "roadmap_nodes": count(db, RoadmapNode)}
    if module == "test_prep":
        return {"test_subjects": count(db, TestSubject), "test_topics": count(db, TestTopic)}
    if module == "site_content":
        return {"site_content_blocks": count(db, SiteContent)}
    return {}


def recent_logs(db: Session, category: str, limit: int, actor_id: int | None = None):
    query = db.query(AuditLog).filter(AuditLog.category == category)
    if actor_id is not None:
        query = query.filter(AuditLog.actor_id == actor_id)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.get("/overview", response_model=OverviewOut)
def overview(user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    permissions = get_user_permissions(db, user)
    stats = {}
    for module in permissions:
        stats.update(module_stats(db, module))

    if user.role == Role.ROOT_ADMIN:
        stats.update({
            "students": count(db, User, User.role == Role.STUDENT),
            "verified_students": count(db, User, User.role == Role.STUDENT, User.is_email_verified.is_(True)),
            "staff": count(db, User, User.role == Role.STAFF),
            "administrators": count(db, User, User.role == Role.ROOT_ADMIN),
            "pending_invitations": count(
                db, StaffInvitation, StaffInvitation.accepted_at.is_(None), StaffInvitation.revoked_at.is_(None),
                StaffInvitation.expires_at > func.now(),
            ),
        })
        return OverviewOut(
            role=user.role,
            stats=stats,
            permissions=permissions,
            recent_accounts=db.query(User).order_by(User.created_at.desc()).limit(6).all(),
            recent_content=recent_logs(db, "content", 8),
            recent_account_activity=recent_logs(db, "account", 8),
        )

    # Staff see their own recent changes only
    return OverviewOut(
        role=user.role, stats=stats, permissions=permissions,
        recent_content=recent_logs(db, "content", 8, actor_id=user.id),
    )


# ---------- Users ----------

def like_pattern(text: str) -> str:
    """A 'contains' pattern in which %, _ and \\ typed by the user match literally."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("/users", response_model=UserListOut)
def list_users(
    search: str = Query("", max_length=SEARCH_MAX),
    role: str = Query("", max_length=20),
    status_filter: str = Query("", alias="status", max_length=20),
    page: int = Query(1, ge=1, le=100_000),
    page_size: int = Query(20, ge=1, le=100),
    root: User = Depends(get_current_root_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search.strip():
        pattern = like_pattern(search.strip())
        query = query.filter(or_(User.full_name.ilike(pattern, escape="\\"), User.email.ilike(pattern, escape="\\")))
    if role in Role.ALL:
        query = query.filter(User.role == role)
    if status_filter == "active":
        query = query.filter(User.is_active.is_(True), User.is_email_verified.is_(True))
    elif status_filter == "inactive":
        query = query.filter(User.is_active.is_(False))
    elif status_filter == "unverified":
        query = query.filter(User.is_email_verified.is_(False))

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return UserListOut(items=users, total=total, page=page, page_size=page_size)


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def ensure_not_root_admin(target: User):
    """Root admin accounts are managed from the command line only."""
    if target.role == Role.ROOT_ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Root admin accounts cannot be changed from the dashboard.")


@router.get("/users/{user_id}", response_model=UserDetailOut)
def get_user(user_id: int, root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    permissions = get_user_permissions(db, user) if user.role == Role.STAFF else {}
    detail = user_with_permissions(UserDetailOut, user, permissions)
    if user.role == Role.STUDENT:
        detail.profile = build_profile_out(user, user.profile)
    detail.recent_activity = (
        db.query(AuditLog)
        .filter(or_(AuditLog.actor_id == user.id, (AuditLog.entity_type == "user") & (AuditLog.entity_id == user.id)))
        .order_by(AuditLog.created_at.desc()).limit(15).all()
    )
    return detail


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    ensure_not_root_admin(user)

    if data.full_name is not None and data.full_name != user.full_name:
        user.full_name = data.full_name
        record_audit(db, root, "account", "user.updated", f"Updated name for {user.email}", "user", user.id)

    if data.is_active is not None and data.is_active != user.is_active:
        user.is_active = data.is_active
        if not data.is_active:
            revoke_all_sessions(db, user)  # signs the user out immediately
        action = "user.activated" if data.is_active else "user.deactivated"
        verb = "Activated" if data.is_active else "Deactivated"
        record_audit(db, root, "account", action, f"{verb} account {user.email}", "user", user.id)

    db.commit()
    return user


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(user_id: int, root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    ensure_not_root_admin(user)
    # Content the user created is kept; its created_by link is cleared (ON DELETE SET NULL)
    record_audit(db, root, "account", "user.deleted", f"Deleted {user.role} account {user.email}", "user", user.id)
    db.delete(user)
    db.commit()
    return {"message": "Account deleted."}


# ---------- Staff permissions ----------

@router.get("/staff", response_model=list[StaffOut])
def list_staff(root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    staff_members = db.query(User).filter(User.role == Role.STAFF).order_by(User.full_name).all()
    return [
        user_with_permissions(StaffOut, member, {row.module: row.access_level for row in member.permissions})
        for member in staff_members
    ]


@router.put("/staff/{user_id}/permissions", response_model=StaffOut)
def update_staff_permissions(
    user_id: int, data: PermissionsUpdate, root: User = Depends(get_current_root_admin), db: Session = Depends(get_db),
):
    user = get_user_or_404(db, user_id)
    if user.role != Role.STAFF:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permissions can only be set for staff accounts.")

    cleaned = invitation_service.validate_permissions(data.permissions)
    db.query(StaffPermission).filter(StaffPermission.user_id == user.id).delete()
    for module, level in cleaned.items():
        db.add(StaffPermission(user_id=user.id, module=module, access_level=level))
    record_audit(db, root, "account", "permissions.updated",
                 f"Updated permissions for {user.email}: {invitation_service.describe_permissions(cleaned)}",
                 "user", user.id)
    db.commit()
    return user_with_permissions(StaffOut, user, cleaned)


# ---------- Invitations ----------

def invitation_out(invitation: StaffInvitation) -> InvitationOut:
    out = InvitationOut.model_validate(invitation)
    out.invited_by_name = invitation.invited_by.full_name if invitation.invited_by else None
    return out


@router.get("/invitations", response_model=list[InvitationOut])
def list_invitations(root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    invitations = db.query(StaffInvitation).order_by(StaffInvitation.created_at.desc()).limit(100).all()
    return [invitation_out(invitation) for invitation in invitations]


@router.post("/invitations", response_model=InvitationOut, status_code=201)
def create_invitation(data: InvitationCreate, root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    invitation = invitation_service.create_invitation(db, root, data.full_name, data.email, data.permissions)
    return invitation_out(invitation)


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationOut)
def resend_invitation(invitation_id: int, root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    return invitation_out(invitation_service.resend_invitation(db, root, invitation_id))


@router.delete("/invitations/{invitation_id}", response_model=MessageResponse)
def revoke_invitation(invitation_id: int, root: User = Depends(get_current_root_admin), db: Session = Depends(get_db)):
    invitation_service.revoke_invitation(db, root, invitation_id)
    return {"message": "Invitation revoked."}


# ---------- Activity log ----------

@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(
    category: str = Query("", max_length=20),
    limit: int = Query(50, ge=1, le=200),
    root: User = Depends(get_current_root_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if category in ("account", "content"):
        query = query.filter(AuditLog.category == category)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.get("/modules")
def modules(user: User = Depends(get_current_admin_user)):
    """Module names for building the permission forms."""
    return CONTENT_MODULES

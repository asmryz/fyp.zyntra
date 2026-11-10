"""
Module-level permissions for the content management system.

Root admin   -> full access to every module.
Staff        -> access depends on their StaffPermission row for the module:
    read        view all records, cannot change anything
    write       create records, and edit/delete only records they created
    read_write  view, create, edit and delete all records
No row       -> no access to the module at all.

Every admin content endpoint uses `module_access(...)`, so these rules are
enforced on the backend even if someone calls the API directly.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.constants import CONTENT_MODULES, AccessLevel, Role
from app.core.dependencies import get_current_admin_user
from app.models import StaffPermission, User


class ModuleAccess:
    def __init__(self, user: User, module: str, level: str):
        self.user = user
        self.module = module
        self.level = level
        self.can_view_all = level in (AccessLevel.READ, AccessLevel.READ_WRITE)
        self.can_write = level in (AccessLevel.WRITE, AccessLevel.READ_WRITE)

    @property
    def own_records_only(self):
        """True for 'write' staff, who only see and edit their own records."""
        return not self.can_view_all

    def can_view_record(self, record) -> bool:
        return self.can_view_all or record.created_by_id == self.user.id

    def can_edit_record(self, record) -> bool:
        return self.can_write and self.can_view_record(record)


def get_user_permissions(db: Session, user: User) -> dict:
    """Return {module: access_level} for a user. Root admins get read_write everywhere."""
    if user.role == Role.ROOT_ADMIN:
        return {module: AccessLevel.READ_WRITE for module in CONTENT_MODULES}
    if user.role != Role.STAFF:
        return {}
    rows = db.query(StaffPermission).filter(StaffPermission.user_id == user.id).all()
    return {row.module: row.access_level for row in rows}


def module_access(module: str, need_write: bool = False):
    """Dependency factory: checks the current user's permission for one module."""
    def dependency(user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)) -> ModuleAccess:
        level = get_user_permissions(db, user).get(module)
        if level is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this module.")

        access = ModuleAccess(user, module, level)
        if need_write and not access.can_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your permission for this module is read-only.",
            )
        return access
    return dependency


def ensure_can_view(access: ModuleAccess, record):
    # 404 instead of 403 so 'write' staff cannot discover other people's records
    if record is None or not access.can_view_record(record):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")


def ensure_can_edit(access: ModuleAccess, record):
    ensure_can_view(access, record)
    if not access.can_edit_record(record):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot edit this record.")


def visible_records(query, model, access: ModuleAccess):
    """Limit a list query to the records this user may see."""
    if access.own_records_only:
        query = query.filter(model.created_by_id == access.user.id)
    return query

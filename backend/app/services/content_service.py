"""Small helpers shared by the content management routers."""
import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ModuleAccess
from app.services.audit_service import record_audit


def get_or_404(db: Session, model, record_id: int, label: str = "Record"):
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found.")
    return record


def apply_changes(record, data: dict):
    """Copy validated fields from a request body onto a database record."""
    for field, value in data.items():
        setattr(record, field, value)


def to_admin_out(schema, record, access: ModuleAccess, **extra):
    """Convert a record to its admin schema and add the per-user can_edit flag."""
    out = schema.model_validate(record)
    out.can_edit = access.can_edit_record(record)
    for field, value in extra.items():
        setattr(out, field, value)
    return out


def audit_content(db: Session, access: ModuleAccess, action: str, entity_type: str, entity_id: int, summary: str):
    record_audit(db, access.user, "content", action, summary, entity_type, entity_id)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "item"


def unique_slug(db: Session, model, text: str, exclude_id: int | None = None) -> str:
    base = slugify(text)[:150]
    slug = base
    counter = 2
    while True:
        query = db.query(model.id).filter(model.slug == slug)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if query.first() is None:
            return slug
        slug = f"{base}-{counter}"
        counter += 1

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def record_audit(
    db: Session,
    actor: User | None,
    category: str,
    action: str,
    summary: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
):
    """
    Add an audit entry to the current transaction.
    The caller commits, so the log is saved together with the change it describes.
    """
    db.add(AuditLog(
        actor_id=actor.id if actor else None,
        actor_name=actor.full_name if actor else None,
        category=category,
        action=action,
        summary=summary[:300],
        entity_type=entity_type,
        entity_id=entity_id,
    ))

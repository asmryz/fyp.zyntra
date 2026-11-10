from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from database import Base
from app.core.security import utcnow


class AuditLog(Base):
    """Record of important account and administrative actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    # Copy of the actor's name so the log stays readable if the account is deleted
    actor_name = Column(String(120))
    category = Column(String(20), nullable=False, index=True)  # 'account' or 'content'
    action = Column(String(60), nullable=False)                # e.g. 'scholarship.updated'
    entity_type = Column(String(40))
    entity_id = Column(Integer)
    summary = Column(String(300), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), index=True)

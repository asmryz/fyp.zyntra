from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.security import utcnow


class TimestampMixin:
    """Adds created_at / updated_at columns to a model."""
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow, server_default=func.now()
    )


class PublishableMixin:
    """
    Shared columns for top-level content records.

    status        - 'draft' (hidden from students) or 'published'
    created_by_id - used for the 'write' permission (staff edit their own records)
    updated_by_id - shown in the admin interface as "last edited by"
    """
    status = Column(String(20), nullable=False, default="draft", server_default="draft", index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

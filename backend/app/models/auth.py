from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base
from app.core.security import utcnow


class RefreshToken(Base):
    """
    A login session. The raw token lives only in the user's HttpOnly cookie;
    the database keeps its SHA-256 hash so sessions can be revoked on logout,
    password reset or account deactivation.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class AuthCode(Base):
    """
    Six-digit codes for email verification and password reset.
    Only an HMAC hash of the code is stored.
    """
    __tablename__ = "auth_codes"
    __table_args__ = (Index("ix_auth_codes_user_purpose", "user_id", "purpose"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = Column(String(30), nullable=False)  # see constants.CodePurpose
    code_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    # Set when the code is used successfully or replaced by a newer code
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class StaffInvitation(Base):
    __tablename__ = "staff_invitations"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    # Example: {"scholarships": "read_write", "roadmaps": "read"}
    permissions = Column(JSONB, nullable=False, default=dict)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    accepted_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    invited_by = relationship("User", foreign_keys=[invited_by_id])

    @property
    def status(self):
        if self.accepted_at:
            return "accepted"
        if self.revoked_at:
            return "revoked"
        if self.expires_at < utcnow():
            return "expired"
        return "pending"

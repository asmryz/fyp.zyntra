from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship, validates

from database import Base
from app.models.base import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('root_admin', 'staff', 'student')", name="ck_users_role"),
    )

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    # Emails are stored in lowercase. Uniqueness is case-insensitive: see the
    # unique index on lower(email) below; ix_users_email is a plain lookup index.
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    is_email_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    email_verified_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))

    profile = relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True,
    )
    permissions = relationship(
        "StaffPermission", back_populates="user", cascade="all, delete-orphan", passive_deletes=True,
    )

    @validates("email")
    def lowercase_email(self, key, value):
        # Safety net: every code path that sets an email stores it in lowercase
        return value.strip().lower() if value else value


# Two addresses that differ only in letter case are the same account
Index("uq_users_email_lower", func.lower(User.email), unique=True)


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        CheckConstraint(
            "percentage IS NULL OR (percentage >= 0 AND percentage <= 100)",
            name="ck_student_profiles_percentage_range",
        ),
        CheckConstraint(
            "(obtained_marks IS NULL OR obtained_marks >= 0) AND (total_marks IS NULL OR total_marks >= 0)",
            name="ck_student_profiles_marks_not_negative",
        ),
        CheckConstraint(
            "obtained_marks IS NULL OR total_marks IS NULL OR obtained_marks <= total_marks",
            name="ck_student_profiles_marks_within_total",
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    contact_number = Column(String(30))
    previous_qualification = Column(String(60))
    academic_background = Column(String(120))   # e.g. Pre-Engineering, ICS, Commerce
    board_or_university = Column(String(150))
    passing_year = Column(Integer)
    obtained_marks = Column(Integer)
    total_marks = Column(Integer)
    percentage = Column(Numeric(5, 2))
    preferred_program_id = Column(Integer, ForeignKey("programs.id", ondelete="SET NULL"))
    additional_details = Column(Text)

    user = relationship("User", back_populates="profile")
    preferred_program = relationship("Program")


class StaffPermission(Base):
    """One row per (staff member, module) with the access level for that module."""
    __tablename__ = "staff_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "module", name="uq_staff_permissions_user_module"),
        CheckConstraint("access_level IN ('read', 'write', 'read_write')", name="ck_staff_permissions_level"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module = Column(String(40), nullable=False)
    access_level = Column(String(20), nullable=False)

    user = relationship("User", back_populates="permissions")

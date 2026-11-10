"""
Importing this package registers every model on Base.metadata,
which Alembic uses to generate migrations.
"""
from app.models.user import User, StudentProfile, StaffPermission
from app.models.auth import RefreshToken, AuthCode, StaffInvitation
from app.models.audit import AuditLog
from app.models.content import (
    Program, Scholarship, Roadmap, RoadmapBranch, RoadmapNode, RoadmapNodeSection, SiteContent,
)
from app.models.test_prep import TestSubject, TestTopic, LearningResource

__all__ = [
    "User", "StudentProfile", "StaffPermission",
    "RefreshToken", "AuthCode", "StaffInvitation",
    "AuditLog",
    "Program", "Scholarship", "Roadmap", "RoadmapBranch", "RoadmapNode", "RoadmapNodeSection", "SiteContent",
    "TestSubject", "TestTopic", "LearningResource",
]

"""
Admission-test preparation content.

TestSubject -> TestTopic
TestSubject -> LearningResource (optionally linked to one topic)
"""
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base
from app.models.base import PublishableMixin, TimestampMixin


class TestSubject(TimestampMixin, PublishableMixin, Base):
    __tablename__ = "test_subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")

    topics = relationship(
        "TestTopic", back_populates="subject", cascade="all, delete-orphan", passive_deletes=True,
        order_by="TestTopic.sort_order",
    )
    resources = relationship(
        "LearningResource", back_populates="subject", cascade="all, delete-orphan", passive_deletes=True,
        order_by="LearningResource.sort_order",
    )


class TestTopic(TimestampMixin, Base):
    __tablename__ = "test_topics"
    __table_args__ = (
        # The same title may be used again under a different subject
        UniqueConstraint("subject_id", "title", name="uq_test_topics_subject_title"),
    )

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("test_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    explanation = Column(Text)
    status = Column(String(20), nullable=False, default="draft", server_default="draft")
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")

    subject = relationship("TestSubject", back_populates="topics")
    resources = relationship("LearningResource", back_populates="topic", passive_deletes=True)


class LearningResource(TimestampMixin, Base):
    """Educational video, article or notes, PDF (such as a past paper) or link to a learning platform."""
    __tablename__ = "learning_resources"
    __table_args__ = (
        # Must match constants.RESOURCE_TYPES
        CheckConstraint(
            "resource_type IN ('video', 'article', 'pdf', 'link')", name="ck_learning_resources_type",
        ),
    )

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("test_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    # If the topic is deleted the resource stays with the subject
    topic_id = Column(Integer, ForeignKey("test_topics.id", ondelete="SET NULL"), index=True)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    resource_type = Column(String(30), nullable=False, default="link")  # see constants.RESOURCE_TYPES
    description = Column(String(300))
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")

    subject = relationship("TestSubject", back_populates="resources")
    topic = relationship("TestTopic", back_populates="resources")


"""Programs, scholarships, roadmaps and general website content."""
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base
from app.models.base import PublishableMixin, TimestampMixin


class Program(TimestampMixin, PublishableMixin, Base):
    __tablename__ = "programs"
    __table_args__ = (
        CheckConstraint(
            "min_percentage IS NULL OR (min_percentage >= 0 AND min_percentage <= 100)",
            name="ck_programs_min_percentage_range",
        ),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    slug = Column(String(160), nullable=False, unique=True, index=True)
    department = Column(String(120))
    degree_level = Column(String(40))      # e.g. Undergraduate, Graduate
    duration = Column(String(60))
    summary = Column(String(300))
    description = Column(Text)
    admission_requirements = Column(Text)
    # Criteria used by the preliminary eligibility check
    min_percentage = Column(Numeric(5, 2))
    accepted_qualifications = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    eligibility_notes = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")

    roadmaps = relationship("Roadmap", back_populates="program")


class Scholarship(TimestampMixin, PublishableMixin, Base):
    """
    The list fields are stored as JSONB arrays because they are always read
    and edited together with the scholarship and keep their order.
    application_steps holds objects: [{"title": "...", "description": "..."}]
    """
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    scholarship_type = Column(String(80))
    summary = Column(String(300))
    description = Column(Text)
    eligibility_criteria = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    benefits = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    required_documents = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    application_steps = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    conditions = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")


class Roadmap(TimestampMixin, PublishableMixin, Base):
    """
    A program roadmap. The title is the central heading (for example
    "Computer Science"); branches hang below it, one column per career path.

    Roadmap -> RoadmapBranch -> RoadmapNode -> RoadmapNodeSection
    """
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(80))          # e.g. Program roadmap, Career roadmap
    summary = Column(String(300))
    description = Column(Text)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="SET NULL"), index=True)

    program = relationship("Program", back_populates="roadmaps")
    branches = relationship(
        "RoadmapBranch", back_populates="roadmap", cascade="all, delete-orphan", passive_deletes=True,
        order_by="(RoadmapBranch.position, RoadmapBranch.id)",
    )


class RoadmapBranch(TimestampMixin, Base):
    """One career path or specialisation: a coloured column of steps."""
    __tablename__ = "roadmap_branches"

    id = Column(Integer, primary_key=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    color = Column(String(7), nullable=False, default="#2563EB", server_default="#2563EB")  # hex, e.g. #16A34A
    position = Column(Integer, nullable=False, default=0, server_default="0")

    roadmap = relationship("Roadmap", back_populates="branches")
    nodes = relationship(
        "RoadmapNode", back_populates="branch", cascade="all, delete-orphan", passive_deletes=True,
        order_by="(RoadmapNode.position, RoadmapNode.id)",
    )


class RoadmapNode(TimestampMixin, Base):
    """A step in a branch, shown as a circle. Steps are listed top to bottom by position."""
    __tablename__ = "roadmap_nodes"
    # Checked at commit time, so reordering (which swaps positions row by row)
    # can pass through intermediate states inside one transaction
    __table_args__ = (
        UniqueConstraint("branch_id", "position", name="uq_roadmap_nodes_branch_position",
                         deferrable=True, initially="DEFERRED"),
    )

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("roadmap_branches.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    position = Column(Integer, nullable=False, default=0, server_default="0")
    # At most one step per roadmap is selected when a student opens the roadmap
    is_default = Column(Boolean, nullable=False, default=False, server_default="false")

    branch = relationship("RoadmapBranch", back_populates="nodes")
    sections = relationship(
        "RoadmapNodeSection", back_populates="node", cascade="all, delete-orphan", passive_deletes=True,
        order_by="(RoadmapNodeSection.position, RoadmapNodeSection.id)",
    )


class RoadmapNodeSection(TimestampMixin, Base):
    """
    A block in a step's detail card, such as Skills, Tools & Technologies,
    Prerequisites or Projects. `content` depends on section_type
    (see constants.ROADMAP_SECTION_TYPES):
        skills, tools, list -> {"items": ["Python", "Git"]}
        text                -> {"text": "..."}
        links               -> {"links": [{"label": "...", "url": "https://..."}]}
    """
    __tablename__ = "roadmap_node_sections"
    # Deferred like the step positions: saving a step replaces all its sections
    __table_args__ = (
        UniqueConstraint("node_id", "position", name="uq_roadmap_node_sections_node_position",
                         deferrable=True, initially="DEFERRED"),
    )

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    section_title = Column(String(100), nullable=False)
    section_type = Column(String(20), nullable=False)
    content = Column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    position = Column(Integer, nullable=False, default=0, server_default="0")

    node = relationship("RoadmapNode", back_populates="sections")


class SiteContent(TimestampMixin, PublishableMixin, Base):
    """Editable text blocks for the website, looked up by key (see constants.SITE_CONTENT_KEYS)."""
    __tablename__ = "site_content"

    id = Column(Integer, primary_key=True)
    key = Column(String(60), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False, default="")

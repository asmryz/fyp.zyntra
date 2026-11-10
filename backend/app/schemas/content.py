"""Request and response schemas for programs, scholarships, roadmaps and website content."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.constants import QUALIFICATIONS, ROADMAP_SECTION_TYPES

StatusField = Literal["draft", "published"]


class InputModel(BaseModel):
    """Base for request bodies: trims whitespace around every string."""
    model_config = ConfigDict(str_strip_whitespace=True)


class OutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def clean_text_list(items: list[str]) -> list[str]:
    """Drop blank lines from list fields such as eligibility criteria."""
    return [item.strip() for item in items if item and item.strip()]


def check_url(url: str) -> str:
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("Links must start with http:// or https://")
    return url


class AdminRecordOut(OutputModel):
    """Fields shared by every record shown in the admin dashboards."""
    id: int
    status: StatusField
    created_by_id: int | None = None
    updated_by_id: int | None = None
    created_at: datetime
    updated_at: datetime
    # Set by the API for the current user (False for read-only staff)
    can_edit: bool = False


# ---------- Programs ----------

class ProgramIn(InputModel):
    name: str = Field(min_length=2, max_length=150)
    department: str | None = Field(default=None, max_length=120)
    degree_level: str | None = Field(default=None, max_length=40)
    duration: str | None = Field(default=None, max_length=60)
    summary: str | None = Field(default=None, max_length=300)
    description: str | None = None
    admission_requirements: str | None = None
    min_percentage: float | None = Field(default=None, ge=0, le=100)
    accepted_qualifications: list[str] = []
    eligibility_notes: str | None = None
    status: StatusField = "draft"
    sort_order: int = 0

    @field_validator("accepted_qualifications")
    @classmethod
    def check_qualifications(cls, values):
        for value in values:
            if value not in QUALIFICATIONS:
                raise ValueError(f"Unknown qualification: {value}")
        return values


class ProgramAdminOut(AdminRecordOut):
    name: str
    slug: str
    department: str | None
    degree_level: str | None
    duration: str | None
    summary: str | None
    description: str | None
    admission_requirements: str | None
    min_percentage: float | None
    accepted_qualifications: list[str]
    eligibility_notes: str | None
    sort_order: int


class RoadmapLink(OutputModel):
    id: int
    title: str
    category: str | None = None


class ProgramPublicOut(OutputModel):
    id: int
    name: str
    slug: str
    department: str | None
    degree_level: str | None
    duration: str | None
    summary: str | None
    description: str | None
    admission_requirements: str | None
    min_percentage: float | None
    accepted_qualifications: list[str]
    eligibility_notes: str | None
    roadmaps: list[RoadmapLink] = []


# ---------- Scholarships ----------

class ApplicationStep(InputModel):
    title: str = Field(min_length=1, max_length=150)
    description: str = ""


class ScholarshipIn(InputModel):
    title: str = Field(min_length=2, max_length=200)
    scholarship_type: str | None = Field(default=None, max_length=80)
    summary: str | None = Field(default=None, max_length=300)
    description: str | None = None
    eligibility_criteria: list[str] = []
    benefits: list[str] = []
    required_documents: list[str] = []
    application_steps: list[ApplicationStep] = []
    conditions: list[str] = []
    status: StatusField = "draft"
    sort_order: int = 0

    @field_validator("eligibility_criteria", "benefits", "required_documents", "conditions")
    @classmethod
    def drop_blank_items(cls, values):
        return clean_text_list(values)


class ScholarshipFields(OutputModel):
    id: int
    title: str
    scholarship_type: str | None
    summary: str | None
    description: str | None
    eligibility_criteria: list[str]
    benefits: list[str]
    required_documents: list[str]
    application_steps: list[ApplicationStep]
    conditions: list[str]
    sort_order: int


class ScholarshipAdminOut(AdminRecordOut, ScholarshipFields):
    pass


class ScholarshipPublicOut(ScholarshipFields):
    updated_at: datetime


# ---------- Roadmaps ----------

HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"


class LinkItem(InputModel):
    label: str = Field(min_length=1, max_length=100)
    url: str = Field(max_length=500)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        return check_url(value)


class RoadmapIn(InputModel):
    # The title is shown as the roadmap's central heading, e.g. "Computer Science"
    title: str = Field(min_length=2, max_length=200)
    category: str | None = Field(default=None, max_length=80)
    summary: str | None = Field(default=None, max_length=300)
    description: str | None = None
    program_id: int | None = None
    status: StatusField = "draft"


class RoadmapBranchIn(InputModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    color: str = Field(default="#2563EB", pattern=HEX_COLOR)

    @field_validator("color")
    @classmethod
    def upper_color(cls, value):
        return value.upper()


class RoadmapSectionIn(InputModel):
    """
    One block of a step's detail card. Only the content key that matches the
    type is kept: items (skills, tools, list), text, or links.
    """
    section_title: str = Field(min_length=1, max_length=100)
    section_type: str
    content: dict = {}

    @field_validator("section_type")
    @classmethod
    def check_type(cls, value):
        if value not in ROADMAP_SECTION_TYPES:
            raise ValueError("Unknown section type.")
        return value

    @model_validator(mode="after")
    def clean_content(self):
        raw = self.content or {}
        if self.section_type in ("skills", "tools", "list"):
            items = raw.get("items") or []
            if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                raise ValueError("Section items must be a list of text values.")
            items = clean_text_list(items)
            if any(len(item) > 200 for item in items):
                raise ValueError("Each item can be at most 200 characters.")
            if len(items) > 50:
                raise ValueError("A section can have at most 50 items.")
            self.content = {"items": items}
        elif self.section_type == "text":
            text = raw.get("text") or ""
            if not isinstance(text, str) or len(text) > 5000:
                raise ValueError("Section text must be at most 5000 characters.")
            self.content = {"text": text.strip()}
        else:
            links = [LinkItem.model_validate(link) for link in (raw.get("links") or [])]
            if len(links) > 30:
                raise ValueError("A section can have at most 30 links.")
            self.content = {"links": [link.model_dump() for link in links]}
        return self


class RoadmapNodeIn(InputModel):
    """A step and its detail sections. Saving replaces the step's sections with this list, in order."""
    title: str = Field(min_length=1, max_length=150)
    description: str | None = None
    is_default: bool = False
    sections: list[RoadmapSectionIn] = Field(default=[], max_length=30)


class ReorderIn(BaseModel):
    """The complete list of ids in their new order."""
    ids: list[int] = Field(min_length=1)


class RoadmapSectionOut(OutputModel):
    id: int
    section_title: str
    section_type: str
    content: dict
    position: int


class RoadmapNodeOut(OutputModel):
    id: int
    branch_id: int
    title: str
    description: str | None
    position: int
    is_default: bool
    sections: list[RoadmapSectionOut] = []


class RoadmapBranchOut(OutputModel):
    id: int
    roadmap_id: int
    name: str
    description: str | None
    color: str
    position: int
    nodes: list[RoadmapNodeOut] = []


class RoadmapAdminOut(AdminRecordOut):
    title: str
    category: str | None
    summary: str | None
    description: str | None
    program_id: int | None
    program_name: str | None = None
    branch_count: int = 0
    node_count: int = 0


class RoadmapAdminDetailOut(RoadmapAdminOut):
    branches: list[RoadmapBranchOut] = []


class RoadmapPublicOut(OutputModel):
    id: int
    title: str
    category: str | None
    summary: str | None
    description: str | None
    program_name: str | None = None
    branch_count: int = 0
    node_count: int = 0
    updated_at: datetime


class RoadmapPublicDetailOut(RoadmapPublicOut):
    branches: list[RoadmapBranchOut] = []


# ---------- Website content ----------

class SiteContentUpdate(InputModel):
    """Editable fields of a website content block. Its key (website section) cannot be changed."""
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    status: StatusField = "draft"


class SiteContentAdminOut(AdminRecordOut):
    key: str
    title: str
    body: str
    used_on: str | None = None


class SiteContentPublicOut(OutputModel):
    key: str
    title: str
    body: str

"""Schemas for admission-test preparation content."""
from pydantic import Field, field_validator

from app.constants import LONG_TEXT_MAX, RESOURCE_TYPES
from app.schemas.content import AdminRecordOut, InputModel, OutputModel, StatusField, check_display_order, check_url


# ---------- Admin: subjects, topics, resources ----------

class SubjectIn(InputModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=LONG_TEXT_MAX)
    status: StatusField = "draft"
    sort_order: int = 1

    @field_validator("sort_order", mode="before")
    @classmethod
    def check_sort_order(cls, value):
        return check_display_order(value)


class SubjectAdminOut(AdminRecordOut):
    name: str
    description: str | None
    sort_order: int
    topic_count: int = 0
    resource_count: int = 0


class TopicIn(InputModel):
    title: str = Field(min_length=2, max_length=200)
    explanation: str | None = Field(default=None, max_length=LONG_TEXT_MAX)
    status: StatusField = "draft"
    sort_order: int = 1

    @field_validator("sort_order", mode="before")
    @classmethod
    def check_sort_order(cls, value):
        return check_display_order(value)


class TopicOut(OutputModel):
    id: int
    subject_id: int
    title: str
    explanation: str | None
    status: StatusField
    sort_order: int


class ResourceIn(InputModel):
    title: str = Field(min_length=2, max_length=200)
    url: str = Field(max_length=500)
    resource_type: str = "link"
    description: str | None = Field(default=None, max_length=300)
    topic_id: int | None = None
    sort_order: int = 1

    @field_validator("sort_order", mode="before")
    @classmethod
    def check_sort_order(cls, value):
        return check_display_order(value)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        return check_url(value)

    @field_validator("resource_type")
    @classmethod
    def check_type(cls, value):
        if value not in RESOURCE_TYPES:
            raise ValueError("Unknown resource type.")
        return value


class ResourceOut(OutputModel):
    id: int
    subject_id: int
    topic_id: int | None
    title: str
    url: str
    resource_type: str
    description: str | None
    sort_order: int


class SubjectAdminDetailOut(SubjectAdminOut):
    topics: list[TopicOut] = []
    resources: list[ResourceOut] = []


class TopicAdminDetailOut(TopicOut):
    subject_name: str


# ---------- Student-facing ----------

class StudentTopicSummary(OutputModel):
    id: int
    title: str


class StudentSubjectOut(OutputModel):
    id: int
    name: str
    description: str | None
    topic_count: int = 0


class StudentSubjectDetailOut(StudentSubjectOut):
    topics: list[StudentTopicSummary] = []
    resources: list[ResourceOut] = []


class StudentTopicDetailOut(OutputModel):
    id: int
    subject_id: int
    subject_name: str
    title: str
    explanation: str | None
    resources: list[ResourceOut] = []

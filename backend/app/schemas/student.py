from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.constants import MARKS_MAX, QUALIFICATIONS
from app.schemas.auth import clean_full_name
from app.schemas.content import InputModel, OutputModel


class ProfileIn(InputModel):
    full_name: str
    contact_number: str | None = Field(default=None, max_length=30)
    previous_qualification: str | None = None
    academic_background: str | None = Field(default=None, max_length=120)
    board_or_university: str | None = Field(default=None, max_length=150)
    passing_year: int | None = Field(default=None, ge=1970)
    obtained_marks: int | None = Field(default=None, ge=0, le=MARKS_MAX)
    total_marks: int | None = Field(default=None, gt=0, le=MARKS_MAX)
    percentage: float | None = Field(default=None, ge=0, le=100)
    preferred_program_id: int | None = None
    additional_details: str | None = Field(default=None, max_length=2000)

    @field_validator("passing_year")
    @classmethod
    def check_passing_year(cls, value):
        # Checked per request, so the limit follows the calendar (it was fixed when the server started)
        if value is not None and value > datetime.now().year + 1:
            raise ValueError(f"Passing year cannot be later than {datetime.now().year + 1}.")
        return value

    @field_validator("full_name")
    @classmethod
    def check_name(cls, value):
        return clean_full_name(value)

    @field_validator("contact_number")
    @classmethod
    def check_contact(cls, value):
        if not value:
            return None
        allowed = set("0123456789+- ()")
        if any(ch not in allowed for ch in value) or sum(ch.isdigit() for ch in value) < 7:
            raise ValueError("Enter a valid contact number (digits, spaces, +, - only).")
        return value

    @field_validator("previous_qualification")
    @classmethod
    def check_qualification(cls, value):
        if not value:
            return None
        if value not in QUALIFICATIONS:
            raise ValueError("Select a qualification from the list.")
        return value

    @model_validator(mode="after")
    def check_marks(self):
        if (self.obtained_marks is None) != (self.total_marks is None):
            raise ValueError("Enter both obtained and total marks, or leave both empty.")
        if self.obtained_marks is not None and self.total_marks is not None:
            if self.obtained_marks > self.total_marks:
                raise ValueError("Obtained marks cannot be greater than total marks.")
        return self


class ProfileOut(OutputModel):
    full_name: str
    email: str
    contact_number: str | None = None
    previous_qualification: str | None = None
    academic_background: str | None = None
    board_or_university: str | None = None
    passing_year: int | None = None
    obtained_marks: int | None = None
    total_marks: int | None = None
    percentage: float | None = None
    preferred_program_id: int | None = None
    preferred_program_name: str | None = None
    additional_details: str | None = None
    completeness_percent: int = 0
    missing_fields: list[str] = []


class EligibilityCheck(BaseModel):
    label: str
    result: str          # 'met', 'not_met' or 'missing'
    detail: str


class ProgramEligibility(BaseModel):
    program_id: int
    program_name: str
    program_slug: str
    status: str          # 'meets_listed_criteria', 'not_met', 'missing_information', 'criteria_not_available'
    checks: list[EligibilityCheck]
    notes: str | None = None


class EligibilityOut(BaseModel):
    disclaimer: str
    profile_complete_for_check: bool
    programs: list[ProgramEligibility]


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class AssistantAnswer(BaseModel):
    answer: str
    sources: list[str] = []

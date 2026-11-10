"""
Student profile helpers and the preliminary eligibility check.

The eligibility check compares the student's saved profile with the criteria
an administrator entered for each published program. It is guidance only and
never an admission decision. The planned LangGraph Program Eligibility Agent
can call the same function later.
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.constants import Status
from app.models import Program, StudentProfile, User
from app.schemas.student import EligibilityCheck, EligibilityOut, ProfileOut, ProgramEligibility

ELIGIBILITY_DISCLAIMER = (
    "This is preliminary guidance based on the criteria currently published in ZYNTRA and the details in "
    "your profile. It is not an official admission decision. Final eligibility is decided by SZABIST "
    "through its official admission process."
)

# Profile fields used for the completeness meter: (attribute, label)
PROFILE_FIELDS = [
    ("contact_number", "Contact number"),
    ("previous_qualification", "Previous qualification"),
    ("academic_background", "Academic background"),
    ("board_or_university", "Board or university"),
    ("passing_year", "Passing year"),
    ("percentage", "Marks or percentage"),
    ("preferred_program_id", "Preferred program"),
]


def get_or_create_profile(db: Session, user: User) -> StudentProfile:
    if user.profile is None:
        user.profile = StudentProfile(user_id=user.id)
        db.commit()
    return user.profile


def calculate_percentage(obtained_marks, total_marks):
    if obtained_marks is None or not total_marks:
        return None
    return round(Decimal(obtained_marks) * 100 / Decimal(total_marks), 2)


def build_profile_out(user: User, profile: StudentProfile | None) -> ProfileOut:
    data = {"full_name": user.full_name, "email": user.email}
    missing = []
    if profile is not None:
        for field in ProfileOut.model_fields:
            if hasattr(profile, field):
                data[field] = getattr(profile, field)
        data["preferred_program_name"] = profile.preferred_program.name if profile.preferred_program else None
    for attribute, label in PROFILE_FIELDS:
        if profile is None or getattr(profile, attribute) in (None, ""):
            missing.append(label)
    filled = len(PROFILE_FIELDS) - len(missing)
    data["completeness_percent"] = round(filled * 100 / len(PROFILE_FIELDS))
    data["missing_fields"] = missing
    return ProfileOut(**data)


def assess_program(profile: StudentProfile | None, program: Program) -> ProgramEligibility:
    checks = []
    accepted = program.accepted_qualifications or []

    if accepted:
        qualification = profile.previous_qualification if profile else None
        if not qualification:
            checks.append(EligibilityCheck(label="Previous qualification", result="missing",
                                           detail="Add your previous qualification to your profile."))
        elif qualification in accepted:
            checks.append(EligibilityCheck(label="Previous qualification", result="met",
                                           detail=f"{qualification} is listed as an accepted qualification."))
        else:
            checks.append(EligibilityCheck(label="Previous qualification", result="not_met",
                                           detail=f"{qualification} is not in the accepted list: {', '.join(accepted)}."))

    if program.min_percentage is not None:
        minimum = float(program.min_percentage)
        percentage = float(profile.percentage) if profile and profile.percentage is not None else None
        if percentage is None:
            checks.append(EligibilityCheck(label="Marks / percentage", result="missing",
                                           detail="Add your marks or percentage to your profile."))
        elif percentage >= minimum:
            checks.append(EligibilityCheck(label="Marks / percentage", result="met",
                                           detail=f"Your {percentage:.2f}% meets the listed minimum of {minimum:.2f}%."))
        else:
            checks.append(EligibilityCheck(label="Marks / percentage", result="not_met",
                                           detail=f"Your {percentage:.2f}% is below the listed minimum of {minimum:.2f}%."))

    results = {check.result for check in checks}
    if not checks:
        status = "criteria_not_available"
    elif "missing" in results:
        status = "missing_information"
    elif "not_met" in results:
        status = "not_met"
    else:
        status = "meets_listed_criteria"

    return ProgramEligibility(
        program_id=program.id, program_name=program.name, program_slug=program.slug,
        status=status, checks=checks, notes=program.eligibility_notes,
    )


def check_eligibility(db: Session, user: User) -> EligibilityOut:
    profile = user.profile
    programs = (
        db.query(Program).filter(Program.status == Status.PUBLISHED).order_by(Program.sort_order, Program.name).all()
    )
    # Show the student's preferred program first
    if profile and profile.preferred_program_id:
        programs.sort(key=lambda program: program.id != profile.preferred_program_id)

    complete = bool(profile and profile.previous_qualification and profile.percentage is not None)
    return EligibilityOut(
        disclaimer=ELIGIBILITY_DISCLAIMER,
        profile_complete_for_check=complete,
        programs=[assess_program(profile, program) for program in programs],
    )

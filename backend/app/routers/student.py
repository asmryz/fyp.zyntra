"""
Endpoints for the logged-in student: their own profile and preliminary
eligibility. A student can only ever read or change their own data because
the user always comes from the access token.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.constants import Status
from app.core.dependencies import get_current_student
from app.models import Program, User
from app.schemas.student import EligibilityOut, ProfileIn, ProfileOut
from app.services import student_service

router = APIRouter(prefix="/api/student", tags=["Student"])


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_student), db: Session = Depends(get_db)):
    profile = student_service.get_or_create_profile(db, user)
    return student_service.build_profile_out(user, profile)


@router.put("/profile", response_model=ProfileOut)
def update_profile(data: ProfileIn, user: User = Depends(get_current_student), db: Session = Depends(get_db)):
    profile = student_service.get_or_create_profile(db, user)

    if data.preferred_program_id is not None:
        program = db.get(Program, data.preferred_program_id)
        if program is None or program.status != Status.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select a program from the list.")

    user.full_name = data.full_name
    fields = data.model_dump(exclude={"full_name"})
    for field, value in fields.items():
        setattr(profile, field, value)

    # When marks are given, the percentage is calculated from them
    calculated = student_service.calculate_percentage(data.obtained_marks, data.total_marks)
    if calculated is not None:
        profile.percentage = calculated

    db.commit()
    db.refresh(profile)
    return student_service.build_profile_out(user, profile)


@router.get("/eligibility", response_model=EligibilityOut)
def eligibility(user: User = Depends(get_current_student), db: Session = Depends(get_db)):
    return student_service.check_eligibility(db, user)


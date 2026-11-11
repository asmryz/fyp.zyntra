"""
Admin CRUD for programs and scholarships, and editing of general website
content (website content blocks can only be viewed and edited, not added or
deleted). Each endpoint checks the user's module permission through `module_access`.
"""
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.constants import PHONE_PATTERN, QUALIFICATIONS, SITE_CONTENT_KEYS
from app.core.permissions import ModuleAccess, ensure_can_edit, ensure_can_view, module_access, visible_records
from app.models import Program, Scholarship, SiteContent
from app.schemas.auth import MessageResponse
from app.schemas.content import (
    ProgramAdminOut, ProgramIn, ScholarshipAdminOut, ScholarshipIn, SiteContentAdminOut, SiteContentUpdate,
)
from app.services.content_service import apply_changes, audit_content, to_admin_out, unique_slug

router = APIRouter(prefix="/api/admin", tags=["Admin: content"])


# ---------- Programs ----------

def check_program_qualifications(values: list[str], current: list[str] | None = None):
    """
    Accepted qualifications must come from the standard list. When a program is
    edited, values it already stores are also kept, so programs whose
    qualifications were entered outside the dashboard (e.g. directly in the
    database) can still be saved without losing that data.
    """
    allowed = set(QUALIFICATIONS) | set(current or [])
    unknown = [value for value in values if value not in allowed]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown accepted qualification: {', '.join(unknown)}",
        )


@router.get("/programs", response_model=list[ProgramAdminOut])
def list_programs(access: ModuleAccess = Depends(module_access("programs")), db: Session = Depends(get_db)):
    query = visible_records(db.query(Program), Program, access).order_by(Program.sort_order, Program.name)
    return [to_admin_out(ProgramAdminOut, program, access) for program in query.all()]


@router.get("/programs/{program_id}", response_model=ProgramAdminOut)
def get_program(program_id: int, access: ModuleAccess = Depends(module_access("programs")), db: Session = Depends(get_db)):
    program = db.get(Program, program_id)
    ensure_can_view(access, program)
    return to_admin_out(ProgramAdminOut, program, access)


@router.post("/programs", response_model=ProgramAdminOut, status_code=201)
def create_program(
    data: ProgramIn,
    access: ModuleAccess = Depends(module_access("programs", need_write=True)),
    db: Session = Depends(get_db),
):
    check_program_qualifications(data.accepted_qualifications)
    program = Program(**data.model_dump(), slug=unique_slug(db, Program, data.name))
    program.created_by_id = access.user.id
    program.updated_by_id = access.user.id
    db.add(program)
    db.flush()
    audit_content(db, access, "program.created", "program", program.id, f"Created program '{program.name}'")
    db.commit()
    return to_admin_out(ProgramAdminOut, program, access)


@router.put("/programs/{program_id}", response_model=ProgramAdminOut)
def update_program(
    program_id: int,
    data: ProgramIn,
    access: ModuleAccess = Depends(module_access("programs", need_write=True)),
    db: Session = Depends(get_db),
):
    program = db.get(Program, program_id)
    ensure_can_edit(access, program)
    check_program_qualifications(data.accepted_qualifications, program.accepted_qualifications)
    if data.name != program.name:
        program.slug = unique_slug(db, Program, data.name, exclude_id=program.id)
    apply_changes(program, data.model_dump())
    program.updated_by_id = access.user.id
    audit_content(db, access, "program.updated", "program", program.id, f"Updated program '{program.name}'")
    db.commit()
    return to_admin_out(ProgramAdminOut, program, access)


@router.delete("/programs/{program_id}", response_model=MessageResponse)
def delete_program(
    program_id: int,
    access: ModuleAccess = Depends(module_access("programs", need_write=True)),
    db: Session = Depends(get_db),
):
    program = db.get(Program, program_id)
    ensure_can_edit(access, program)
    # Linked roadmaps and student preferences are kept; their program link is cleared (ON DELETE SET NULL)
    audit_content(db, access, "program.deleted", "program", program.id, f"Deleted program '{program.name}'")
    db.delete(program)
    db.commit()
    return {"message": "Program deleted."}


# ---------- Scholarships ----------

@router.get("/scholarships", response_model=list[ScholarshipAdminOut])
def list_scholarships(access: ModuleAccess = Depends(module_access("scholarships")), db: Session = Depends(get_db)):
    query = visible_records(db.query(Scholarship), Scholarship, access)
    query = query.order_by(Scholarship.sort_order, Scholarship.title)
    return [to_admin_out(ScholarshipAdminOut, item, access) for item in query.all()]


@router.get("/scholarships/{scholarship_id}", response_model=ScholarshipAdminOut)
def get_scholarship(
    scholarship_id: int, access: ModuleAccess = Depends(module_access("scholarships")), db: Session = Depends(get_db),
):
    scholarship = db.get(Scholarship, scholarship_id)
    ensure_can_view(access, scholarship)
    return to_admin_out(ScholarshipAdminOut, scholarship, access)


@router.post("/scholarships", response_model=ScholarshipAdminOut, status_code=201)
def create_scholarship(
    data: ScholarshipIn,
    access: ModuleAccess = Depends(module_access("scholarships", need_write=True)),
    db: Session = Depends(get_db),
):
    scholarship = Scholarship(**data.model_dump())
    scholarship.created_by_id = access.user.id
    scholarship.updated_by_id = access.user.id
    db.add(scholarship)
    db.flush()
    audit_content(db, access, "scholarship.created", "scholarship", scholarship.id,
                  f"Created scholarship '{scholarship.title}'")
    db.commit()
    return to_admin_out(ScholarshipAdminOut, scholarship, access)


@router.put("/scholarships/{scholarship_id}", response_model=ScholarshipAdminOut)
def update_scholarship(
    scholarship_id: int,
    data: ScholarshipIn,
    access: ModuleAccess = Depends(module_access("scholarships", need_write=True)),
    db: Session = Depends(get_db),
):
    scholarship = db.get(Scholarship, scholarship_id)
    ensure_can_edit(access, scholarship)
    apply_changes(scholarship, data.model_dump())
    scholarship.updated_by_id = access.user.id
    audit_content(db, access, "scholarship.updated", "scholarship", scholarship.id,
                  f"Updated scholarship '{scholarship.title}'")
    db.commit()
    return to_admin_out(ScholarshipAdminOut, scholarship, access)


@router.delete("/scholarships/{scholarship_id}", response_model=MessageResponse)
def delete_scholarship(
    scholarship_id: int,
    access: ModuleAccess = Depends(module_access("scholarships", need_write=True)),
    db: Session = Depends(get_db),
):
    scholarship = db.get(Scholarship, scholarship_id)
    ensure_can_edit(access, scholarship)
    audit_content(db, access, "scholarship.deleted", "scholarship", scholarship.id,
                  f"Deleted scholarship '{scholarship.title}'")
    db.delete(scholarship)
    db.commit()
    return {"message": "Scholarship deleted."}


# ---------- General website content ----------

def site_content_out(record, access):
    return to_admin_out(SiteContentAdminOut, record, access, used_on=SITE_CONTENT_KEYS.get(record.key))


@router.get("/site-content", response_model=list[SiteContentAdminOut])
def list_site_content(access: ModuleAccess = Depends(module_access("site_content")), db: Session = Depends(get_db)):
    query = visible_records(db.query(SiteContent), SiteContent, access).order_by(SiteContent.key)
    return [site_content_out(item, access) for item in query.all()]


@router.put("/site-content/{content_id}", response_model=SiteContentAdminOut)
def update_site_content(
    content_id: int,
    data: SiteContentUpdate,
    access: ModuleAccess = Depends(module_access("site_content", need_write=True)),
    db: Session = Depends(get_db),
):
    record = db.get(SiteContent, content_id)
    ensure_can_edit(access, record)
    if record.key == "contact_phone" and not re.fullmatch(PHONE_PATTERN, data.body):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Enter the phone number only: 7 to 15 digits, optionally starting with + for the country code "
                   "(no spaces, dashes or other text).",
        )
    # The key (which website section the block belongs to) is fixed
    apply_changes(record, data.model_dump())
    record.updated_by_id = access.user.id
    audit_content(db, access, "site_content.updated", "site_content", record.id, f"Updated website content '{record.key}'")
    db.commit()
    return site_content_out(record, access)


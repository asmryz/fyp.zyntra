"""Public endpoints (no login needed). Only published content is returned."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.constants import (
    ACCESS_LEVEL_LABELS, CONTENT_MODULES, QUALIFICATIONS, RESOURCE_TYPES, ROADMAP_BRANCH_COLORS, ROADMAP_SECTION_TYPES,
    SITE_CONTENT_KEYS, Status,
)
from app.models import Program, SiteContent
from app.schemas.content import ProgramPublicOut, RoadmapLink

router = APIRouter(prefix="/api/public", tags=["Public"])


def program_public_out(program: Program) -> ProgramPublicOut:
    out = ProgramPublicOut.model_validate(program)
    out.roadmaps = [
        RoadmapLink.model_validate(roadmap) for roadmap in program.roadmaps if roadmap.status == Status.PUBLISHED
    ]
    return out


@router.get("/programs", response_model=list[ProgramPublicOut])
def list_programs(db: Session = Depends(get_db)):
    programs = (
        db.query(Program).filter(Program.status == Status.PUBLISHED).order_by(Program.sort_order, Program.name).all()
    )
    return [program_public_out(program) for program in programs]


@router.get("/programs/{slug}", response_model=ProgramPublicOut)
def get_program(slug: str, db: Session = Depends(get_db)):
    program = db.query(Program).filter(Program.slug == slug, Program.status == Status.PUBLISHED).first()
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This program is not available.")
    return program_public_out(program)


@router.get("/site-content")
def site_content(db: Session = Depends(get_db)):
    """Published content blocks as {key: {title, body}} for the landing page and footer."""
    blocks = db.query(SiteContent).filter(SiteContent.status == Status.PUBLISHED).all()
    return {block.key: {"title": block.title, "body": block.body} for block in blocks}


@router.get("/form-options")
def form_options():
    """Fixed lists used by forms in the React app, defined once in app/constants.py."""
    return {
        "qualifications": QUALIFICATIONS,
        "content_modules": CONTENT_MODULES,
        "access_levels": ACCESS_LEVEL_LABELS,
        "roadmap_section_types": ROADMAP_SECTION_TYPES,
        "roadmap_branch_colors": ROADMAP_BRANCH_COLORS,
        "resource_types": RESOURCE_TYPES,
        "site_content_keys": SITE_CONTENT_KEYS,
    }


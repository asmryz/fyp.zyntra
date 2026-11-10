"""
Read-only institutional content for logged-in students.
Only published records are returned; there are no create/edit endpoints here.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.constants import Status
from app.core.dependencies import get_current_user
from app.models import Roadmap, Scholarship, TestSubject, TestTopic, User
from app.schemas.content import RoadmapBranchOut, RoadmapPublicDetailOut, RoadmapPublicOut, ScholarshipPublicOut
from app.schemas.test_prep import (
    ResourceOut, StudentSubjectDetailOut, StudentSubjectOut, StudentTopicDetailOut, StudentTopicSummary,
)

router = APIRouter(prefix="/api/content", tags=["Student content (read-only)"])

PUBLISHED = Status.PUBLISHED


def not_found(label):
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"This {label} is not available.")


# ---------- Scholarships ----------

@router.get("/scholarships", response_model=list[ScholarshipPublicOut])
def list_scholarships(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Scholarship).filter(Scholarship.status == PUBLISHED)
        .order_by(Scholarship.sort_order, Scholarship.title).all()
    )


@router.get("/scholarships/{scholarship_id}", response_model=ScholarshipPublicOut)
def get_scholarship(scholarship_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id, Scholarship.status == PUBLISHED).first()
    if scholarship is None:
        raise not_found("scholarship")
    return scholarship


# ---------- Roadmaps ----------

def roadmap_public_out(roadmap: Roadmap, schema=RoadmapPublicOut):
    out = schema.model_validate(roadmap)
    out.program_name = roadmap.program.name if roadmap.program and roadmap.program.status == PUBLISHED else None
    out.branch_count = len(roadmap.branches)
    out.node_count = sum(len(branch.nodes) for branch in roadmap.branches)
    return out


@router.get("/roadmaps", response_model=list[RoadmapPublicOut])
def list_roadmaps(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmaps = db.query(Roadmap).filter(Roadmap.status == PUBLISHED).order_by(Roadmap.title).all()
    return [roadmap_public_out(roadmap) for roadmap in roadmaps]


@router.get("/roadmaps/{roadmap_id}", response_model=RoadmapPublicDetailOut)
def get_roadmap(roadmap_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.status == PUBLISHED).first()
    if roadmap is None:
        raise not_found("roadmap")
    out = roadmap_public_out(roadmap, schema=RoadmapPublicDetailOut)
    out.branches = [RoadmapBranchOut.model_validate(branch) for branch in roadmap.branches]
    return out


# ---------- Test preparation ----------

def published_topics(subject: TestSubject):
    return [topic for topic in subject.topics if topic.status == PUBLISHED]


@router.get("/test-prep/subjects", response_model=list[StudentSubjectOut])
def list_subjects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subjects = (
        db.query(TestSubject).filter(TestSubject.status == PUBLISHED)
        .order_by(TestSubject.sort_order, TestSubject.name).all()
    )
    result = []
    for subject in subjects:
        out = StudentSubjectOut.model_validate(subject)
        out.topic_count = len(published_topics(subject))
        result.append(out)
    return result


@router.get("/test-prep/subjects/{subject_id}", response_model=StudentSubjectDetailOut)
def get_subject(subject_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = db.query(TestSubject).filter(TestSubject.id == subject_id, TestSubject.status == PUBLISHED).first()
    if subject is None:
        raise not_found("subject")

    topics = published_topics(subject)
    topic_ids = {topic.id for topic in topics}
    out = StudentSubjectDetailOut.model_validate(subject)
    out.topics = [StudentTopicSummary.model_validate(topic) for topic in topics]
    out.topic_count = len(topics)
    # Subject-wide resources plus resources of published topics
    out.resources = [
        ResourceOut.model_validate(resource) for resource in subject.resources
        if resource.topic_id is None or resource.topic_id in topic_ids
    ]
    return out


@router.get("/test-prep/topics/{topic_id}", response_model=StudentTopicDetailOut)
def get_topic(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = (
        db.query(TestTopic).join(TestSubject)
        .filter(TestTopic.id == topic_id, TestTopic.status == PUBLISHED, TestSubject.status == PUBLISHED).first()
    )
    if topic is None:
        raise not_found("topic")
    return StudentTopicDetailOut(
        id=topic.id,
        subject_id=topic.subject_id,
        subject_name=topic.subject.name,
        title=topic.title,
        explanation=topic.explanation,
        resources=[ResourceOut.model_validate(resource) for resource in topic.resources],
    )

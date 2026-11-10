"""
Admin CRUD for test preparation: subjects, topics and learning resources
(videos, links, past papers). Permission ownership is checked on the subject.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from app.core.permissions import ModuleAccess, ensure_can_edit, ensure_can_view, module_access, visible_records
from app.core.security import utcnow
from app.models import LearningResource, TestSubject, TestTopic
from app.schemas.auth import MessageResponse
from app.schemas.test_prep import (
    ResourceIn, ResourceOut, SubjectAdminDetailOut, SubjectAdminOut, SubjectIn, TopicAdminDetailOut, TopicIn, TopicOut,
)
from app.services.content_service import apply_changes, audit_content, get_or_404, to_admin_out

router = APIRouter(prefix="/api/admin/test-prep", tags=["Admin: test preparation"])

MODULE = "test_prep"


def subject_counts(db: Session) -> dict:
    """Return {subject_id: (topics, resources)}."""
    topics = db.query(TestTopic.subject_id, func.count(TestTopic.id)).group_by(TestTopic.subject_id)
    resources = db.query(LearningResource.subject_id, func.count(LearningResource.id)).group_by(LearningResource.subject_id)
    topic_map, resource_map = dict(topics.all()), dict(resources.all())
    ids = set(topic_map) | set(resource_map)
    return {sid: (topic_map.get(sid, 0), resource_map.get(sid, 0)) for sid in ids}


def subject_out(subject, access, counts, schema=SubjectAdminOut):
    topic_count, resource_count = counts.get(subject.id, (0, 0))
    return to_admin_out(schema, subject, access, topic_count=topic_count, resource_count=resource_count)


def topic_out(topic) -> TopicOut:
    return TopicOut.model_validate(topic)


def check_topic_title_free(db: Session, subject_id: int, title: str, topic_id: int | None = None):
    """A title can be used once per subject (also enforced by uq_test_topics_subject_title)."""
    query = db.query(TestTopic.id).filter(TestTopic.subject_id == subject_id, TestTopic.title == title)
    if topic_id is not None:
        query = query.filter(TestTopic.id != topic_id)
    if query.first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="This subject already has a topic with this title.")


def touch_subject(subject: TestSubject, access: ModuleAccess):
    subject.updated_by_id = access.user.id
    subject.updated_at = utcnow()


# ---------- Subjects ----------

@router.get("/subjects", response_model=list[SubjectAdminOut])
def list_subjects(access: ModuleAccess = Depends(module_access(MODULE)), db: Session = Depends(get_db)):
    counts = subject_counts(db)
    query = visible_records(db.query(TestSubject), TestSubject, access).order_by(TestSubject.sort_order, TestSubject.name)
    return [subject_out(subject, access, counts) for subject in query.all()]


@router.get("/subjects/{subject_id}", response_model=SubjectAdminDetailOut)
def get_subject(subject_id: int, access: ModuleAccess = Depends(module_access(MODULE)), db: Session = Depends(get_db)):
    subject = db.get(TestSubject, subject_id)
    ensure_can_view(access, subject)
    out = subject_out(subject, access, subject_counts(db), schema=SubjectAdminDetailOut)
    out.topics = [topic_out(topic) for topic in subject.topics]
    out.resources = [ResourceOut.model_validate(resource) for resource in subject.resources]
    return out


@router.post("/subjects", response_model=SubjectAdminOut, status_code=201)
def create_subject(
    data: SubjectIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    subject = TestSubject(**data.model_dump(), created_by_id=access.user.id, updated_by_id=access.user.id)
    db.add(subject)
    db.flush()
    audit_content(db, access, "test_subject.created", "test_subject", subject.id, f"Created test subject '{subject.name}'")
    db.commit()
    return subject_out(subject, access, {})


@router.put("/subjects/{subject_id}", response_model=SubjectAdminOut)
def update_subject(
    subject_id: int,
    data: SubjectIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    subject = db.get(TestSubject, subject_id)
    ensure_can_edit(access, subject)
    apply_changes(subject, data.model_dump())
    subject.updated_by_id = access.user.id
    audit_content(db, access, "test_subject.updated", "test_subject", subject.id, f"Updated test subject '{subject.name}'")
    db.commit()
    return subject_out(subject, access, subject_counts(db))


@router.delete("/subjects/{subject_id}", response_model=MessageResponse)
def delete_subject(
    subject_id: int,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    subject = db.get(TestSubject, subject_id)
    ensure_can_edit(access, subject)
    audit_content(db, access, "test_subject.deleted", "test_subject", subject.id, f"Deleted test subject '{subject.name}'")
    db.delete(subject)  # topics and resources are deleted too
    db.commit()
    return {"message": "Subject deleted."}


# ---------- Topics ----------

@router.post("/subjects/{subject_id}/topics", response_model=TopicOut, status_code=201)
def create_topic(
    subject_id: int,
    data: TopicIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    subject = db.get(TestSubject, subject_id)
    ensure_can_edit(access, subject)
    check_topic_title_free(db, subject.id, data.title)
    topic = TestTopic(subject_id=subject.id, **data.model_dump())
    db.add(topic)
    touch_subject(subject, access)
    db.flush()
    audit_content(db, access, "test_topic.created", "test_subject", subject.id,
                  f"Added topic '{topic.title}' to '{subject.name}'")
    db.commit()
    return topic_out(topic)


@router.get("/topics/{topic_id}", response_model=TopicAdminDetailOut)
def get_topic(topic_id: int, access: ModuleAccess = Depends(module_access(MODULE)), db: Session = Depends(get_db)):
    topic = get_or_404(db, TestTopic, topic_id, "Topic")
    ensure_can_view(access, topic.subject)
    return TopicAdminDetailOut(**topic_out(topic).model_dump(), subject_name=topic.subject.name)


@router.put("/topics/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: int,
    data: TopicIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    topic = get_or_404(db, TestTopic, topic_id, "Topic")
    ensure_can_edit(access, topic.subject)
    check_topic_title_free(db, topic.subject_id, data.title, topic.id)
    apply_changes(topic, data.model_dump())
    touch_subject(topic.subject, access)
    audit_content(db, access, "test_topic.updated", "test_subject", topic.subject_id, f"Updated topic '{topic.title}'")
    db.commit()
    return topic_out(topic)


@router.delete("/topics/{topic_id}", response_model=MessageResponse)
def delete_topic(
    topic_id: int,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    topic = get_or_404(db, TestTopic, topic_id, "Topic")
    ensure_can_edit(access, topic.subject)
    touch_subject(topic.subject, access)
    audit_content(db, access, "test_topic.deleted", "test_subject", topic.subject_id, f"Deleted topic '{topic.title}'")
    db.delete(topic)
    db.commit()
    return {"message": "Topic deleted."}


# ---------- Learning resources (videos, links, past papers) ----------

def check_topic_in_subject(db: Session, subject: TestSubject, topic_id: int | None):
    if topic_id is None:
        return
    topic = db.get(TestTopic, topic_id)
    if topic is None or topic.subject_id != subject.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected topic is not part of this subject.")


@router.post("/subjects/{subject_id}/resources", response_model=ResourceOut, status_code=201)
def create_resource(
    subject_id: int,
    data: ResourceIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    subject = db.get(TestSubject, subject_id)
    ensure_can_edit(access, subject)
    check_topic_in_subject(db, subject, data.topic_id)
    resource = LearningResource(subject_id=subject.id, **data.model_dump())
    db.add(resource)
    touch_subject(subject, access)
    db.flush()
    audit_content(db, access, "learning_resource.created", "test_subject", subject.id,
                  f"Added resource '{resource.title}' to '{subject.name}'")
    db.commit()
    return resource


@router.put("/resources/{resource_id}", response_model=ResourceOut)
def update_resource(
    resource_id: int,
    data: ResourceIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    resource = get_or_404(db, LearningResource, resource_id, "Resource")
    ensure_can_edit(access, resource.subject)
    check_topic_in_subject(db, resource.subject, data.topic_id)
    apply_changes(resource, data.model_dump())
    touch_subject(resource.subject, access)
    audit_content(db, access, "learning_resource.updated", "test_subject", resource.subject_id,
                  f"Updated resource '{resource.title}'")
    db.commit()
    return resource


@router.delete("/resources/{resource_id}", response_model=MessageResponse)
def delete_resource(
    resource_id: int,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    resource = get_or_404(db, LearningResource, resource_id, "Resource")
    ensure_can_edit(access, resource.subject)
    touch_subject(resource.subject, access)
    audit_content(db, access, "learning_resource.deleted", "test_subject", resource.subject_id,
                  f"Deleted resource '{resource.title}'")
    db.delete(resource)
    db.commit()
    return {"message": "Resource deleted."}


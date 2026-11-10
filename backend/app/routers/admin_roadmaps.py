"""
Admin CRUD for roadmaps: the roadmap (central heading), its branches
(coloured columns) and each branch's steps with their detail sections.
Edit rights for branches and steps are checked on the roadmap they belong to.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from app.core.permissions import ModuleAccess, ensure_can_edit, ensure_can_view, module_access, visible_records
from app.core.security import utcnow
from app.models import Program, Roadmap, RoadmapBranch, RoadmapNode, RoadmapNodeSection
from app.schemas.auth import MessageResponse
from app.schemas.content import (
    ReorderIn, RoadmapAdminDetailOut, RoadmapAdminOut, RoadmapBranchIn, RoadmapBranchOut, RoadmapIn, RoadmapNodeIn,
    RoadmapNodeOut,
)
from app.services.content_service import apply_changes, audit_content, get_or_404, to_admin_out

router = APIRouter(prefix="/api/admin", tags=["Admin: roadmaps"])

MODULE = "roadmaps"


def roadmap_counts(db: Session) -> dict:
    """Return {roadmap_id: (branches, steps)}."""
    branches = dict(
        db.query(RoadmapBranch.roadmap_id, func.count(RoadmapBranch.id)).group_by(RoadmapBranch.roadmap_id).all()
    )
    nodes = dict(
        db.query(RoadmapBranch.roadmap_id, func.count(RoadmapNode.id))
        .join(RoadmapNode, RoadmapNode.branch_id == RoadmapBranch.id)
        .group_by(RoadmapBranch.roadmap_id).all()
    )
    return {rid: (branches.get(rid, 0), nodes.get(rid, 0)) for rid in set(branches) | set(nodes)}


def roadmap_out(roadmap, access, counts, schema=RoadmapAdminOut):
    branch_count, node_count = counts.get(roadmap.id, (0, 0))
    return to_admin_out(
        schema, roadmap, access,
        program_name=roadmap.program.name if roadmap.program else None,
        branch_count=branch_count,
        node_count=node_count,
    )


def check_program_exists(db: Session, program_id: int | None):
    if program_id is not None and db.get(Program, program_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected program does not exist.")


def touch_roadmap(roadmap: Roadmap, access: ModuleAccess):
    """Record who last changed the roadmap when one of its branches or steps changes."""
    roadmap.updated_by_id = access.user.id
    roadmap.updated_at = utcnow()


def apply_order(items, ids: list[int], label: str):
    """Set positions from a complete, ordered list of ids."""
    by_id = {item.id: item for item in items}
    if len(ids) != len(set(ids)) or set(ids) != set(by_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Send every {label} of this list exactly once.")
    for position, item_id in enumerate(ids):
        by_id[item_id].position = position


# ---------- Roadmaps ----------

@router.get("/roadmaps", response_model=list[RoadmapAdminOut])
def list_roadmaps(access: ModuleAccess = Depends(module_access(MODULE)), db: Session = Depends(get_db)):
    counts = roadmap_counts(db)
    query = visible_records(db.query(Roadmap), Roadmap, access).order_by(Roadmap.title)
    return [roadmap_out(roadmap, access, counts) for roadmap in query.all()]


@router.get("/roadmaps/{roadmap_id}", response_model=RoadmapAdminDetailOut)
def get_roadmap(roadmap_id: int, access: ModuleAccess = Depends(module_access(MODULE)), db: Session = Depends(get_db)):
    roadmap = db.get(Roadmap, roadmap_id)
    ensure_can_view(access, roadmap)
    out = roadmap_out(roadmap, access, roadmap_counts(db), schema=RoadmapAdminDetailOut)
    out.branches = [RoadmapBranchOut.model_validate(branch) for branch in roadmap.branches]
    return out


@router.post("/roadmaps", response_model=RoadmapAdminOut, status_code=201)
def create_roadmap(
    data: RoadmapIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    check_program_exists(db, data.program_id)
    roadmap = Roadmap(**data.model_dump(), created_by_id=access.user.id, updated_by_id=access.user.id)
    db.add(roadmap)
    db.flush()
    audit_content(db, access, "roadmap.created", "roadmap", roadmap.id, f"Created roadmap '{roadmap.title}'")
    db.commit()
    return roadmap_out(roadmap, access, {})


@router.put("/roadmaps/{roadmap_id}", response_model=RoadmapAdminOut)
def update_roadmap(
    roadmap_id: int,
    data: RoadmapIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    roadmap = db.get(Roadmap, roadmap_id)
    ensure_can_edit(access, roadmap)
    check_program_exists(db, data.program_id)
    apply_changes(roadmap, data.model_dump())
    roadmap.updated_by_id = access.user.id
    audit_content(db, access, "roadmap.updated", "roadmap", roadmap.id, f"Updated roadmap '{roadmap.title}'")
    db.commit()
    return roadmap_out(roadmap, access, roadmap_counts(db))


@router.delete("/roadmaps/{roadmap_id}", response_model=MessageResponse)
def delete_roadmap(
    roadmap_id: int,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    roadmap = db.get(Roadmap, roadmap_id)
    ensure_can_edit(access, roadmap)
    audit_content(db, access, "roadmap.deleted", "roadmap", roadmap.id, f"Deleted roadmap '{roadmap.title}'")
    db.delete(roadmap)  # branches, steps and sections are deleted too (ON DELETE CASCADE)
    db.commit()
    return {"message": "Roadmap deleted."}


# ---------- Branches ----------

def editable_branch(db: Session, access: ModuleAccess, branch_id: int) -> RoadmapBranch:
    branch = get_or_404(db, RoadmapBranch, branch_id, "Branch")
    ensure_can_edit(access, branch.roadmap)
    return branch


@router.post("/roadmaps/{roadmap_id}/branches", response_model=RoadmapBranchOut, status_code=201)
def create_branch(
    roadmap_id: int,
    data: RoadmapBranchIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    roadmap = db.get(Roadmap, roadmap_id)
    ensure_can_edit(access, roadmap)
    position = max((branch.position for branch in roadmap.branches), default=-1) + 1
    branch = RoadmapBranch(roadmap_id=roadmap.id, position=position, **data.model_dump())
    db.add(branch)
    touch_roadmap(roadmap, access)
    db.flush()
    audit_content(db, access, "roadmap.branch_added", "roadmap", roadmap.id,
                  f"Added branch '{branch.name}' to roadmap '{roadmap.title}'")
    db.commit()
    db.refresh(branch)
    return branch


@router.put("/roadmap-branches/{branch_id}", response_model=RoadmapBranchOut)
def update_branch(
    branch_id: int,
    data: RoadmapBranchIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    branch = editable_branch(db, access, branch_id)
    apply_changes(branch, data.model_dump())
    touch_roadmap(branch.roadmap, access)
    audit_content(db, access, "roadmap.branch_updated", "roadmap", branch.roadmap_id,
                  f"Updated branch '{branch.name}' on roadmap '{branch.roadmap.title}'")
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/roadmap-branches/{branch_id}", response_model=MessageResponse)
def delete_branch(
    branch_id: int,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    branch = editable_branch(db, access, branch_id)
    touch_roadmap(branch.roadmap, access)
    audit_content(db, access, "roadmap.branch_deleted", "roadmap", branch.roadmap_id,
                  f"Deleted branch '{branch.name}' from roadmap '{branch.roadmap.title}'")
    db.delete(branch)  # its steps and their sections are deleted too
    db.commit()
    return {"message": "Branch deleted."}


@router.put("/roadmaps/{roadmap_id}/branches/order", response_model=list[RoadmapBranchOut])
def reorder_branches(
    roadmap_id: int,
    data: ReorderIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    roadmap = db.get(Roadmap, roadmap_id)
    ensure_can_edit(access, roadmap)
    apply_order(roadmap.branches, data.ids, "branch")
    touch_roadmap(roadmap, access)
    audit_content(db, access, "roadmap.branches_reordered", "roadmap", roadmap.id,
                  f"Reordered the branches of roadmap '{roadmap.title}'")
    db.commit()
    db.refresh(roadmap)
    return roadmap.branches


# ---------- Steps (nodes) and their detail sections ----------

def editable_node(db: Session, access: ModuleAccess, node_id: int) -> RoadmapNode:
    node = get_or_404(db, RoadmapNode, node_id, "Roadmap step")
    ensure_can_edit(access, node.branch.roadmap)
    return node


def save_node_fields(db: Session, node: RoadmapNode, data: RoadmapNodeIn, roadmap: Roadmap):
    node.title = data.title
    node.description = data.description
    node.sections = [
        RoadmapNodeSection(section_title=section.section_title, section_type=section.section_type,
                           content=section.content, position=index)
        for index, section in enumerate(data.sections)
    ]
    node.is_default = data.is_default
    if data.is_default:
        # Only one step per roadmap can be the one selected when the roadmap opens
        branch_ids = [branch.id for branch in roadmap.branches]
        query = db.query(RoadmapNode).filter(RoadmapNode.branch_id.in_(branch_ids), RoadmapNode.is_default.is_(True))
        if node.id is not None:
            query = query.filter(RoadmapNode.id != node.id)
        query.update({RoadmapNode.is_default: False}, synchronize_session=False)


@router.post("/roadmap-branches/{branch_id}/nodes", response_model=RoadmapNodeOut, status_code=201)
def create_node(
    branch_id: int,
    data: RoadmapNodeIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    branch = editable_branch(db, access, branch_id)
    roadmap = branch.roadmap
    position = max((node.position for node in branch.nodes), default=-1) + 1
    node = RoadmapNode(branch_id=branch.id, position=position)
    save_node_fields(db, node, data, roadmap)
    db.add(node)
    touch_roadmap(roadmap, access)
    db.flush()
    audit_content(db, access, "roadmap.node_added", "roadmap", roadmap.id,
                  f"Added step '{node.title}' to branch '{branch.name}' on roadmap '{roadmap.title}'")
    db.commit()
    db.refresh(node)
    return node


@router.put("/roadmap-nodes/{node_id}", response_model=RoadmapNodeOut)
def update_node(
    node_id: int,
    data: RoadmapNodeIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    node = editable_node(db, access, node_id)
    roadmap = node.branch.roadmap
    save_node_fields(db, node, data, roadmap)
    touch_roadmap(roadmap, access)
    audit_content(db, access, "roadmap.node_updated", "roadmap", roadmap.id,
                  f"Updated step '{node.title}' on roadmap '{roadmap.title}'")
    db.commit()
    db.refresh(node)
    return node


@router.delete("/roadmap-nodes/{node_id}", response_model=MessageResponse)
def delete_node(
    node_id: int,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    node = editable_node(db, access, node_id)
    roadmap = node.branch.roadmap
    touch_roadmap(roadmap, access)
    audit_content(db, access, "roadmap.node_deleted", "roadmap", roadmap.id,
                  f"Deleted step '{node.title}' from roadmap '{roadmap.title}'")
    db.delete(node)  # its sections are deleted too
    db.commit()
    return {"message": "Step deleted."}


@router.put("/roadmap-branches/{branch_id}/nodes/order", response_model=RoadmapBranchOut)
def reorder_nodes(
    branch_id: int,
    data: ReorderIn,
    access: ModuleAccess = Depends(module_access(MODULE, need_write=True)),
    db: Session = Depends(get_db),
):
    branch = editable_branch(db, access, branch_id)
    apply_order(branch.nodes, data.ids, "step")
    touch_roadmap(branch.roadmap, access)
    audit_content(db, access, "roadmap.nodes_reordered", "roadmap", branch.roadmap_id,
                  f"Reordered the steps of branch '{branch.name}' on roadmap '{branch.roadmap.title}'")
    db.commit()
    db.refresh(branch)
    return branch

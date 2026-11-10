"""roadmap branches, steps and detail sections

Replaces the tree of roadmap nodes (parent_id) with:
    roadmaps -> roadmap_branches -> roadmap_nodes -> roadmap_node_sections

Existing roadmap content is moved, not deleted:
- every top-level node becomes a branch (name, description, a colour from
  the default palette); links on a top-level node are added to the branch
  description
- every node below it becomes a step of that branch, in the order it was
  shown (depth-first by sort order)
- each step gets a "Category" text section recording its old node type,
  the node it was connected to (when it was nested deeper) and whether it
  was optional; its links become a "Learning Resources" links section
If any node cannot be placed in a branch the migration stops and nothing
is changed (PostgreSQL runs the whole migration in one transaction).

Revision ID: b7e5f0a2c913
Revises: a3d91c27b4e1
Create Date: 2026-11-02 12:00:00.000000

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7e5f0a2c913'
down_revision: Union[str, Sequence[str], None] = 'a3d91c27b4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PALETTE = ["#2563EB", "#16A34A", "#9333EA", "#EA580C", "#DB2777", "#DC2626"]
OLD_TYPE_LABELS = {
    "stage": "Stage",
    "subject": "Subject",
    "skill": "Skill",
    "specialization": "Specialization",
    "tool": "Tool / Technology",
    "job_role": "Job Role",
    "career": "Career Opportunity",
}


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('roadmap_branches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('roadmap_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('color', sa.String(length=7), server_default='#2563EB', nullable=False),
    sa.Column('position', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roadmap_branches_roadmap_id'), 'roadmap_branches', ['roadmap_id'], unique=False)

    op.add_column('roadmap_nodes', sa.Column('branch_id', sa.Integer(), nullable=True))
    op.add_column('roadmap_nodes', sa.Column('position', sa.Integer(), server_default='0', nullable=False))
    op.add_column('roadmap_nodes', sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False))
    op.create_foreign_key('roadmap_nodes_branch_id_fkey', 'roadmap_nodes', 'roadmap_branches', ['branch_id'], ['id'],
                          ondelete='CASCADE')

    op.create_table('roadmap_node_sections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('node_id', sa.Integer(), nullable=False),
    sa.Column('section_title', sa.String(length=100), nullable=False),
    sa.Column('section_type', sa.String(length=20), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('position', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roadmap_node_sections_node_id'), 'roadmap_node_sections', ['node_id'], unique=False)

    move_tree_into_branches(op.get_bind())

    op.alter_column('roadmap_nodes', 'branch_id', nullable=False)
    op.create_index(op.f('ix_roadmap_nodes_branch_id'), 'roadmap_nodes', ['branch_id'], unique=False)
    op.drop_index(op.f('ix_roadmap_nodes_parent_id'), table_name='roadmap_nodes')
    op.drop_index(op.f('ix_roadmap_nodes_roadmap_id'), table_name='roadmap_nodes')
    op.drop_constraint('roadmap_nodes_parent_id_fkey', 'roadmap_nodes', type_='foreignkey')
    op.drop_constraint('roadmap_nodes_roadmap_id_fkey', 'roadmap_nodes', type_='foreignkey')
    for column in ('roadmap_id', 'parent_id', 'node_type', 'links', 'is_optional', 'sort_order'):
        op.drop_column('roadmap_nodes', column)


def move_tree_into_branches(conn) -> None:
    rows = conn.execute(sa.text(
        "SELECT id, roadmap_id, parent_id, title, node_type, description, links, is_optional, sort_order, "
        "created_at, updated_at FROM roadmap_nodes ORDER BY sort_order, id"
    )).mappings().all()
    nodes = {row["id"]: row for row in rows}
    children = {}
    for row in rows:
        children.setdefault(row["parent_id"], []).append(row)  # already in display order

    placed = set()
    roadmap_ids = sorted({row["roadmap_id"] for row in rows})
    for roadmap_id in roadmap_ids:
        top_level = [row for row in children.get(None, []) if row["roadmap_id"] == roadmap_id]
        for branch_position, top in enumerate(top_level):
            description = top["description"] or ""
            links = top["links"] or []
            if links:
                lines = "\n".join(f"{link.get('label', '')}: {link.get('url', '')}" for link in links)
                description = f"{description}\n\nLinks:\n{lines}".strip()
            branch_id = conn.execute(sa.text(
                "INSERT INTO roadmap_branches (roadmap_id, name, description, color, position, created_at, updated_at) "
                "VALUES (:roadmap_id, :name, :description, :color, :position, :created_at, :updated_at) RETURNING id"
            ), {
                "roadmap_id": roadmap_id, "name": top["title"], "description": description or None,
                "color": PALETTE[branch_position % len(PALETTE)], "position": branch_position,
                "created_at": top["created_at"], "updated_at": top["updated_at"],
            }).scalar_one()
            placed.add(top["id"])

            # Depth-first, so a nested item follows the item it was connected to
            ordered = []

            def walk(parent_id, depth):
                for child in children.get(parent_id, []):
                    ordered.append((child, depth))
                    walk(child["id"], depth + 1)

            walk(top["id"], 1)
            for step_position, (node, depth) in enumerate(ordered):
                conn.execute(sa.text(
                    "UPDATE roadmap_nodes SET branch_id = :branch_id, position = :position WHERE id = :id"
                ), {"branch_id": branch_id, "position": step_position, "id": node["id"]})
                placed.add(node["id"])

                category = OLD_TYPE_LABELS.get(node["node_type"], node["node_type"])
                if depth > 1:
                    category += f" · connected to {nodes[node['parent_id']]['title']}"
                if node["is_optional"]:
                    category += " · optional"
                sections = [("Category", "text", {"text": category})]
                if node["links"]:
                    sections.append(("Learning Resources", "links", {"links": node["links"]}))
                for section_position, (title, section_type, content) in enumerate(sections):
                    conn.execute(sa.text(
                        "INSERT INTO roadmap_node_sections (node_id, section_title, section_type, content, position) "
                        "VALUES (:node_id, :title, :type, CAST(:content AS jsonb), :position)"
                    ), {"node_id": node["id"], "title": title, "type": section_type,
                        "content": json.dumps(content), "position": section_position})

    unplaced = set(nodes) - placed
    if unplaced:
        raise RuntimeError(f"Roadmap nodes {sorted(unplaced)} could not be placed in a branch; nothing was changed.")

    # Top-level nodes are now branches. Detach the tree first so removing
    # them does not cascade to the steps.
    conn.execute(sa.text("UPDATE roadmap_nodes SET parent_id = NULL"))
    conn.execute(sa.text("DELETE FROM roadmap_nodes WHERE branch_id IS NULL"))


def downgrade() -> None:
    """
    Downgrade schema: branches become top-level nodes again and steps become
    their child nodes. Section content other than links is not kept.
    """
    op.add_column('roadmap_nodes', sa.Column('roadmap_id', sa.Integer(), nullable=True))
    op.add_column('roadmap_nodes', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('roadmap_nodes', sa.Column('node_type', sa.String(length=30), server_default='skill', nullable=False))
    op.add_column('roadmap_nodes', sa.Column('links', postgresql.JSONB(astext_type=sa.Text()),
                                             server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column('roadmap_nodes', sa.Column('is_optional', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('roadmap_nodes', sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE roadmap_nodes n SET roadmap_id = b.roadmap_id, sort_order = n.position,
            links = COALESCE((
                SELECT s.content -> 'links' FROM roadmap_node_sections s
                WHERE s.node_id = n.id AND s.section_type = 'links' ORDER BY s.position LIMIT 1
            ), '[]'::jsonb)
        FROM roadmap_branches b WHERE b.id = n.branch_id
    """))
    branches = conn.execute(sa.text(
        "SELECT id, roadmap_id, name, description, position, created_at, updated_at FROM roadmap_branches"
    )).mappings().all()
    for branch in branches:
        parent_id = conn.execute(sa.text(
            "INSERT INTO roadmap_nodes (roadmap_id, branch_id, title, node_type, description, sort_order, "
            "created_at, updated_at) VALUES (:roadmap_id, :branch_id, :title, 'stage', :description, :position, "
            ":created_at, :updated_at) RETURNING id"
        ), {"roadmap_id": branch["roadmap_id"], "branch_id": branch["id"], "title": branch["name"][:150],
            "description": branch["description"], "position": branch["position"],
            "created_at": branch["created_at"], "updated_at": branch["updated_at"]}).scalar_one()
        conn.execute(sa.text(
            "UPDATE roadmap_nodes SET parent_id = :parent_id WHERE branch_id = :branch_id AND id <> :parent_id"
        ), {"parent_id": parent_id, "branch_id": branch["id"]})

    op.alter_column('roadmap_nodes', 'roadmap_id', nullable=False)
    op.create_foreign_key('roadmap_nodes_roadmap_id_fkey', 'roadmap_nodes', 'roadmaps', ['roadmap_id'], ['id'],
                          ondelete='CASCADE')
    op.create_foreign_key('roadmap_nodes_parent_id_fkey', 'roadmap_nodes', 'roadmap_nodes', ['parent_id'], ['id'],
                          ondelete='CASCADE')
    op.create_index(op.f('ix_roadmap_nodes_roadmap_id'), 'roadmap_nodes', ['roadmap_id'], unique=False)
    op.create_index(op.f('ix_roadmap_nodes_parent_id'), 'roadmap_nodes', ['parent_id'], unique=False)

    op.drop_index(op.f('ix_roadmap_node_sections_node_id'), table_name='roadmap_node_sections')
    op.drop_table('roadmap_node_sections')
    op.drop_index(op.f('ix_roadmap_nodes_branch_id'), table_name='roadmap_nodes')
    op.drop_constraint('roadmap_nodes_branch_id_fkey', 'roadmap_nodes', type_='foreignkey')
    op.drop_column('roadmap_nodes', 'is_default')
    op.drop_column('roadmap_nodes', 'position')
    op.drop_column('roadmap_nodes', 'branch_id')
    op.drop_index(op.f('ix_roadmap_branches_roadmap_id'), table_name='roadmap_branches')
    op.drop_table('roadmap_branches')

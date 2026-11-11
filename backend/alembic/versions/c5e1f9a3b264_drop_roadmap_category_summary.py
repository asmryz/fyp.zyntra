"""drop roadmaps.category and roadmaps.summary

The roadmap Category and Short summary fields were removed from ZYNTRA.
Only these two columns of the roadmaps table are dropped; no other column,
table, record or relationship changes. No index, constraint or view uses them.

Before the drop, only roadmap 2 (BS Computer Science Career Roadmap) held
values: category "Career roadmap" and a one-line placeholder summary. They were
backed up to the session scratchpad (roadmaps-category-summary-backup.json).
Downgrade re-adds both columns empty (the dropped values are not restored).

Revision ID: c5e1f9a3b264
Revises: a8d3e5f17c42
Create Date: 2026-11-11 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e1f9a3b264'
down_revision: Union[str, Sequence[str], None] = 'a8d3e5f17c42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('roadmaps', 'category')
    op.drop_column('roadmaps', 'summary')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('roadmaps', sa.Column('summary', sa.String(length=300), nullable=True))
    op.add_column('roadmaps', sa.Column('category', sa.String(length=80), nullable=True))

"""remove academic offerings and contact address website content

The "Academic offerings" block (key szabist_programs_overview) and the
"Contact address" block (key contact_address) were removed from ZYNTRA, so
their site_content rows are deleted. Only these two keys are touched; no
table or column changes.

At the time of the migration only szabist_programs_overview existed, holding
unedited placeholder text; contact_address had already been deleted from the
dashboard. Downgrade puts back the original placeholder rows.

Revision ID: e2c8b41d7a90
Revises: 70e5d3631eb4
Create Date: 2026-11-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2c8b41d7a90'
down_revision: Union[str, Sequence[str], None] = '70e5d3631eb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REMOVED_KEYS = ('szabist_programs_overview', 'contact_address')
PLACEHOLDERS = [
    ('szabist_programs_overview', 'Academic offerings',
     "[Placeholder] Add an overview of SZABIST's faculties and departments here. During FYP-I, ZYNTRA focuses on "
     "Computer Science programs; more programs will be added in FYP-II."),
    ('contact_address', 'Address', '[Placeholder] contact address'),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("DELETE FROM site_content WHERE key IN :keys").bindparams(
        sa.bindparam('keys', value=REMOVED_KEYS, expanding=True)))


def downgrade() -> None:
    """Downgrade schema: restore the placeholder rows if they are missing."""
    for key, title, body in PLACEHOLDERS:
        op.execute(sa.text(
            "INSERT INTO site_content (key, title, body, status) SELECT :key, :title, :body, 'published' "
            "WHERE NOT EXISTS (SELECT 1 FROM site_content WHERE key = :key)"
        ).bindparams(key=key, title=title, body=body))

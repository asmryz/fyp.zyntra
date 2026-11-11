"""program display order must be a whole number from 1 to 1000

Adds ck_programs_sort_order_range and changes the column default from 0 to 1
(0 is no longer a valid display order). The upgrade stops with an error,
without changing anything, if any existing program is outside the range.

Revision ID: f4a6c2d9e815
Revises: e2c8b41d7a90
Create Date: 2026-11-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a6c2d9e815'
down_revision: Union[str, Sequence[str], None] = 'e2c8b41d7a90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bad = op.get_bind().execute(sa.text(
        "SELECT id, name, sort_order FROM programs WHERE sort_order NOT BETWEEN 1 AND 1000"
    )).all()
    if bad:
        listed = ', '.join(f'{row.id} ({row.name}): {row.sort_order}' for row in bad)
        raise RuntimeError(f'Programs with a display order outside 1-1000 must be fixed first: {listed}')
    op.alter_column('programs', 'sort_order', server_default='1')
    op.create_check_constraint('ck_programs_sort_order_range', 'programs', 'sort_order BETWEEN 1 AND 1000')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_programs_sort_order_range', 'programs', type_='check')
    op.alter_column('programs', 'sort_order', server_default='0')

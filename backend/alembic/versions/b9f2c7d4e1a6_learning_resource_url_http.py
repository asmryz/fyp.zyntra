"""learning resource links must be http(s) web addresses

Adds ck_learning_resources_url_http. The API already accepts only http(s)
links; this also protects rows inserted directly in the database (for example
through the Neon SQL editor), so a javascript: or data: URL can never be stored
and rendered as a link. Stops without changing anything if a row breaks it.

Revision ID: b9f2c7d4e1a6
Revises: c5e1f9a3b264
Create Date: 2026-11-11 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9f2c7d4e1a6'
down_revision: Union[str, Sequence[str], None] = 'c5e1f9a3b264'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bad = op.get_bind().execute(sa.text("SELECT id FROM learning_resources WHERE url !~* '^https?://'")).scalars().all()
    if bad:
        raise RuntimeError(f'Learning resources with non-http links must be fixed first: ids {bad}')
    op.create_check_constraint('ck_learning_resources_url_http', 'learning_resources', "url ~* '^https?://'")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_learning_resources_url_http', 'learning_resources', type_='check')

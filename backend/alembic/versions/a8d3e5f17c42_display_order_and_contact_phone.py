"""display order 1-100 on every display order column; contact phone holds the number only

Display order (sort_order) on programs, scholarships, test_subjects,
test_topics and learning_resources must be a whole number from 1 to 100:
CHECK constraints are added (the programs one is narrowed from 1-1000) and the
column defaults change from 0 to 1.

Data changes, both agreed with the project owner:
- the "[Placeholder] Sample Scholarship" (id 3) display order 0 -> 1;
- the website contact phone value ("0333-74273171") is cleared, so the
  correct number can be entered as digits only from the dashboard.

The upgrade stops without changing anything if any other row is outside 1-100.

Revision ID: a8d3e5f17c42
Revises: f4a6c2d9e815
Create Date: 2026-11-11 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8d3e5f17c42'
down_revision: Union[str, Sequence[str], None] = 'f4a6c2d9e815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ('programs', 'scholarships', 'test_subjects', 'test_topics', 'learning_resources')
PHONE_CHECK = "key <> 'contact_phone' OR body = '' OR body ~ '^[+]?[0-9]{7,15}$'"
PREVIOUS_PHONE = '0333-74273171'


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    op.execute("UPDATE scholarships SET sort_order = 1 WHERE id = 3 AND sort_order = 0")
    bad = []
    for table in TABLES:
        rows = bind.execute(sa.text(f"SELECT id, sort_order FROM {table} WHERE sort_order NOT BETWEEN 1 AND 100")).all()
        bad += [f'{table} {row.id}: {row.sort_order}' for row in rows]
    if bad:
        raise RuntimeError('Display order values outside 1-100 must be fixed first: ' + ', '.join(bad))

    op.drop_constraint('ck_programs_sort_order_range', 'programs', type_='check')
    for table in TABLES:
        op.alter_column(table, 'sort_order', server_default='1')
        op.create_check_constraint(f'ck_{table}_sort_order_range', table, 'sort_order BETWEEN 1 AND 100')

    op.execute(sa.text("UPDATE site_content SET body = '' WHERE key = 'contact_phone' AND body = :old").bindparams(
        old=PREVIOUS_PHONE))
    op.create_check_constraint('ck_site_content_contact_phone', 'site_content', PHONE_CHECK)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_site_content_contact_phone', 'site_content', type_='check')
    op.execute(sa.text("UPDATE site_content SET body = :old WHERE key = 'contact_phone' AND body = ''").bindparams(
        old=PREVIOUS_PHONE))
    for table in TABLES:
        op.drop_constraint(f'ck_{table}_sort_order_range', table, type_='check')
        op.alter_column(table, 'sort_order', server_default='0')
    op.alter_column('programs', 'sort_order', server_default='1')
    op.create_check_constraint('ck_programs_sort_order_range', 'programs', 'sort_order BETWEEN 1 AND 1000')

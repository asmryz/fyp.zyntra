"""data integrity constraints

Database-level validation (enforced on every INSERT and UPDATE):

- student_profiles: percentage between 0 and 100; marks not negative;
  obtained_marks not above total_marks. NULLs stay allowed (optional fields).
- programs: min_percentage between 0 and 100 (NULL allowed).
- test_topics: a title can be used once per subject.
- roadmap_nodes / roadmap_node_sections: one item per position. These are
  DEFERRABLE INITIALLY DEFERRED so reordering and replacing sections inside
  one transaction is checked at commit, not row by row.
- learning_resources: resource_type is video, article, pdf or link.
  Existing rows using the earlier types are converted first:
  platform -> link, other -> link, past_paper -> pdf.
- users: email uniqueness is case-insensitive (unique index on lower(email)).
  The old unique index on email becomes a plain lookup index, so there is
  only one uniqueness rule.

Before applying, the data was checked: no existing row violated any of these
rules except one resource stored as 'platform', which is converted.

Revision ID: 70e5d3631eb4
Revises: b7e5f0a2c913
Create Date: 2026-11-07 20:48:08.640076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70e5d3631eb4'
down_revision: Union[str, Sequence[str], None] = 'b7e5f0a2c913'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        'ck_student_profiles_percentage_range', 'student_profiles',
        'percentage IS NULL OR (percentage >= 0 AND percentage <= 100)',
    )
    op.create_check_constraint(
        'ck_student_profiles_marks_not_negative', 'student_profiles',
        '(obtained_marks IS NULL OR obtained_marks >= 0) AND (total_marks IS NULL OR total_marks >= 0)',
    )
    op.create_check_constraint(
        'ck_student_profiles_marks_within_total', 'student_profiles',
        'obtained_marks IS NULL OR total_marks IS NULL OR obtained_marks <= total_marks',
    )
    op.create_check_constraint(
        'ck_programs_min_percentage_range', 'programs',
        'min_percentage IS NULL OR (min_percentage >= 0 AND min_percentage <= 100)',
    )

    op.create_unique_constraint('uq_test_topics_subject_title', 'test_topics', ['subject_id', 'title'])
    op.create_unique_constraint('uq_roadmap_nodes_branch_position', 'roadmap_nodes', ['branch_id', 'position'],
                                deferrable=True, initially='DEFERRED')
    op.create_unique_constraint('uq_roadmap_node_sections_node_position', 'roadmap_node_sections',
                                ['node_id', 'position'], deferrable=True, initially='DEFERRED')

    op.execute("UPDATE learning_resources SET resource_type = 'link' WHERE resource_type IN ('platform', 'other')")
    op.execute("UPDATE learning_resources SET resource_type = 'pdf' WHERE resource_type = 'past_paper'")
    op.create_check_constraint(
        'ck_learning_resources_type', 'learning_resources',
        "resource_type IN ('video', 'article', 'pdf', 'link')",
    )

    # Emails are already stored in lowercase; make it a database rule
    op.execute("UPDATE users SET email = lower(email) WHERE email <> lower(email)")
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index('uq_users_email_lower', 'users', [sa.literal_column('lower(email)')], unique=True)


def downgrade() -> None:
    """Downgrade schema (resource types map back to platform and past_paper)."""
    op.drop_index('uq_users_email_lower', table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.drop_constraint('ck_learning_resources_type', 'learning_resources', type_='check')
    op.execute("UPDATE learning_resources SET resource_type = 'platform' WHERE resource_type = 'link'")
    op.execute("UPDATE learning_resources SET resource_type = 'past_paper' WHERE resource_type = 'pdf'")

    op.drop_constraint('uq_roadmap_node_sections_node_position', 'roadmap_node_sections', type_='unique')
    op.drop_constraint('uq_roadmap_nodes_branch_position', 'roadmap_nodes', type_='unique')
    op.drop_constraint('uq_test_topics_subject_title', 'test_topics', type_='unique')

    op.drop_constraint('ck_programs_min_percentage_range', 'programs', type_='check')
    op.drop_constraint('ck_student_profiles_marks_within_total', 'student_profiles', type_='check')
    op.drop_constraint('ck_student_profiles_marks_not_negative', 'student_profiles', type_='check')
    op.drop_constraint('ck_student_profiles_percentage_range', 'student_profiles', type_='check')

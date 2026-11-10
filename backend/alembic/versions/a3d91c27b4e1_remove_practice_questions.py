"""remove practice questions and mock tests

ZYNTRA no longer runs quizzes or mock tests on the website, so the tables
that only stored multiple-choice questions, their options and student
answers are removed. Subjects, topics and learning resources are kept.

Revision ID: a3d91c27b4e1
Revises: 5cefee3cf282
Create Date: 2026-11-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3d91c27b4e1'
down_revision: Union[str, Sequence[str], None] = '5cefee3cf282'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f('ix_practice_attempts_user_id'), table_name='practice_attempts')
    op.drop_index(op.f('ix_practice_attempts_question_id'), table_name='practice_attempts')
    op.drop_table('practice_attempts')
    op.drop_index(op.f('ix_question_options_question_id'), table_name='question_options')
    op.drop_table('question_options')
    op.drop_index(op.f('ix_practice_questions_topic_id'), table_name='practice_questions')
    op.drop_table('practice_questions')

    # The placeholder subject from seed_placeholders.py mentioned practice
    # questions. Only the unedited placeholder text is changed.
    op.execute(sa.text(
        "UPDATE test_subjects SET description = :new WHERE description = :old"
    ).bindparams(
        old="Sample subject showing how topics, resources and practice questions appear. "
            "It is not official admission-test material.",
        new="Sample subject showing how topics and learning resources appear. "
            "It is not official admission-test material.",
    ))


def downgrade() -> None:
    """Downgrade schema: recreates the empty tables (removed questions are not restored)."""
    op.create_table('practice_questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=True),
    sa.Column('difficulty', sa.String(length=10), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['test_topics.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practice_questions_topic_id'), 'practice_questions', ['topic_id'], unique=False)
    op.create_table('question_options',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('option_text', sa.String(length=500), nullable=False),
    sa.Column('is_correct', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['practice_questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_options_question_id'), 'question_options', ['question_id'], unique=False)
    op.create_table('practice_attempts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('selected_option_id', sa.Integer(), nullable=True),
    sa.Column('is_correct', sa.Boolean(), nullable=False),
    sa.Column('mode', sa.String(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['practice_questions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practice_attempts_question_id'), 'practice_attempts', ['question_id'], unique=False)
    op.create_index(op.f('ix_practice_attempts_user_id'), 'practice_attempts', ['user_id'], unique=False)

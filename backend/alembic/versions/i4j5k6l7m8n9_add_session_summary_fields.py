"""add summary and summarized_at to sessions table

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-04-03 13:00:00.000000

Adds AI-generated session summary storage so the AI Mentor can resume
conversations naturally when a user returns.
"""

from alembic import op
import sqlalchemy as sa

revision = 'i4j5k6l7m8n9'
down_revision = 'h3i4j5k6l7m8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'sessions',
        sa.Column('summary', sa.Text(), nullable=True),
    )
    op.add_column(
        'sessions',
        sa.Column('summarized_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_sessions_summarized', 'sessions', ['summarized_at'])


def downgrade() -> None:
    op.drop_index('idx_sessions_summarized', table_name='sessions')
    op.drop_column('sessions', 'summarized_at')
    op.drop_column('sessions', 'summary')

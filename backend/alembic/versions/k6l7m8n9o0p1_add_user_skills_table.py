"""add user_skills table

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2026-04-03 15:00:00.000000

Tracks per-user skill proficiency, updated after each project assessment.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'k6l7m8n9o0p1'
down_revision = 'j5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_skills',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('proficiency', sa.Float(), server_default='0.0'),
        sa.Column('assessment_count', sa.Integer(), server_default='0'),
        sa.Column('total_score', sa.Integer(), server_default='0'),
        sa.Column('last_assessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_skills_user_id', 'user_skills', ['user_id'])
    # Unique constraint: one row per (user, skill name)
    op.create_index('ix_user_skills_user_name', 'user_skills', ['user_id', 'name'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_user_skills_user_name', table_name='user_skills')
    op.drop_index('ix_user_skills_user_id', table_name='user_skills')
    op.drop_table('user_skills')

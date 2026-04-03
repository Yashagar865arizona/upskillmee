"""add project_assessments table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-03 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'project_assessments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('completeness_score', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('skill_alignment_score', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.String(), nullable=True),
        sa.Column('strengths', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('improvements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('next_steps', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('recommended_topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('assessment_report', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_project_assessments_project_id', 'project_assessments', ['project_id'])
    op.create_index('ix_project_assessments_user_id', 'project_assessments', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_project_assessments_user_id', table_name='project_assessments')
    op.drop_index('ix_project_assessments_project_id', table_name='project_assessments')
    op.drop_table('project_assessments')

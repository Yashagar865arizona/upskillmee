"""add post_project_discoveries table

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2026-04-03 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'h3i4j5k6l7m8'
down_revision = 'g2h3i4j5k6l7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'post_project_discoveries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('trigger_reason', sa.String(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conversation_starter', sa.String(), nullable=True),
        sa.Column('enjoyed_aspects', sa.String(), nullable=True),
        sa.Column('struggled_aspects', sa.String(), nullable=True),
        sa.Column('would_continue', sa.Boolean(), nullable=True),
        sa.Column('engagement_score', sa.Integer(), nullable=True),
        sa.Column('domains_confirmed', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('domains_rejected', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_post_project_discoveries_project_id', 'post_project_discoveries', ['project_id'])
    op.create_index('ix_post_project_discoveries_user_id', 'post_project_discoveries', ['user_id'])
    # Unique: one discovery per project (prevents duplicate triggers)
    op.create_unique_constraint(
        'uq_post_project_discoveries_project_id',
        'post_project_discoveries',
        ['project_id'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_post_project_discoveries_project_id', 'post_project_discoveries', type_='unique')
    op.drop_index('ix_post_project_discoveries_user_id', table_name='post_project_discoveries')
    op.drop_index('ix_post_project_discoveries_project_id', table_name='post_project_discoveries')
    op.drop_table('post_project_discoveries')

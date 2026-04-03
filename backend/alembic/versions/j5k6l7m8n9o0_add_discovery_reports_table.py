"""add discovery_reports table

Revision ID: j5k6l7m8n9o0
Revises: i4j5k6l7m8n9
Create Date: 2026-04-03 14:30:00.000000

Stores cached self-discovery reports with a shareable public token.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'j5k6l7m8n9o0'
down_revision = 'i4j5k6l7m8n9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'discovery_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('share_token', sa.String(), nullable=False),
        sa.Column('interest_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('strength_signals', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('domains_explored', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('pivot_suggestions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('narrative_summary', sa.String(), nullable=True),
        sa.Column('project_count_at_generation', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_discovery_reports_user_id', 'discovery_reports', ['user_id'])
    op.create_index('ix_discovery_reports_share_token', 'discovery_reports', ['share_token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_discovery_reports_share_token', table_name='discovery_reports')
    op.drop_index('ix_discovery_reports_user_id', table_name='discovery_reports')
    op.drop_table('discovery_reports')

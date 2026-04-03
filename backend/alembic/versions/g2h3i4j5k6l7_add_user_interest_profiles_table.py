"""add user_interest_profiles table

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-03 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k6l7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_interest_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_profile_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('domains', sa.JSON(), nullable=True),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('aversions', sa.JSON(), nullable=True),
        sa.Column('learning_style', sa.String(), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('signal_count', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_profile_id'),
    )


def downgrade() -> None:
    op.drop_table('user_interest_profiles')

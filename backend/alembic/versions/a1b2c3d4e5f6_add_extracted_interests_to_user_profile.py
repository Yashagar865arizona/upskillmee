"""add extracted_interests to user_profile

Revision ID: a1b2c3d4e5f6
Revises: f86e1a729d38
Create Date: 2026-04-03 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f86e1a729d38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'user_profiles',
        sa.Column('extracted_interests', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('user_profiles', 'extracted_interests')

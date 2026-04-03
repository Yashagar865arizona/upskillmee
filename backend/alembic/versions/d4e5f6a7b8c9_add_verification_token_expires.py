"""add verification_token_expires to users

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-03 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('verification_token_expires', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    op.drop_column('users', 'verification_token_expires')

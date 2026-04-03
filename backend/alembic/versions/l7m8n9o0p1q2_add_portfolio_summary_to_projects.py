"""add portfolio_summary to projects

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2026-04-03 16:00:00.000000

Caches AI-generated portfolio summaries per project for the portfolio builder.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'l7m8n9o0p1q2'
down_revision = 'k6l7m8n9o0p1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('portfolio_summary', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'portfolio_summary')

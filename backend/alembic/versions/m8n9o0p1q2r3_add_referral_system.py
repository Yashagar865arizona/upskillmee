"""add referral system

Revision ID: m8n9o0p1q2r3
Revises: l7m8n9o0p1q2
Create Date: 2026-04-03 17:00:00.000000

Adds referral_code to users and creates the referrals table.
"""
from alembic import op
import sqlalchemy as sa

revision = 'm8n9o0p1q2r3'
down_revision = 'l7m8n9o0p1q2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add referral_code to users
    op.add_column('users', sa.Column('referral_code', sa.String(), nullable=True))
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)

    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('referrer_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('referred_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('referral_code', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('reward_applied', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referred_user_id', name='uq_referrals_referred_user_id'),
    )
    op.create_index('ix_referrals_referrer_user_id', 'referrals', ['referrer_user_id'])


def downgrade() -> None:
    op.drop_index('ix_referrals_referrer_user_id', table_name='referrals')
    op.drop_table('referrals')
    op.drop_index('ix_users_referral_code', table_name='users')
    op.drop_column('users', 'referral_code')

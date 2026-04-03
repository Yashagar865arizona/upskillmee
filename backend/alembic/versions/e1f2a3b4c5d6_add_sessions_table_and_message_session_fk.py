"""add sessions table and message session_id FK

Revision ID: e1f2a3b4c5d6
Revises: 51565d26bea6, d4e5f6a7b8c9
Create Date: 2026-04-03 11:00:00.000000

Merges the two active heads and adds:
- sessions table (id, user_id, started_at, ended_at, message_count)
- session_id FK column on messages
"""

from alembic import op
import sqlalchemy as sa

revision = 'e1f2a3b4c5d6'
down_revision = ('51565d26bea6', 'd4e5f6a7b8c9')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_sessions_user_started', 'sessions', ['user_id', 'started_at'])
    op.create_index('idx_sessions_ended', 'sessions', ['ended_at'])

    # Add session_id FK to messages
    op.add_column(
        'messages',
        sa.Column('session_id', sa.String(), nullable=True),
    )
    op.create_foreign_key(
        'fk_messages_session_id',
        'messages', 'sessions',
        ['session_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('idx_messages_session_id', 'messages', ['session_id'])


def downgrade() -> None:
    op.drop_index('idx_messages_session_id', table_name='messages')
    op.drop_constraint('fk_messages_session_id', 'messages', type_='foreignkey')
    op.drop_column('messages', 'session_id')

    op.drop_index('idx_sessions_ended', table_name='sessions')
    op.drop_index('idx_sessions_user_started', table_name='sessions')
    op.drop_table('sessions')

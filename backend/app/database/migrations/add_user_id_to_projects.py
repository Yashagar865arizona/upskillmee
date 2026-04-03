"""
Migration script to add user_id column to projects table
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    """Add user_id column to projects table"""
    op.add_column('projects', sa.Column('user_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_projects_user_id_users',
        'projects', 'users',
        ['user_id'], ['id']
    )

def downgrade():
    """Remove user_id column from projects table"""
    op.drop_constraint('fk_projects_user_id_users', 'projects', type_='foreignkey')
    op.drop_column('projects', 'user_id')

"""Add global application settings

Revision ID: 8d7f2b6c1a4e
Revises: 6092c1f2572e
"""
from alembic import op
import sqlalchemy as sa

revision = '8d7f2b6c1a4e'
down_revision = '6092c1f2572e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('npm_bin_path', sa.String(length=500), nullable=True),
        sa.Column('node_path', sa.String(length=500), nullable=True),
        sa.Column('python_env_path', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('app_settings')

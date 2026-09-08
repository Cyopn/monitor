"""Remove email from users

Revision ID: c4e91a7b2d6f
Revises: 8d7f2b6c1a4e
"""
from alembic import op
import sqlalchemy as sa

revision = 'c4e91a7b2d6f'
down_revision = '8d7f2b6c1a4e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('email')


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('email', sa.String(length=120), nullable=True)
        )
        batch_op.create_unique_constraint('uq_user_email', ['email'])

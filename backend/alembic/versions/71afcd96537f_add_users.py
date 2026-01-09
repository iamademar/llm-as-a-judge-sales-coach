"""add users

Revision ID: 71afcd96537f
Revises: 002
Create Date: 2025-11-07 10:31:27.684349

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '71afcd96537f'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique user identifier'),
        sa.Column('email', sa.String(), nullable=False, comment='User email address (unique)'),
        sa.Column('hashed_password', sa.String(), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('full_name', sa.String(), nullable=True, comment="User's full name"),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether user account is active'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false', comment='Whether user has superuser privileges'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Account creation timestamp'),
        sa.PrimaryKeyConstraint('id'),
        comment='User accounts for authentication'
    )
    # Create indexes
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    # Drop table
    op.drop_table('users')

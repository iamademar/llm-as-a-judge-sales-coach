"""add organizations table

Revision ID: 004
Revises: 003
Create Date: 2025-12-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique organization identifier'),
        sa.Column('name', sa.String(), nullable=False, comment='Organization name (unique)'),
        sa.Column('description', sa.String(), nullable=True, comment='Organization description'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether organization is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Organization creation timestamp'),
        sa.PrimaryKeyConstraint('id'),
        comment='Organizations for multi-tenant support'
    )
    # Create indexes on organizations
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=True)

    # Add organization_id column to users table (nullable initially for migration)
    op.add_column('users', sa.Column('organization_id', UUID(as_uuid=True), nullable=True, comment='Organization this user belongs to'))
    op.create_foreign_key('fk_users_organization_id', 'users', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)

    # Add organization_id column to representatives table (nullable initially for migration)
    op.add_column('representatives', sa.Column('organization_id', UUID(as_uuid=True), nullable=True, comment='Organization this representative belongs to'))
    op.create_foreign_key('fk_representatives_organization_id', 'representatives', 'organizations', ['organization_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_representatives_organization_id'), 'representatives', ['organization_id'], unique=False)


def downgrade() -> None:
    # Drop organization_id from representatives
    op.drop_index(op.f('ix_representatives_organization_id'), table_name='representatives')
    op.drop_constraint('fk_representatives_organization_id', 'representatives', type_='foreignkey')
    op.drop_column('representatives', 'organization_id')

    # Drop organization_id from users
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    op.drop_column('users', 'organization_id')

    # Drop organizations table and indexes
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')


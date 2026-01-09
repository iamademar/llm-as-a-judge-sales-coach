"""add llm_credentials table

Revision ID: 005
Revises: 004
Create Date: 2025-12-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create LLM provider enum type (if it doesn't exist)
    op.execute("DO $$ BEGIN CREATE TYPE llmprovider AS ENUM ('openai', 'anthropic', 'google'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create llm_credentials table
    op.create_table(
        'llm_credentials',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique credential identifier'),
        sa.Column('organization_id', UUID(as_uuid=True), nullable=False, comment='Organization this credential belongs to'),
        sa.Column('provider', ENUM('openai', 'anthropic', 'google', name='llmprovider', create_type=False), nullable=False, comment='LLM provider (openai, anthropic, google)'),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False, comment='Fernet-encrypted API key'),
        sa.Column('default_model', sa.String(), nullable=True, comment='Default model name for this provider'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether this credential is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Credential creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Credential last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_llm_credentials_organization_id', ondelete='CASCADE'),
        comment='LLM provider API credentials for organizations'
    )

    # Create indexes
    op.create_index(op.f('ix_llm_credentials_id'), 'llm_credentials', ['id'], unique=False)
    op.create_index(op.f('ix_llm_credentials_organization_id'), 'llm_credentials', ['organization_id'], unique=False)
    op.create_index(op.f('ix_llm_credentials_provider'), 'llm_credentials', ['provider'], unique=False)

    # Create unique constraint for one credential per org per provider
    op.create_unique_constraint(
        'uq_llm_credentials_org_provider',
        'llm_credentials',
        ['organization_id', 'provider']
    )


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint('uq_llm_credentials_org_provider', 'llm_credentials', type_='unique')

    # Drop indexes
    op.drop_index(op.f('ix_llm_credentials_provider'), table_name='llm_credentials')
    op.drop_index(op.f('ix_llm_credentials_organization_id'), table_name='llm_credentials')
    op.drop_index(op.f('ix_llm_credentials_id'), table_name='llm_credentials')

    # Drop table
    op.drop_table('llm_credentials')

    # Drop enum type
    op.execute("DROP TYPE llmprovider")


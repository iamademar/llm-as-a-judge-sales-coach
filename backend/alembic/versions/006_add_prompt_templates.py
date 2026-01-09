"""add prompt_templates table

Revision ID: 006
Revises: 005
Create Date: 2025-12-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create prompt_templates table
    op.create_table(
        'prompt_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique template identifier'),
        sa.Column('organization_id', UUID(as_uuid=True), nullable=False, comment='Organization this template belongs to'),
        sa.Column('name', sa.String(100), nullable=False, comment='Human-readable template name'),
        sa.Column('version', sa.String(20), nullable=False, server_default='v0', comment='Version identifier (e.g., v0, v1, custom_v2)'),
        sa.Column('system_prompt', sa.Text(), nullable=False, comment='System prompt defining LLM behavior'),
        sa.Column('user_template', sa.Text(), nullable=False, comment='User prompt template (must contain {transcript} placeholder)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false', comment='Only one template per org can be active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Template creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Template last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_prompt_templates_organization_id', ondelete='CASCADE'),
        comment='Organization-specific prompt templates for SPIN assessments'
    )

    # Create indexes
    op.create_index(op.f('ix_prompt_templates_id'), 'prompt_templates', ['id'], unique=False)
    op.create_index(op.f('ix_prompt_templates_organization_id'), 'prompt_templates', ['organization_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_prompt_templates_organization_id'), table_name='prompt_templates')
    op.drop_index(op.f('ix_prompt_templates_id'), table_name='prompt_templates')

    # Drop table
    op.drop_table('prompt_templates')


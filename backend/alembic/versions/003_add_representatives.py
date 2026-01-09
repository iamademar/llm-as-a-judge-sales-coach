"""add representatives table

Revision ID: 003
Revises: 71afcd96537f
Create Date: 2025-11-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '71afcd96537f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create representatives table
    op.create_table(
        'representatives',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique representative identifier'),
        sa.Column('full_name', sa.String(), nullable=False, comment="Representative's full name"),
        sa.Column('email', sa.String(), nullable=False, comment="Representative's email address"),
        sa.Column('department', sa.String(), nullable=True, comment="Department or team (e.g., 'Enterprise Sales', 'SMB')"),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether representative is currently active'),
        sa.Column('hire_date', sa.DateTime(timezone=True), nullable=True, comment='Date when rep joined'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.PrimaryKeyConstraint('id'),
        comment='Sales representatives being coached'
    )
    # Create indexes on representatives
    op.create_index(op.f('ix_representatives_id'), 'representatives', ['id'], unique=False)
    op.create_index(op.f('ix_representatives_full_name'), 'representatives', ['full_name'], unique=False)
    op.create_index(op.f('ix_representatives_email'), 'representatives', ['email'], unique=True)
    
    # Drop old rep_id column from transcripts
    op.drop_index('ix_transcripts_rep_id', table_name='transcripts')
    op.drop_column('transcripts', 'rep_id')
    
    # Add new representative_id column to transcripts
    op.add_column('transcripts', sa.Column('representative_id', UUID(as_uuid=True), nullable=True, comment='Reference to representative'))
    op.create_foreign_key('fk_transcripts_representative_id', 'transcripts', 'representatives', ['representative_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_transcripts_representative_id'), 'transcripts', ['representative_id'], unique=False)


def downgrade() -> None:
    # Drop representative_id from transcripts
    op.drop_index(op.f('ix_transcripts_representative_id'), table_name='transcripts')
    op.drop_constraint('fk_transcripts_representative_id', 'transcripts', type_='foreignkey')
    op.drop_column('transcripts', 'representative_id')
    
    # Re-add old rep_id column
    op.add_column('transcripts', sa.Column('rep_id', sa.String(), nullable=True, comment='Sales representative identifier'))
    op.create_index('ix_transcripts_rep_id', 'transcripts', ['rep_id'], unique=False)
    
    # Drop representatives table and indexes
    op.drop_index(op.f('ix_representatives_email'), table_name='representatives')
    op.drop_index(op.f('ix_representatives_full_name'), table_name='representatives')
    op.drop_index(op.f('ix_representatives_id'), table_name='representatives')
    op.drop_table('representatives')


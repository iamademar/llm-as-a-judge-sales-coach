"""Initial schema with transcripts and assessments tables

Revision ID: 001
Revises:
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transcripts table
    op.create_table(
        'transcripts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rep_id', sa.String(), nullable=True, comment='Sales representative identifier'),
        sa.Column('buyer_id', sa.String(), nullable=True, comment='Buyer/customer identifier'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='Additional context (call_date, industry, etc.)'),
        sa.Column('transcript', sa.Text(), nullable=False, comment='Full conversation text with speaker tags'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when transcript was created'),
        sa.PrimaryKeyConstraint('id'),
        comment='Sales conversation transcripts'
    )
    op.create_index(op.f('ix_transcripts_id'), 'transcripts', ['id'], unique=False)
    op.create_index(op.f('ix_transcripts_rep_id'), 'transcripts', ['rep_id'], unique=False)
    op.create_index(op.f('ix_transcripts_buyer_id'), 'transcripts', ['buyer_id'], unique=False)

    # Create assessments table
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transcript_id', sa.Integer(), nullable=False, comment='Reference to parent transcript'),
        sa.Column('scores', sa.JSON(), nullable=False, comment='SPIN scores: {situation, problem, implication, need_payoff, flow, tone, engagement}'),
        sa.Column('coaching', sa.JSON(), nullable=False, comment='Coaching feedback: {summary, wins, gaps, next_actions}'),
        sa.Column('model_name', sa.String(), nullable=False, comment="LLM model identifier (e.g., 'gpt-4o-mini', 'claude-3-sonnet')"),
        sa.Column('prompt_version', sa.String(), nullable=False, comment="Prompt template version (e.g., 'spin_v1', 'spin_v2')"),
        sa.Column('latency_ms', sa.Integer(), nullable=True, comment='LLM call latency in milliseconds'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when assessment was created'),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='SPIN framework assessments'
    )
    op.create_index(op.f('ix_assessments_id'), 'assessments', ['id'], unique=False)
    op.create_index(op.f('ix_assessments_transcript_id'), 'assessments', ['transcript_id'], unique=False)
    op.create_index(op.f('ix_assessments_model_name'), 'assessments', ['model_name'], unique=False)
    op.create_index(op.f('ix_assessments_prompt_version'), 'assessments', ['prompt_version'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_assessments_prompt_version'), table_name='assessments')
    op.drop_index(op.f('ix_assessments_model_name'), table_name='assessments')
    op.drop_index(op.f('ix_assessments_transcript_id'), table_name='assessments')
    op.drop_index(op.f('ix_assessments_id'), table_name='assessments')
    op.drop_table('assessments')

    op.drop_index(op.f('ix_transcripts_buyer_id'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_rep_id'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_id'), table_name='transcripts')
    op.drop_table('transcripts')

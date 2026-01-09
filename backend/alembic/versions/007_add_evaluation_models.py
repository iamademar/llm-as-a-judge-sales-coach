"""add evaluation models

Revision ID: 007
Revises: 006
Create Date: 2025-12-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create evaluation_datasets table
    op.create_table(
        'evaluation_datasets',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('organization_id', UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Dataset name (e.g., sales-eval-v1, Q4-2024-golden-set)'),
        sa.Column('description', sa.Text(), nullable=True, comment='Description of dataset contents and purpose'),
        sa.Column('source_type', sa.String(length=20), nullable=False, server_default='csv', comment='Source type: csv, langsmith, or database'),
        sa.Column('source_path', sa.String(length=500), nullable=True, comment='CSV file path or LangSmith dataset ID'),
        sa.Column('num_examples', sa.Integer(), nullable=False, comment='Number of examples in the dataset'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='Dataset creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='Dataset last update timestamp'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evaluation_datasets_id', 'evaluation_datasets', ['id'])
    op.create_index('ix_evaluation_datasets_organization_id', 'evaluation_datasets', ['organization_id'])

    # Create evaluation_runs table
    op.create_table(
        'evaluation_runs',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('prompt_template_id', UUID(), nullable=False),
        sa.Column('dataset_id', UUID(), nullable=True),
        sa.Column('experiment_name', sa.String(length=100), nullable=True, comment='Optional experiment name for tracking iterations'),
        sa.Column('num_examples', sa.Integer(), nullable=False, comment='Number of examples evaluated'),
        sa.Column('macro_pearson_r', sa.Float(), nullable=True, comment='Macro-averaged Pearson correlation across all dimensions'),
        sa.Column('macro_qwk', sa.Float(), nullable=True, comment='Macro-averaged Quadratic Weighted Kappa'),
        sa.Column('macro_plus_minus_one', sa.Float(), nullable=True, comment='Macro-averaged ±1 accuracy'),
        sa.Column('per_dimension_metrics', JSON, nullable=False, comment='Metrics for each dimension: {dimension: {pearson_r, qwk, pm1}}'),
        sa.Column('model_name', sa.String(length=50), nullable=True, comment='LLM model used (e.g., gpt-4o-mini)'),
        sa.Column('runtime_seconds', sa.Float(), nullable=True, comment='Total evaluation runtime in seconds'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='Evaluation run timestamp'),
        sa.ForeignKeyConstraint(['dataset_id'], ['evaluation_datasets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_template_id'], ['prompt_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evaluation_runs_id', 'evaluation_runs', ['id'])
    op.create_index('ix_evaluation_runs_prompt_template_id', 'evaluation_runs', ['prompt_template_id'])
    op.create_index('ix_evaluation_runs_dataset_id', 'evaluation_runs', ['dataset_id'])


def downgrade():
    op.drop_index('ix_evaluation_runs_dataset_id', table_name='evaluation_runs')
    op.drop_index('ix_evaluation_runs_prompt_template_id', table_name='evaluation_runs')
    op.drop_index('ix_evaluation_runs_id', table_name='evaluation_runs')
    op.drop_table('evaluation_runs')
    
    op.drop_index('ix_evaluation_datasets_organization_id', table_name='evaluation_datasets')
    op.drop_index('ix_evaluation_datasets_id', table_name='evaluation_datasets')
    op.drop_table('evaluation_datasets')


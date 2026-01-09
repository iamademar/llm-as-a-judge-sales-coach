"""add langsmith fields

Revision ID: 008
Revises: 007
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Add LangSmith fields to evaluation_datasets
    op.add_column('evaluation_datasets', 
        sa.Column('langsmith_dataset_name', sa.String(length=200), nullable=True,
                  comment='Slugified name used in LangSmith'))
    op.add_column('evaluation_datasets', 
        sa.Column('langsmith_dataset_id', sa.String(length=100), nullable=True,
                  comment='LangSmith dataset ID after upload'))
    
    # Add LangSmith fields to evaluation_runs
    op.add_column('evaluation_runs', 
        sa.Column('langsmith_url', sa.String(length=500), nullable=True,
                  comment='URL to view this evaluation in LangSmith'))
    op.add_column('evaluation_runs', 
        sa.Column('langsmith_experiment_id', sa.String(length=100), nullable=True,
                  comment='LangSmith experiment/session ID'))


def downgrade():
    # Remove LangSmith fields from evaluation_runs
    op.drop_column('evaluation_runs', 'langsmith_experiment_id')
    op.drop_column('evaluation_runs', 'langsmith_url')
    
    # Remove LangSmith fields from evaluation_datasets
    op.drop_column('evaluation_datasets', 'langsmith_dataset_id')
    op.drop_column('evaluation_datasets', 'langsmith_dataset_name')


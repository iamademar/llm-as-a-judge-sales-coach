"""Add embedding vector column to transcripts

Revision ID: 002
Revises: 001
Create Date: 2024-11-04 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add embedding column for similarity search.

    Uses TEXT to store JSON-encoded arrays for both PostgreSQL and SQLite.
    This simplifies the implementation and avoids PostgreSQL extension dependencies.
    """
    # Use TEXT for both PostgreSQL and SQLite (JSON-encoded array)
    op.add_column('transcripts',
        sa.Column('embedding', sa.Text, nullable=True,
                  comment="Embedding vector for similarity search (JSON-encoded array)")
    )


def downgrade() -> None:
    """Remove embedding column."""
    op.drop_column('transcripts', 'embedding')

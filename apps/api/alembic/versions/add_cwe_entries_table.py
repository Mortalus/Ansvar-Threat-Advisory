"""Add CWE entries table for knowledge base integration

Revision ID: add_cwe_entries_table
Revises: add_system_prompt_templates
Create Date: 2025-08-07 08:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_cwe_entries_table'
down_revision: Union[str, None] = 'add_system_prompt_templates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CWE entries table for storing Common Weakness Enumeration data."""
    
    op.create_table('cwe_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cwe_id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('extended_description', sa.Text(), nullable=True),
        sa.Column('weakness_abstraction', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('likelihood_of_exploit', sa.String(length=20), nullable=True),
        sa.Column('relevant_components', sa.JSON(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('source_version', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index('ix_cwe_entries_id', 'cwe_entries', ['id'])
    op.create_index('ix_cwe_entries_cwe_id', 'cwe_entries', ['cwe_id'], unique=True)
    op.create_index('ix_cwe_entries_name', 'cwe_entries', ['name'])
    

def downgrade() -> None:
    """Remove CWE entries table."""
    
    op.drop_index('ix_cwe_entries_name', table_name='cwe_entries')
    op.drop_index('ix_cwe_entries_cwe_id', table_name='cwe_entries')
    op.drop_index('ix_cwe_entries_id', table_name='cwe_entries')
    op.drop_table('cwe_entries')
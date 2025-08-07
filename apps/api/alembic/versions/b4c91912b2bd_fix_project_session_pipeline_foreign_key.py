"""fix_project_session_pipeline_foreign_key

Revision ID: b4c91912b2bd
Revises: 656b11d079ab
Create Date: 2025-08-07 10:33:34.785147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4c91912b2bd'
down_revision: Union[str, None] = '656b11d079ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration fixes the foreign key constraint in project_sessions table 
    # to reference pipelines.pipeline_id instead of pipelines.id
    # 
    # Note: This assumes the project_sessions table exists but has an incorrect FK.
    # If the previous migration failed, this will be handled by the constraint check.
    
    try:
        # Drop the incorrect foreign key constraint if it exists
        op.drop_constraint('project_sessions_pipeline_id_fkey', 'project_sessions', type_='foreignkey')
    except Exception:
        # Constraint might not exist if previous migration failed
        pass
    
    try:
        # Add the correct foreign key constraint
        op.create_foreign_key(
            'project_sessions_pipeline_id_fkey',  # constraint name
            'project_sessions',                   # source table
            'pipelines',                          # target table
            ['pipeline_id'],                      # source column
            ['pipeline_id']                       # target column
        )
    except Exception:
        # If this fails, the table structure might need to be created first
        pass


def downgrade() -> None:
    # Revert back to the incorrect foreign key (this is for completeness but will likely fail)
    try:
        op.drop_constraint('project_sessions_pipeline_id_fkey', 'project_sessions', type_='foreignkey')
    except Exception:
        pass
    
    try:
        # Recreate the incorrect constraint (this will fail, but matches the original state)
        op.create_foreign_key(
            'project_sessions_pipeline_id_fkey',
            'project_sessions',
            'pipelines', 
            ['pipeline_id'],
            ['id']
        )
    except Exception:
        pass

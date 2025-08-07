"""add_stride_data_extraction_fields

Revision ID: 656b11d079ab
Revises: e5d443e88ad4
Create Date: 2025-08-07 10:15:22.542775

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '656b11d079ab'
down_revision: Union[str, None] = 'e5d443e88ad4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns for STRIDE data extraction
    op.add_column('pipelines', sa.Column('extracted_security_data', sa.JSON(), nullable=True))
    op.add_column('pipelines', sa.Column('extraction_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove the STRIDE data extraction columns
    op.drop_column('pipelines', 'extraction_metadata')
    op.drop_column('pipelines', 'extracted_security_data')

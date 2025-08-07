"""merge heads

Revision ID: e5d443e88ad4
Revises: add_cwe_entries_table, add_project_session_management
Create Date: 2025-08-07 09:58:22.766072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5d443e88ad4'
down_revision: Union[str, None] = ('add_cwe_entries_table', 'add_project_session_management')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

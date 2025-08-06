"""Enable vector extension

Revision ID: a0e0e645baea
Revises: f053c594b48b
Create Date: 2025-08-06 15:13:37.556768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0e0e645baea'
down_revision: Union[str, None] = 'f053c594b48b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only create extension for PostgreSQL
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    # Only drop extension for PostgreSQL
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        op.execute("DROP EXTENSION IF EXISTS vector;")

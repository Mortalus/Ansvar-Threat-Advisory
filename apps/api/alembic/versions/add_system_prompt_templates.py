"""Add system prompt templates table

Revision ID: add_system_prompt_templates
Revises: fe732f22db6c
Create Date: 2025-08-07 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'add_system_prompt_templates'
down_revision = 'fe732f22db6c'
branch_labels = None
depends_on = None

def upgrade():
    # Create system_prompt_templates table
    op.create_table(
        'system_prompt_templates',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('step_name', sa.String(100), nullable=False, index=True),
        sa.Column('agent_type', sa.String(100), nullable=True, index=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    
    # Create indexes
    op.create_index('ix_step_agent_active', 'system_prompt_templates', ['step_name', 'agent_type', 'is_active'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_step_agent_active', 'system_prompt_templates')
    
    # Drop table
    op.drop_table('system_prompt_templates')
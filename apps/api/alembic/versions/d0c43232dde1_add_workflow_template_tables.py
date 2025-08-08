"""Add workflow template tables

Revision ID: d0c43232dde1
Revises: 4e6b473791b0
Create Date: 2025-08-08 14:12:50.620144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0c43232dde1'
down_revision: Union[str, None] = '4e6b473791b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflow_templates table
    op.create_table(
        'workflow_templates',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(20), nullable=True, default='1.0.0'),
        sa.Column('steps', sa.JSON(), nullable=False),
        sa.Column('automation_settings', sa.JSON(), nullable=True, default=sa.text('{}')),
        sa.Column('client_access_rules', sa.JSON(), nullable=True, default=sa.text('{}')),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'])
    )
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=True),
        sa.Column('client_email', sa.String(255), nullable=True),
        sa.Column('client_organization', sa.String(255), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(50), nullable=True, default='pending'),
        sa.Column('data', sa.JSON(), nullable=True, default=sa.text('{}')),
        sa.Column('automation_overrides', sa.JSON(), nullable=True, default=sa.text('{}')),
        sa.Column('started_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['workflow_templates.id'])
    )
    
    # Create workflow_step_executions table
    op.create_table(
        'workflow_step_executions',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_execution_id', sa.UUID(), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('agent_name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, default='pending'),
        sa.Column('input_data', sa.JSON(), nullable=True, default=sa.text('{}')),
        sa.Column('output_data', sa.JSON(), nullable=True, default=sa.text('{}')),
        sa.Column('automated', sa.Boolean(), nullable=True, default=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('requires_review', sa.Boolean(), nullable=True, default=False),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_status', sa.String(50), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'])
    )
    
    # Create indexes for performance
    op.create_index('ix_workflow_executions_template_id', 'workflow_executions', ['template_id'])
    op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])
    op.create_index('ix_workflow_step_executions_workflow_id', 'workflow_step_executions', ['workflow_execution_id'])
    op.create_index('ix_workflow_step_executions_status', 'workflow_step_executions', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_workflow_step_executions_status')
    op.drop_index('ix_workflow_step_executions_workflow_id')
    op.drop_index('ix_workflow_executions_status')
    op.drop_index('ix_workflow_executions_template_id')
    
    # Drop tables in reverse order
    op.drop_table('workflow_step_executions')
    op.drop_table('workflow_executions')
    op.drop_table('workflow_templates')

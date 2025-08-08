"""Phase 1 Workflow Engine Models

Revision ID: 337d52f8ff8
Revises: d0c43232dde1
Create Date: 2025-08-08 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = '337d52f8ff8'
down_revision: Union[str, None] = 'd0c43232dde1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade to Phase 1 Workflow Engine Models"""
    
    # Drop old workflow tables if they exist
    op.execute("DROP TABLE IF EXISTS workflow_step_executions CASCADE")
    op.execute("DROP TABLE IF EXISTS workflow_executions CASCADE")
    op.execute("DROP TABLE IF EXISTS workflow_templates CASCADE")
    
    # Create new workflow_templates table
    op.create_table(
        'workflow_templates',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                 onupdate=sa.func.now(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(50), nullable=False, default='1.0.0'),
        sa.Column('definition', JSONB(), nullable=False),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('tags', JSONB(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_system_template', sa.Boolean(), default=False, nullable=False),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('max_parallel_steps', sa.Integer(), default=3),
        sa.Column('requires_review', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'version', name='uq_template_name_version'),
        sa.CheckConstraint('char_length(name) >= 3', name='chk_template_name_length'),
        sa.CheckConstraint('max_parallel_steps > 0', name='chk_max_parallel_positive'),
        sa.CheckConstraint('estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0', 
                          name='chk_duration_positive')
    )
    
    # Create index for template active status and category
    op.create_index('idx_template_active_category', 'workflow_templates', ['is_active', 'category'])
    
    # Create workflow_runs table
    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                 onupdate=sa.func.now(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('run_id', UUID(as_uuid=True), default=sa.text('gen_random_uuid()'), 
                 unique=True, index=True, nullable=False),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('workflow_templates.id'), 
                 nullable=False, index=True),
        sa.Column('template_version', sa.String(50), nullable=False),
        sa.Column('run_definition', JSONB(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='created', index=True),
        sa.Column('current_step_id', sa.String(100), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', JSONB(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('max_retries', sa.Integer(), default=3, nullable=False),
        sa.Column('total_steps', sa.Integer(), nullable=True),
        sa.Column('completed_steps', sa.Integer(), default=0, nullable=False),
        sa.Column('failed_steps', sa.Integer(), default=0, nullable=False),
        sa.Column('auto_continue', sa.Boolean(), default=False),
        sa.Column('timeout_minutes', sa.Integer(), default=240),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('created', 'running', 'paused', 'completed', 'failed', 'cancelled', 'timeout')", 
                          name='chk_valid_status'),
        sa.CheckConstraint('retry_count >= 0', name='chk_retry_count_positive'),
        sa.CheckConstraint('max_retries >= 0', name='chk_max_retries_positive'),
        sa.CheckConstraint('total_steps IS NULL OR total_steps > 0', name='chk_total_steps_positive'),
        sa.CheckConstraint('completed_steps >= 0', name='chk_completed_steps_positive'),
        sa.CheckConstraint('failed_steps >= 0', name='chk_failed_steps_positive'),
        sa.CheckConstraint('timeout_minutes > 0', name='chk_timeout_positive')
    )
    
    # Create indexes for workflow runs
    op.create_index('idx_run_status_user', 'workflow_runs', ['status', 'user_id'])
    op.create_index('idx_run_template_status', 'workflow_runs', ['template_id', 'status'])
    
    # Create workflow_step_executions table
    op.create_table(
        'workflow_step_executions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                 onupdate=sa.func.now(), nullable=False),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('workflow_runs.id'), nullable=False, index=True),
        sa.Column('step_id', sa.String(100), nullable=False, index=True),
        sa.Column('step_name', sa.String(255), nullable=True),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('agent_version', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending', index=True),
        sa.Column('execution_order', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', JSONB(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('input_artifacts', JSONB(), nullable=True),
        sa.Column('output_artifacts', JSONB(), nullable=True),
        sa.Column('prompt_override', sa.Text(), nullable=True),
        sa.Column('configuration', JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id', 'step_id', name='uq_run_step'),
        sa.CheckConstraint("status IN ('pending', 'ready', 'running', 'awaiting_review', 'completed', 'failed', 'skipped', 'retrying')", 
                          name='chk_valid_step_status'),
        sa.CheckConstraint('retry_count >= 0', name='chk_step_retry_count_positive'),
        sa.CheckConstraint('duration_seconds IS NULL OR duration_seconds >= 0', name='chk_duration_positive')
    )
    
    # Create indexes for step executions
    op.create_index('idx_step_run_status', 'workflow_step_executions', ['run_id', 'status'])
    op.create_index('idx_step_agent_type', 'workflow_step_executions', ['agent_type'])
    
    # Create workflow_artifacts table
    op.create_table(
        'workflow_artifacts',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), 
                 onupdate=sa.func.now(), nullable=False),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('workflow_runs.id'), nullable=False, index=True),
        sa.Column('producing_step_id', sa.String(100), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('artifact_type', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('is_latest', sa.Boolean(), default=True, nullable=False, index=True),
        sa.Column('content_json', JSONB(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('content_binary', sa.LargeBinary(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id', 'name', 'version', name='uq_artifact_version'),
        sa.CheckConstraint('version > 0', name='chk_version_positive'),
        sa.CheckConstraint('size_bytes IS NULL OR size_bytes >= 0', name='chk_size_positive'),
        sa.CheckConstraint('char_length(name) >= 1', name='chk_artifact_name_length'),
        # Ensure only one content field is used
        sa.CheckConstraint(
            '(content_json IS NOT NULL)::int + (content_text IS NOT NULL)::int + (content_binary IS NOT NULL)::int = 1',
            name='chk_single_content_type'
        )
    )
    
    # Create indexes for artifacts
    op.create_index('idx_artifact_run_name_latest', 'workflow_artifacts', ['run_id', 'name', 'is_latest'])
    op.create_index('idx_artifact_type_step', 'workflow_artifacts', ['artifact_type', 'producing_step_id'])


def downgrade() -> None:
    """Downgrade from Phase 1 Workflow Engine Models"""
    
    # Drop indexes
    op.drop_index('idx_artifact_type_step', table_name='workflow_artifacts')
    op.drop_index('idx_artifact_run_name_latest', table_name='workflow_artifacts')
    op.drop_index('idx_step_agent_type', table_name='workflow_step_executions')
    op.drop_index('idx_step_run_status', table_name='workflow_step_executions')
    op.drop_index('idx_run_template_status', table_name='workflow_runs')
    op.drop_index('idx_run_status_user', table_name='workflow_runs')
    op.drop_index('idx_template_active_category', table_name='workflow_templates')
    
    # Drop tables in reverse order
    op.drop_table('workflow_artifacts')
    op.drop_table('workflow_step_executions')
    op.drop_table('workflow_runs')
    op.drop_table('workflow_templates')
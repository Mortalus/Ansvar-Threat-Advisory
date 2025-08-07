"""Add project and session management tables

Revision ID: add_project_session_management
Revises: fe732f22db6c
Create Date: 2025-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_project_session_management'
down_revision = 'fe732f22db6c'
branch_labels = None
depends_on = None


def upgrade():
    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('default_llm_provider', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_created_at'), 'projects', ['created_at'], unique=False)

    # Create project_sessions table
    op.create_table('project_sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_session_id', sa.String(36), nullable=True),
        sa.Column('branch_point', sa.String(length=50), nullable=True),
        sa.Column('is_main_branch', sa.Boolean(), nullable=True),
        sa.Column('pipeline_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('completion_percentage', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('document_name', sa.String(length=255), nullable=True),
        sa.Column('document_size', sa.Integer(), nullable=True),
        sa.Column('total_threats_found', sa.Integer(), nullable=True),
        sa.Column('risk_level_summary', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['parent_session_id'], ['project_sessions.id'], ),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.pipeline_id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_sessions_project_id'), 'project_sessions', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_sessions_created_at'), 'project_sessions', ['created_at'], unique=False)
    op.create_index(op.f('ix_project_sessions_status'), 'project_sessions', ['status'], unique=False)

    # Create session_snapshots table
    op.create_table('session_snapshots',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('step_name', sa.String(length=50), nullable=False),
        sa.Column('snapshot_name', sa.String(length=255), nullable=True),
        sa.Column('pipeline_state', sa.Text(), nullable=False),
        sa.Column('step_results', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('created_by_action', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['project_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_snapshots_session_id'), 'session_snapshots', ['session_id'], unique=False)
    op.create_index(op.f('ix_session_snapshots_step_name'), 'session_snapshots', ['step_name'], unique=False)
    op.create_index(op.f('ix_session_snapshots_created_at'), 'session_snapshots', ['created_at'], unique=False)


def downgrade():
    # Drop indexes and tables in reverse order
    op.drop_index(op.f('ix_session_snapshots_created_at'), table_name='session_snapshots')
    op.drop_index(op.f('ix_session_snapshots_step_name'), table_name='session_snapshots')
    op.drop_index(op.f('ix_session_snapshots_session_id'), table_name='session_snapshots')
    op.drop_table('session_snapshots')
    
    op.drop_index(op.f('ix_project_sessions_status'), table_name='project_sessions')
    op.drop_index(op.f('ix_project_sessions_created_at'), table_name='project_sessions')
    op.drop_index(op.f('ix_project_sessions_project_id'), table_name='project_sessions')
    op.drop_table('project_sessions')
    
    op.drop_index(op.f('ix_projects_created_at'), table_name='projects')
    op.drop_index(op.f('ix_projects_name'), table_name='projects')
    op.drop_table('projects')

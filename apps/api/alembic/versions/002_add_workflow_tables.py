"""Add workflow tables

Revision ID: 002_add_workflow_tables
Revises: 001_initial
Create Date: 2026-02-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '002_add_workflow_tables'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def table_exists(table_name):
    bind = op.get_context().bind
    insp = inspect(bind)
    return table_name in insp.get_table_names()

def upgrade() -> None:
    # 1. Create Enums (Idempotent)
    # job_status
    op.execute("DO $$ BEGIN CREATE TYPE job_status AS ENUM ('intake', 'reset', 'functional', 'qc', 'completed', 'failed', 'on_hold'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    # test_result_status
    op.execute("DO $$ BEGIN CREATE TYPE test_result_status AS ENUM ('pass', 'fail', 'skip', 'pending'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    # evidence_type
    op.execute("DO $$ BEGIN CREATE TYPE evidence_type AS ENUM ('photo', 'video', 'document'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    # report_scope
    op.execute("DO $$ BEGIN CREATE TYPE report_scope AS ENUM ('master', 'intake', 'reset', 'functional', 'qc'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    # report_variant
    op.execute("DO $$ BEGIN CREATE TYPE report_variant AS ENUM ('customer', 'internal'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # 2. Add station_type to users (Idempotent check)
    bind = op.get_context().bind
    insp = inspect(bind)
    columns = [c['name'] for c in insp.get_columns('users')]
    if 'station_type' not in columns:
        op.add_column('users', sa.Column('station_type', postgresql.ENUM(name='job_status', create_type=False), nullable=True))

    # 3. Create devices table
    if not table_exists('devices'):
        op.create_table('devices',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('platform', sa.String(length=50), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('model_number', sa.String(length=50), nullable=True),
            sa.Column('test_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

    # 4. Create stations table
    if not table_exists('stations'):
        op.create_table('stations',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('station_type', postgresql.ENUM(name='job_status', create_type=False), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    # 5. Create jobs table
    if not table_exists('jobs'):
        op.create_table('jobs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('device_id', sa.UUID(), nullable=True),
            sa.Column('serial_number', sa.String(length=100), nullable=False),
            sa.Column('status', postgresql.ENUM(name='job_status', create_type=False), nullable=False),
            sa.Column('current_station_id', sa.UUID(), nullable=True),
            sa.Column('assigned_technician_id', sa.UUID(), nullable=True),
            sa.Column('intake_started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('intake_completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('reset_started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('reset_completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('functional_started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('functional_completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('qc_started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('qc_completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('qc_technician_id', sa.UUID(), nullable=True),
            sa.Column('qc_initials', sa.String(length=10), nullable=True),
            sa.Column('qc_notes', sa.Text(), nullable=True),
            sa.Column('batch_id', sa.String(length=100), nullable=True),
            sa.Column('customer_reference', sa.String(length=255), nullable=True),
            sa.Column('intake_condition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(['assigned_technician_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['current_station_id'], ['stations.id'], ),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
            sa.ForeignKeyConstraint(['qc_technician_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_jobs_serial_number'), 'jobs', ['serial_number'], unique=False)

    # 6. Create test_steps table
    if not table_exists('test_steps'):
        op.create_table('test_steps',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('device_id', sa.UUID(), nullable=True),
            sa.Column('station_type', postgresql.ENUM(name='job_status', create_type=False), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('sequence_order', sa.Integer(), nullable=False),
            sa.Column('is_mandatory', sa.Boolean(), nullable=False),
            sa.Column('requires_evidence', sa.Boolean(), nullable=False),
            sa.Column('evidence_instructions', sa.Text(), nullable=True),
            sa.Column('criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 7. Create test_results table
    if not table_exists('test_results'):
        op.create_table('test_results',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('job_id', sa.UUID(), nullable=False),
            sa.Column('test_step_id', sa.UUID(), nullable=False),
            sa.Column('status', postgresql.ENUM(name='test_result_status', create_type=False), nullable=False),
            sa.Column('performed_by_id', sa.UUID(), nullable=False),
            sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('measurements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['test_step_id'], ['test_steps.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 8. Create evidence table
    if not table_exists('evidence'):
        op.create_table('evidence',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('job_id', sa.UUID(), nullable=False),
            sa.Column('test_result_id', sa.UUID(), nullable=True),
            sa.Column('evidence_type', postgresql.ENUM(name='evidence_type', create_type=False), nullable=False),
            sa.Column('original_filename', sa.String(length=255), nullable=False),
            sa.Column('stored_filename', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=False),
            sa.Column('sha256_hash', sa.String(length=64), nullable=False),
            sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('captured_by_id', sa.UUID(), nullable=False),
            sa.Column('caption', sa.Text(), nullable=True),
            sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('superseded_by_id', sa.UUID(), nullable=True),
            sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['captured_by_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['superseded_by_id'], ['evidence.id'], ),
            sa.ForeignKeyConstraint(['test_result_id'], ['test_results.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_evidence_job_id'), 'evidence', ['job_id'], unique=False)
        op.create_index(op.f('ix_evidence_sha256_hash'), 'evidence', ['sha256_hash'], unique=False)
        op.create_index(op.f('ix_evidence_test_result_id'), 'evidence', ['test_result_id'], unique=False)

    # 9. Create reports table
    if not table_exists('reports'):
        op.create_table('reports',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('job_id', sa.UUID(), nullable=False),
            sa.Column('scope', postgresql.ENUM(name='report_scope', create_type=False), nullable=False),
            sa.Column('variant', postgresql.ENUM(name='report_variant', create_type=False), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
            sa.Column('access_token', sa.String(length=64), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('generated_by_id', sa.UUID(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['generated_by_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_reports_access_token'), 'reports', ['access_token'], unique=True)
        op.create_index(op.f('ix_reports_job_id'), 'reports', ['job_id'], unique=False)

    # 10. Create job_history table
    if not table_exists('job_history'):
        op.create_table('job_history',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('job_id', sa.UUID(), nullable=False),
            sa.Column('from_status', postgresql.ENUM(name='job_status', create_type=False), nullable=True),
            sa.Column('to_status', postgresql.ENUM(name='job_status', create_type=False), nullable=False),
            sa.Column('changed_by_id', sa.UUID(), nullable=False),
            sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('station_id', sa.UUID(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('transition_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('job_history')
    op.drop_index(op.f('ix_reports_job_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_access_token'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_evidence_test_result_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_sha256_hash'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_job_id'), table_name='evidence')
    op.drop_table('evidence')
    op.drop_table('test_results')
    op.drop_table('test_steps')
    op.drop_index(op.f('ix_jobs_serial_number'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_table('stations')
    op.drop_table('devices')
    
    # Remove column
    op.drop_column('users', 'station_type')

    # Drop types
    op.execute("DROP TYPE report_variant")
    op.execute("DROP TYPE report_scope")
    op.execute("DROP TYPE evidence_type")
    op.execute("DROP TYPE test_result_status")
    op.execute("DROP TYPE job_status")

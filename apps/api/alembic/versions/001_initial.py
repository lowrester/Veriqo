"""Initial migration - create all tables.

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'supervisor', 'technician', 'viewer')")
    op.execute("CREATE TYPE job_status AS ENUM ('intake', 'reset', 'functional', 'qc', 'completed', 'failed', 'on_hold')")
    op.execute("CREATE TYPE test_result_status AS ENUM ('pass', 'fail', 'skip', 'pending')")
    op.execute("CREATE TYPE evidence_type AS ENUM ('photo', 'video', 'document')")
    op.execute("CREATE TYPE report_scope AS ENUM ('master', 'intake', 'reset', 'functional', 'qc')")
    op.execute("CREATE TYPE report_variant AS ENUM ('customer', 'internal')")

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("admin", "supervisor", "technician", "viewer", name="user_role", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=False)
    op.create_index("idx_users_role", "users", ["role"], unique=False)

    # Devices table
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("model_number", sa.String(50), nullable=True),
        sa.Column("test_config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Stations table
    op.create_table(
        "stations",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("station_type", postgresql.ENUM("intake", "reset", "functional", "qc", "completed", "failed", "on_hold", name="job_status", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("capabilities", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Jobs table
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("serial_number", sa.String(100), nullable=False),
        sa.Column("status", postgresql.ENUM("intake", "reset", "functional", "qc", "completed", "failed", "on_hold", name="job_status", create_type=False), nullable=False, server_default="intake"),
        sa.Column("current_station_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("assigned_technician_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("intake_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("intake_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reset_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reset_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("functional_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("functional_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("qc_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("qc_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("qc_technician_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qc_initials", sa.String(10), nullable=True),
        sa.Column("qc_notes", sa.Text(), nullable=True),
        sa.Column("batch_id", sa.String(100), nullable=True),
        sa.Column("customer_reference", sa.String(255), nullable=True),
        sa.Column("intake_condition", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["current_station_id"], ["stations.id"]),
        sa.ForeignKeyConstraint(["assigned_technician_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["qc_technician_id"], ["users.id"]),
    )
    op.create_index("idx_jobs_status", "jobs", ["status"], unique=False)
    op.create_index("idx_jobs_serial", "jobs", ["serial_number"], unique=False)
    op.create_index("idx_jobs_technician", "jobs", ["assigned_technician_id"], unique=False)
    op.create_index("idx_jobs_created", "jobs", ["created_at"], unique=False)

    # Test steps table
    op.create_table(
        "test_steps",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("station_type", postgresql.ENUM("intake", "reset", "functional", "qc", "completed", "failed", "on_hold", name="job_status", create_type=False), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_evidence", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("evidence_instructions", sa.Text(), nullable=True),
        sa.Column("criteria", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
    )

    # Test results table
    op.create_table(
        "test_results",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("test_step_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", postgresql.ENUM("pass", "fail", "skip", "pending", name="test_result_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("performed_by_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("measurements", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_step_id"], ["test_steps.id"]),
        sa.ForeignKeyConstraint(["performed_by_id"], ["users.id"]),
    )
    op.create_index("idx_test_results_job", "test_results", ["job_id"], unique=False)

    # Evidence table
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("test_result_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("evidence_type", postgresql.ENUM("photo", "video", "document", name="evidence_type", create_type=False), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("captured_by_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("superseded_by_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_result_id"], ["test_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["captured_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["superseded_by_id"], ["evidence.id"]),
    )
    op.create_index("idx_evidence_job", "evidence", ["job_id"], unique=False)
    op.create_index("idx_evidence_test_result", "evidence", ["test_result_id"], unique=False)
    op.create_index("idx_evidence_hash", "evidence", ["sha256_hash"], unique=False)

    # Reports table
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scope", postgresql.ENUM("master", "intake", "reset", "functional", "qc", name="report_scope", create_type=False), nullable=False),
        sa.Column("variant", postgresql.ENUM("customer", "internal", name="report_variant", create_type=False), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("access_token", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_by_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("access_token"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by_id"], ["users.id"]),
    )
    op.create_index("idx_reports_token", "reports", ["access_token"], unique=False)
    op.create_index("idx_reports_job", "reports", ["job_id"], unique=False)

    # Job history table
    op.create_table(
        "job_history",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("from_status", postgresql.ENUM("intake", "reset", "functional", "qc", "completed", "failed", "on_hold", name="job_status", create_type=False), nullable=True),
        sa.Column("to_status", postgresql.ENUM("intake", "reset", "functional", "qc", "completed", "failed", "on_hold", name="job_status", create_type=False), nullable=False),
        sa.Column("changed_by_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("station_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
    )
    op.create_index("idx_job_history_job", "job_history", ["job_id"], unique=False)
    op.create_index("idx_job_history_changed_at", "job_history", ["changed_at"], unique=False)


def downgrade() -> None:
    op.drop_table("job_history")
    op.drop_table("reports")
    op.drop_table("evidence")
    op.drop_table("test_results")
    op.drop_table("test_steps")
    op.drop_table("jobs")
    op.drop_table("stations")
    op.drop_table("devices")
    op.drop_table("users")

    op.execute("DROP TYPE report_variant")
    op.execute("DROP TYPE report_scope")
    op.execute("DROP TYPE evidence_type")
    op.execute("DROP TYPE test_result_status")
    op.execute("DROP TYPE job_status")
    op.execute("DROP TYPE user_role")

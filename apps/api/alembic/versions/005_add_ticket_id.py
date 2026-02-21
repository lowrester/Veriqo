"""add_ticket_id

Revision ID: 005
Revises: 004
Create Date: 2026-02-03 19:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '005_add_ticket_id'
down_revision = '004_add_imei_to_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add ticket_id column with Identity (auto-increment)
    # Start from 10001 to look like a "real" system ticket
    op.add_column('jobs', sa.Column('ticket_id', sa.Integer(), sa.Identity(start=10001, cycle=True), nullable=False))

    # Create unique index
    op.create_index(op.f('ix_jobs_ticket_id'), 'jobs', ['ticket_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_jobs_ticket_id'), table_name='jobs')
    op.drop_column('jobs', 'ticket_id')

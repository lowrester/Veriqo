"""add sla fields

Revision ID: 007_add_sla_fields
Revises: 006_add_integration_tables
Create Date: 2026-02-03 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '007_add_sla_fields'
down_revision = '006_add_integration_tables'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    bind = op.get_context().bind
    insp = inspect(bind)
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns

def upgrade() -> None:
    # 1. Add sla_hours to users
    if not column_exists('users', 'sla_hours'):
        op.add_column('users', sa.Column('sla_hours', sa.Integer(), nullable=True))

    # 2. Add sla_due_at to jobs
    if not column_exists('jobs', 'sla_due_at'):
        op.add_column('jobs', sa.Column('sla_due_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs', 'sla_due_at')
    op.drop_column('users', 'sla_hours')

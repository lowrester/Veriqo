"""add imei to jobs

Revision ID: 004_add_imei_to_jobs
Revises: 003_add_printing_tables
Create Date: 2026-02-03 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_imei_to_jobs'
down_revision: Union[str, None] = '003_add_printing_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add imei column to jobs table
    op.add_column('jobs', sa.Column('imei', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_jobs_imei'), 'jobs', ['imei'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_jobs_imei'), table_name='jobs')
    op.drop_column('jobs', 'imei')

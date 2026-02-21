"""Add manual completion overrides.

Revision ID: 011_manual_overrides
Revises: 010_normalize_device_structure
Create Date: 2026-02-20 09:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '011_manual_overrides'
down_revision: str | None = '010_normalize_device_structure'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add columns for manual override
    op.add_column('jobs', sa.Column('is_fully_tested', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('jobs', sa.Column('skip_reason', sa.Text(), nullable=True))

    # Add 'customer' to user_role enum
    # PostgreSQL requires separate transaction for ALTER TYPE ADD VALUE or specific handling
    op.execute("COMMIT") # End current transaction if any
    op.execute("ALTER TYPE user_role ADD VALUE 'customer'")


def downgrade() -> None:
    # Note: Removing enum values is complex in PG and usually not done in migrations
    op.drop_column('jobs', 'skip_reason')
    op.drop_column('jobs', 'is_fully_tested')

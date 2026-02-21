"""Refactor device model to separate brand and type.

Revision ID: 009_refactor_device_model
Revises: 008_add_inventory
Create Date: 2026-02-04 09:44:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009_refactor_device_model"
down_revision: str | None = "008_add_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # Rename platform to brand
    op.alter_column('devices', 'platform', new_column_name='brand')

    # Add device_type column
    op.add_column('devices', sa.Column('device_type', sa.String(length=50), nullable=True))

    # Update existing data
    # Based on existing patterns, we map these to reasonable types
    op.execute("UPDATE devices SET device_type = 'Console'")

    # Make device_type non-nullable
    op.alter_column('devices', 'device_type', nullable=False)

def downgrade() -> None:
    # Remove device_type column
    op.drop_column('devices', 'device_type')

    # Rename brand back to platform
    op.alter_column('devices', 'brand', new_column_name='platform')

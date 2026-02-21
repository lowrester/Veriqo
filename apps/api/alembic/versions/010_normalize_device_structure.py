"""Normalize device structure.

Revision ID: 010_normalize_device_structure
Revises: 009_refactor_device_model
Create Date: 2026-02-05 19:20:00.000000
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "010_normalize_device_structure"
down_revision: str | None = "009_refactor_device_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. Create brands table
    op.create_table(
        'brands',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('logo_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. Create gadget_types table
    op.create_table(
        'gadget_types',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 3. Add brand_id and type_id to devices (temporarily nullable)
    op.add_column('devices', sa.Column('brand_id', sa.String(length=36), nullable=True))
    op.add_column('devices', sa.Column('type_id', sa.String(length=36), nullable=True))

    # 4. Data Migration
    # Extract unique brands and gadget types, then link them
    connection = op.get_bind()

    # Migrate Brands
    brands = connection.execute(sa.text("SELECT DISTINCT brand FROM devices")).fetchall()
    for brand_row in brands:
        brand_name = brand_row[0]
        brand_id = str(uuid4())
        connection.execute(
            sa.text("INSERT INTO brands (id, name) VALUES (:id, :name)"),
            {"id": brand_id, "name": brand_name}
        )
        connection.execute(
            sa.text("UPDATE devices SET brand_id = :brand_id WHERE brand = :brand_name"),
            {"brand_id": brand_id, "brand_name": brand_name}
        )

    # Migrate Gadget Types
    types = connection.execute(sa.text("SELECT DISTINCT device_type FROM devices")).fetchall()
    for type_row in types:
        type_name = type_row[0]
        type_id = str(uuid4())
        connection.execute(
            sa.text("INSERT INTO gadget_types (id, name) VALUES (:id, :name)"),
            {"id": type_id, "name": type_name}
        )
        connection.execute(
            sa.text("UPDATE devices SET type_id = :type_id WHERE device_type = :type_name"),
            {"type_id": type_id, "type_name": type_name}
        )

    # 5. Finalize devices table
    # Make columns non-nullable
    op.alter_column('devices', 'brand_id', nullable=False)
    op.alter_column('devices', 'type_id', nullable=False)

    # Remove old columns
    op.drop_column('devices', 'brand')
    op.drop_column('devices', 'device_type')

    # Add foreign keys
    op.create_foreign_key('fk_devices_brand_id', 'devices', 'brands', ['brand_id'], ['id'])
    op.create_foreign_key('fk_devices_type_id', 'devices', 'gadget_types', ['type_id'], ['id'])

def downgrade() -> None:
    # Reverse process
    op.add_column('devices', sa.Column('brand', sa.String(length=50), nullable=True))
    op.add_column('devices', sa.Column('device_type', sa.String(length=50), nullable=True))

    connection = op.get_bind()

    # Restore brand strings
    connection.execute(
        sa.text("UPDATE devices SET brand = (SELECT name FROM brands WHERE brands.id = devices.brand_id)")
    )
    # Restore device_type strings
    connection.execute(
        sa.text("UPDATE devices SET device_type = (SELECT name FROM gadget_types WHERE gadget_types.id = devices.type_id)")
    )

    op.alter_column('devices', 'brand', nullable=False)
    op.alter_column('devices', 'device_type', nullable=False)

    op.drop_constraint('fk_devices_brand_id', 'devices', type_='foreignkey')
    op.drop_constraint('fk_devices_type_id', 'devices', type_='foreignkey')

    op.drop_column('devices', 'brand_id')
    op.drop_column('devices', 'type_id')

    op.drop_table('gadget_types')
    op.drop_table('brands')

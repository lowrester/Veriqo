"""add inventory tables

Revision ID: 008_add_inventory
Revises: 007_add_sla_fields
Create Date: 2026-02-03 20:45:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '008_add_inventory'
down_revision = '007_add_sla_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create parts table
    op.create_table('parts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity_on_hand', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku')
    )

    # Create part_usages table
    op.create_table('part_usages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('part_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id'], )
    )


def downgrade() -> None:
    op.drop_table('part_usages')
    op.drop_table('parts')

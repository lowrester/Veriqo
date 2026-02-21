"""Add printing tables

Revision ID: 003_add_printing_tables
Revises: 002_add_workflow_tables
Create Date: 2026-02-03 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '003_add_printing_tables'
down_revision = '002_add_workflow_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # label_templates table
    op.create_table(
        'label_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('zpl_code', sa.Text(), nullable=False),
        sa.Column('dimensions', sa.String(length=50), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    op.drop_table('label_templates')

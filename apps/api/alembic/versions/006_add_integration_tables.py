"""add integration tables

Revision ID: 006_add_integration_tables
Revises: 005_add_ticket_id
Create Date: 2026-02-03 20:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '006_add_integration_tables'
down_revision = '005_add_ticket_id'
branch_labels = None
depends_on = None

def table_exists(table_name):
    bind = op.get_context().bind
    insp = inspect(bind)
    return table_name in insp.get_table_names()

def upgrade() -> None:
    # 1. Create api_keys table
    if not table_exists('api_keys'):
        op.create_table('api_keys',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('key_prefix', sa.String(length=8), nullable=False),
            sa.Column('hashed_key', sa.String(), nullable=False),
            sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_by_id', sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('hashed_key')
        )
        op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)

    # 2. Create webhook_subscriptions table
    if not table_exists('webhook_subscriptions'):
        op.create_table('webhook_subscriptions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('url', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('events', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('secret_key', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('failure_count', sa.Integer(), nullable=False),
            sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by_id', sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_webhook_subscriptions_id'), 'webhook_subscriptions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('webhook_subscriptions')
    op.drop_table('api_keys')

"""add audit events and notifications

Works on BOTH a brand-new empty database and on the older shared Neon DB
that already had legacy `notifications` / `activity_logs` tables.

Revision ID: aaa631722147
Revises: 63718ff273fb
Create Date: 2026-09-25 11:43:47.122672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aaa631722147'
down_revision: Union[str, None] = '63718ff273fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_notifications_table() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('link_url', sa.String(length=500), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def _upgrade_legacy_notifications_table(existing_cols: set[str]) -> None:
    if 'link_url' not in existing_cols:
        op.add_column('notifications', sa.Column('link_url', sa.String(length=500), nullable=True))
    if 'read_at' not in existing_cols:
        op.add_column('notifications', sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
    op.alter_column('notifications', 'notification_type',
                    existing_type=sa.VARCHAR(length=30), type_=sa.String(length=50), existing_nullable=False)
    op.alter_column('notifications', 'title',
                    existing_type=sa.VARCHAR(length=150), type_=sa.String(length=200), existing_nullable=False)
    op.alter_column('notifications', 'created_at',
                    existing_type=postgresql.TIMESTAMP(), type_=sa.DateTime(timezone=True),
                    existing_nullable=False, existing_server_default=sa.text('now()'))
    op.execute('DELETE FROM notifications WHERE user_id IS NULL')
    op.alter_column('notifications', 'user_id', existing_type=sa.UUID(), nullable=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.execute('ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_related_file_id_fkey')
    op.execute('ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_user_id_fkey')
    op.create_foreign_key('notifications_user_id_fkey', 'notifications', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    if 'related_file_id' in existing_cols:
        op.drop_column('notifications', 'related_file_id')
    if 'is_read' in existing_cols:
        op.drop_column('notifications', 'is_read')


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    op.create_table(
        'audit_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('actor_user_id', sa.UUID(), nullable=True),
        sa.Column('target_user_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_events_actor_user_id'), 'audit_events', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_audit_events_created_at'), 'audit_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_events_event_type'), 'audit_events', ['event_type'], unique=False)

    # Legacy table, only present on the old shared DB.
    if 'activity_logs' in tables:
        op.drop_table('activity_logs')

    if 'notifications' in tables:
        cols = {c['name'] for c in inspector.get_columns('notifications')}
        _upgrade_legacy_notifications_table(cols)
    else:
        _create_notifications_table()


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_audit_events_event_type'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_created_at'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_actor_user_id'), table_name='audit_events')
    op.drop_table('audit_events')
"""Add integration tables

Revision ID: 001_add_integrations
Revises: 
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_integrations'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_integrations table
    op.create_table(
        'user_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('integration_type', sa.Enum('PLAID', 'ALPACA', 'SNAPTRADE', name='integrationtype'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'ERROR', 'EXPIRED', name='integrationstatus'), default='INACTIVE'),
        sa.Column('encrypted_credentials', sa.Text(), nullable=False),
        sa.Column('external_user_id', sa.String(), nullable=True),
        sa.Column('is_sandbox', sa.Boolean(), default=True),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_integrations_id'), 'user_integrations', ['id'], unique=False)
    op.create_index(op.f('ix_user_integrations_user_id'), 'user_integrations', ['user_id'], unique=False)
    
    # Create connected_accounts table
    op.create_table(
        'connected_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('external_account_id', sa.String(), nullable=False),
        sa.Column('account_name', sa.String(), nullable=True),
        sa.Column('account_type', sa.String(), nullable=True),
        sa.Column('account_subtype', sa.String(), nullable=True),
        sa.Column('institution_name', sa.String(), nullable=True),
        sa.Column('institution_id', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), default='USD'),
        sa.Column('available_balance', sa.String(), nullable=True),
        sa.Column('current_balance', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('sync_enabled', sa.Boolean(), default=True),
        sa.Column('last_successful_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['integration_id'], ['user_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_connected_accounts_id'), 'connected_accounts', ['id'], unique=False)
    
    # Create users table for authentication
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_connected_accounts_id'), table_name='connected_accounts')
    op.drop_table('connected_accounts')
    
    op.drop_index(op.f('ix_user_integrations_user_id'), table_name='user_integrations')
    op.drop_index(op.f('ix_user_integrations_id'), table_name='user_integrations')
    op.drop_table('user_integrations')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS integrationtype")
    op.execute("DROP TYPE IF EXISTS integrationstatus")

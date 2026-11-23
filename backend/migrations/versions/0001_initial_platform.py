"""Initial SaaS platform and tenant foundation."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_platform"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_name", sa.String(180), nullable=False), sa.Column("owner_name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(254), nullable=False), sa.Column("mobile", sa.String(24), nullable=False),
        sa.Column("district", sa.String(100), nullable=False), sa.Column("domain", sa.String(253)),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"), sa.UniqueConstraint("domain"))
    op.create_index("ix_tenants_email", "tenants", ["email"])
    op.create_index("ix_tenants_status", "tenants", ["status"])
    op.create_table("plans",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(80), nullable=False),
        sa.Column("monthly_price_paise", sa.Integer(), nullable=False), sa.Column("annual_price_paise", sa.Integer(), nullable=False),
        sa.Column("trial_days", sa.Integer(), nullable=False), sa.Column("max_users", sa.Integer(), nullable=False),
        sa.Column("max_staff", sa.Integer(), nullable=False), sa.Column("max_agents", sa.Integer(), nullable=False),
        sa.Column("storage_limit_mb", sa.Integer(), nullable=False), sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False), sa.UniqueConstraint("name"))
    op.create_table("admin_users",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE")),
        sa.Column("email", sa.String(254), nullable=False), sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", sa.String(32), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False), sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("tenant_id", "email", name="ix_admin_users_tenant_email"))
    op.create_index("ix_admin_users_tenant_id", "admin_users", ["tenant_id"])
    op.create_table("tenant_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False), sa.Column("status", sa.String(24), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("custom_price_paise", sa.Integer()))
    op.create_index("ix_tenant_subscription_scope", "tenant_subscriptions", ["tenant_id", "status"])
    op.create_table("refresh_sessions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("token_hash"))
    op.create_index("ix_refresh_sessions_admin_user_id", "refresh_sessions", ["admin_user_id"])
    op.create_index("ix_refresh_sessions_token_hash", "refresh_sessions", ["token_hash"])
    op.create_table("audit_events",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("admin_users.id", ondelete="SET NULL")),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="SET NULL")), sa.Column("action", sa.String(100), nullable=False),
        sa.Column("module", sa.String(80), nullable=False), sa.Column("record_id", sa.String(120)), sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("ip_address", sa.String(45)), sa.Column("user_agent", sa.String(512)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_scope_time", "audit_events", ["tenant_id", "created_at"])


def downgrade():
    op.drop_table("audit_events")
    op.drop_table("refresh_sessions")
    op.drop_table("tenant_subscriptions")
    op.drop_table("admin_users")
    op.drop_table("plans")
    op.drop_table("tenants")

import pytest

from app.core.tenant_context import TenantContext, ensure_tenant_scope


def test_tenant_user_can_only_use_own_tenant_scope():
    context = TenantContext(tenant_id=8, role="tenant_admin", permissions=frozenset({"users.view"}))
    ensure_tenant_scope(context, 8)
    with pytest.raises(PermissionError):
        ensure_tenant_scope(context, 9)


def test_super_admin_scope_is_explicitly_platform_wide():
    context = TenantContext(tenant_id=0, role="super_admin", permissions=frozenset({"*"}))
    ensure_tenant_scope(context, 9)

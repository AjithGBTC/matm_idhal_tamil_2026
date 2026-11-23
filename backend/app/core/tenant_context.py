from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: int
    role: str
    permissions: frozenset[str]

    def allows(self, permission: str) -> bool:
        return "*" in self.permissions or permission in self.permissions


def ensure_tenant_scope(context: TenantContext, requested_tenant_id: int) -> None:
    if context.role != "super_admin" and context.tenant_id != requested_tenant_id:
        raise PermissionError("Tenant resource is outside the authenticated tenant scope")

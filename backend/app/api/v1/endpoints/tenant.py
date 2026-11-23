from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_principal
from app.core.database import get_db
from app.models import AdminUser, Tenant, TenantSubscription

router = APIRouter()


def tenant_principal(principal: dict = Depends(get_current_principal)) -> dict:
    if principal["role"] == "super_admin" or principal["tenant_id"] is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A tenant staff account is required")
    if "*" not in principal["permissions"] and "tenant.dashboard.view" not in principal["permissions"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
    return principal


@router.get("/dashboard")
def tenant_dashboard(principal: dict = Depends(tenant_principal), db: Session = Depends(get_db)):
    tenant_id = principal["tenant_id"]
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    staff_count = db.scalar(select(func.count(AdminUser.id)).where(AdminUser.tenant_id == tenant_id)) or 0
    subscriptions = db.scalar(select(func.count(TenantSubscription.id)).where(TenantSubscription.tenant_id == tenant_id, TenantSubscription.status.in_(["active", "trial"]))) or 0
    return {"tenant": {"id": tenant.id, "business_name": tenant.business_name, "status": tenant.status}, "staff_count": staff_count, "subscriptions": subscriptions}

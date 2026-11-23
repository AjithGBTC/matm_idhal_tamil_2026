from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field, SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.security import hash_password
from app.models import AdminUser, AuditEvent, Plan, Tenant, TenantSubscription

router = APIRouter()


class TenantCreate(BaseModel):
    business_name: str = Field(min_length=2, max_length=180)
    owner_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    mobile: str = Field(min_length=7, max_length=24)
    district: str = Field(min_length=2, max_length=100)
    plan_id: int
    initial_password: SecretStr = Field(min_length=12, max_length=128)


class PlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    monthly_price_paise: int = Field(ge=0)
    annual_price_paise: int = Field(ge=0)
    trial_days: int = Field(ge=0, le=365)
    max_users: int = Field(ge=1)
    max_staff: int = Field(ge=1)
    max_agents: int = Field(ge=0)
    storage_limit_mb: int = Field(ge=1)
    features: dict[str, bool] = Field(default_factory=dict)


@router.get("/overview", dependencies=[Depends(require_permission("platform.dashboard.view"))])
def overview(db: Session = Depends(get_db)):
    tenant_counts = dict(db.execute(select(Tenant.status, func.count(Tenant.id)).group_by(Tenant.status)).all())
    subscription_count = db.scalar(select(func.count(TenantSubscription.id)).where(TenantSubscription.status == "active")) or 0
    plan_distribution = db.execute(select(Plan.name, func.count(TenantSubscription.id)).outerjoin(TenantSubscription, (TenantSubscription.plan_id == Plan.id) & (TenantSubscription.status.in_(["active", "trial"]))).where(Plan.is_active.is_(True)).group_by(Plan.id, Plan.name).order_by(Plan.monthly_price_paise)).all()
    return {"tenants": {"total": sum(tenant_counts.values()), "active": tenant_counts.get("active", 0), "inactive": tenant_counts.get("inactive", 0), "trial": tenant_counts.get("trial", 0), "pending": tenant_counts.get("pending", 0)}, "active_subscriptions": subscription_count, "plan_distribution": [{"plan": name, "subscriptions": count} for name, count in plan_distribution], "monthly_recurring_revenue_paise": None, "pending_payments": None, "generated_at": datetime.now(timezone.utc).isoformat()}


@router.get("/tenants", dependencies=[Depends(require_permission("tenants.view"))])
def list_tenants(q: str | None = Query(default=None, max_length=120), page: int = Query(default=1, ge=1), page_size: int = Query(default=25, ge=1, le=100), db: Session = Depends(get_db)):
    filters = []
    if q:
        filters.append(Tenant.business_name.ilike(f"%{q}%"))
    total = db.scalar(select(func.count(func.distinct(Tenant.id))).where(*filters)) or 0
    latest_subscription_id = select(TenantSubscription.id).where(TenantSubscription.tenant_id == Tenant.id).order_by(TenantSubscription.starts_at.desc(), TenantSubscription.id.desc()).limit(1).scalar_subquery()
    query = select(Tenant, Plan.name, Plan.monthly_price_paise).outerjoin(TenantSubscription, TenantSubscription.id == latest_subscription_id).outerjoin(Plan, Plan.id == TenantSubscription.plan_id).where(*filters)
    rows = db.execute(query.order_by(Tenant.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"id": t.id, "business_name": t.business_name, "owner_name": t.owner_name, "email": t.email, "mobile": t.mobile, "district": t.district, "status": t.status, "created_at": t.created_at, "plan_name": plan_name, "monthly_price_paise": monthly_price} for t, plan_name, monthly_price in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def create_tenant(body: TenantCreate, request: Request, principal: dict = Depends(require_permission("tenants.create")), db: Session = Depends(get_db)):
    if db.scalar(select(Tenant.id).where(Tenant.email == body.email.lower())):
        raise HTTPException(status_code=409, detail="A tenant already uses this email")
    plan = db.get(Plan, body.plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=422, detail="Select an active plan")
    tenant = Tenant(business_name=body.business_name, owner_name=body.owner_name, email=body.email.lower(), mobile=body.mobile, district=body.district, status="pending")
    db.add(tenant)
    db.flush()
    admin = AdminUser(tenant_id=tenant.id, email=body.email.lower(), full_name=body.owner_name, password_hash=hash_password(body.initial_password.get_secret_value()), role="tenant_admin", permissions=["tenant.dashboard.view", "users.view", "users.create", "users.update", "profiles.view", "reports.view"], is_active=True)
    db.add(admin)
    db.add(TenantSubscription(tenant_id=tenant.id, plan_id=plan.id, status="trial"))
    db.add(AuditEvent(actor_id=principal["id"], tenant_id=tenant.id, action="tenant_created", module="tenants", record_id=str(tenant.id), ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")))
    db.commit()
    db.refresh(tenant)
    return {"id": tenant.id, "business_name": tenant.business_name, "email": tenant.email, "status": tenant.status}


@router.get("/plans", dependencies=[Depends(require_permission("plans.view"))])
def list_plans(db: Session = Depends(get_db)):
    rows = db.scalars(select(Plan).order_by(Plan.monthly_price_paise)).all()
    return [{"id": p.id, "name": p.name, "monthly_price_paise": p.monthly_price_paise, "annual_price_paise": p.annual_price_paise, "trial_days": p.trial_days, "max_users": p.max_users, "max_staff": p.max_staff, "max_agents": p.max_agents, "storage_limit_mb": p.storage_limit_mb, "features": p.features, "is_active": p.is_active} for p in rows]


@router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_plan(body: PlanCreate, principal: dict = Depends(require_permission("plans.create")), db: Session = Depends(get_db)):
    if db.scalar(select(Plan.id).where(Plan.name == body.name)):
        raise HTTPException(status_code=409, detail="Plan name already exists")
    plan = Plan(**body.model_dump())
    db.add(plan)
    db.add(AuditEvent(actor_id=principal["id"], action="plan_created", module="plans", details={"name": body.name}))
    db.commit()
    db.refresh(plan)
    return {"id": plan.id, "name": plan.name, "is_active": plan.is_active}

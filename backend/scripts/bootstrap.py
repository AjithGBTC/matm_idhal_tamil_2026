"""Create initial SaaS plans and a first super admin after applying migrations."""
import argparse
from getpass import getpass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import AdminUser, Plan

PLANS = [
    {"name": "Starter", "monthly_price_paise": 299900, "annual_price_paise": 2999000, "trial_days": 14, "max_users": 1000, "max_staff": 3, "max_agents": 2, "storage_limit_mb": 5120, "features": {"website_access": True, "admin_panel": True}},
    {"name": "Professional", "monthly_price_paise": 749900, "annual_price_paise": 7499000, "trial_days": 14, "max_users": 5000, "max_staff": 10, "max_agents": 10, "storage_limit_mb": 20480, "features": {"website_access": True, "admin_panel": True, "agent_management": True, "horoscope_matching": True}},
    {"name": "Business", "monthly_price_paise": 1249900, "annual_price_paise": 12499000, "trial_days": 14, "max_users": 20000, "max_staff": 30, "max_agents": 50, "storage_limit_mb": 102400, "features": {"website_access": True, "admin_panel": True, "agent_management": True, "horoscope_matching": True, "advanced_analytics": True, "custom_branding": True}},
    {"name": "Enterprise", "monthly_price_paise": 2499900, "annual_price_paise": 24999000, "trial_days": 30, "max_users": 100000, "max_staff": 200, "max_agents": 500, "storage_limit_mb": 512000, "features": {"website_access": True, "admin_panel": True, "agent_management": True, "horoscope_matching": True, "advanced_analytics": True, "custom_branding": True, "custom_domain": True, "api_access": True, "payment_integration": True}},
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Super admin display name")
    parser.add_argument("--email", required=True, help="Super admin email address")
    args = parser.parse_args()
    password = getpass("Initial password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password must have at least 12 characters")
    with SessionLocal.begin() as db:
        if db.scalar(select(func.count()).select_from(AdminUser).where(AdminUser.role == "super_admin")):
            raise SystemExit("A super admin already exists; bootstrap is first-admin only")
        email = args.email.strip().lower()
        db.add(AdminUser(tenant_id=None, email=email, full_name=args.name, password_hash=hash_password(password), role="super_admin", permissions=["*"], is_active=True))
        for values in PLANS:
            existing = db.scalar(select(Plan.id).where(Plan.name == values["name"]))
            if existing is None:
                db.add(Plan(**values))
    print(f"Super admin created for {args.email}; standard plans are ready.")


if __name__ == "__main__":
    main()

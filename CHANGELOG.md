# Changelog

## 0.1.0 — Initial foundation

- Recorded the repository inspection, database/tenant architecture, and staged API/module plan.
- Added React/Vite Super Admin sign-in, live tenant and plan views, tenant creation, and responsive admin workspace shell.
- Added FastAPI JWT access/refresh authentication, refresh rotation and revocation, account lockout, permissions, tenant-scoped dashboard route, and platform endpoints.
- Added SQLAlchemy tenant, admin, plan, subscription, refresh-session, and audit models plus the first Alembic migration.
- Added a first-admin and standard-plan bootstrap command, setup documentation, and initial RBAC/tenant-scope tests.
- Left member/profile, payments, integrations, advanced reporting, and tenant lifecycle editing for subsequent phases; unavailable metrics are shown as unavailable rather than invented.

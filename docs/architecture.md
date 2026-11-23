# Architecture and implementation plan

## Existing project structure analysis

The workspace was empty apart from `.venv`; it had no application sources, package manifests, tests, migrations, or existing schema. This is therefore a greenfield implementation. FastAPI is present in the supplied environment, while SQLAlchemy and frontend dependencies need to be installed from the manifests.

## Database architecture

Use MySQL 8 in deployed environments and SQLAlchemy models with Alembic migrations. Global SaaS entities include tenants, SaaS plans, tenant subscriptions, platform admins, permission roles, refresh sessions, and audit events. Tenant-owned entities (members, profiles, staff, agents, payments, membership plans, messages, and moderation records) carry a non-null `tenant_id`, indexed alongside common lookup fields. Foreign keys that join tenant-owned data should include tenant scope where practical. Repository/service methods always take a resolved tenant context, and authorization dependencies reject cross-tenant identifiers before returning data. No tenant ID is accepted as authority from a client header; it is derived from the authenticated principal and verified host mapping. Financial writes use transactions and idempotency keys. Sensitive document blobs live in private object storage; only metadata and protected object references are stored in SQL.

## Multi-tenant architecture

One API and database serve multiple tenants. A verified hostname maps to a tenant. Login identifies the principal and role; the backend constructs a request-scoped tenant context. Tenant staff can access only that context and their assigned records. Super-admin routes require explicit platform permissions and use auditable, intentional cross-tenant queries. All tenant-facing repository queries filter by `tenant_id`; authorization is enforced on every API request, independent of frontend navigation.

## Module implementation plan

1. Foundation: configuration, database session, tenant and account models, password hashing, access/refresh tokens, RBAC dependencies, audit records, and tenant isolation.
2. SaaS operations: super-admin overview, tenant lifecycle, plan catalog, subscriptions, and billing records.
3. Tenant operations: dashboard, member/profile records, moderation, photos, and identity verification.
4. Matrimony workflows: search, matches, interests, horoscope configuration, member subscriptions.
5. Business operations: payments, agents, staff, roles, and permission administration.
6. Engagement: notifications, CMS, coupons, events, astrologers, support.
7. Platform: analytics, reports/exports, audit views, white-label settings, Tamil Nadu master data.
8. Hardening: automated unit/API/RBAC/tenant-isolation and frontend tests, payment integration verification, performance and deployment work.

## API implementation plan

Version APIs under `/api/v1`. Public authentication endpoints handle login, refresh rotation, logout, password recovery, and verification. `/super-admin/*` endpoints require platform-scoped permissions. `/tenant/*` endpoints derive tenant scope from authenticated context and expose paginated resources for dashboard, members, profiles, moderation, plans, payments, agents, staff, settings, and reports. Shared request schemas validate input; consistent error and pagination schemas make contracts predictable. OpenAPI/Swagger is supplied by FastAPI. Payment webhooks are isolated from browser routes and verified using provider signatures. Data exports are permission-gated, tenant-filtered, and audited.

## Current implementation status

This initial slice provides a Super Admin sign-in, tenant overview/list/create flow, plan catalog view, tenant-scoped dashboard endpoint, FastAPI OpenAPI docs, SQLAlchemy platform models, token refresh/revocation, account lockout, permission checks, audit events, bootstrap command, and the initial Alembic migration. The revenue and member metrics are intentionally shown as unavailable until those modules have real tables and API sources.

Not implemented yet: matrimony member/profile records, moderation and identity document workflows, payments and invoices, detailed plan editing/lifecycle controls, subscriptions/billing history, staff and agent workflows, notifications, reports/exports, domain verification, and production integrations. The interface marks unfinished areas as scheduled modules rather than presenting placeholder records as live data. The next development pass should continue with tenant and plan lifecycle operations, then tenant member/profile management.

Integrations that need credentials (email, SMS, payments, object storage) remain adapter points until configured. The local dependency install could not complete in this workspace because package registry TLS verification failed; run the listed install commands in an environment with registry access before starting the services.


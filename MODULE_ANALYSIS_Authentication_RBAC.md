## Authentication & RBAC Module — API/Feature Analysis

Files reviewed:
- `apps/api/app/api/v1/auth.py`
- `apps/api/app/models/user.py`
- `apps/api/app/models/rbac.py`
- `apps/api/app/services/rbac_service.py`
- `apps/api/app/services/user_service.py`
- `apps/api/app/core/init_rbac.py`
- `apps/api/app/dependencies.py`

### User-facing and API-level functionalities

- **User login (session token issuance)**: `POST /api/v1/auth/login` authenticates by username or email + password, returns session token, roles, and permissions; records audit logs.
- **User logout (session invalidation)**: `POST /api/v1/auth/logout` revokes the active session token and logs the event.
- **Get current user profile**: `GET /api/v1/auth/me` returns the authenticated user's profile, roles, permissions, and timestamps.
- **Change current user's password**: `POST /api/v1/auth/change-password` verifies current password and updates to a new hashed password; resets account lock/failed attempts; audit logged.
- **Create user (admin)**: `POST /api/v1/auth/users` creates a user with optional roles and client context (multi-tenant fields), returns full user profile.
- **List users (admin)**: `GET /api/v1/auth/users` returns all users with roles/permissions summarised.
- **Get user by id (admin)**: `GET /api/v1/auth/users/{user_id}` returns a specific user's profile with roles/permissions.
- **Update user roles (admin)**: `PUT /api/v1/auth/users/{user_id}/roles` replaces a user's roles and audit-logs the role change.
- **Create client user (admin)**: `POST /api/v1/auth/clients/users` creates an external client user bound to `client_id`/`client_organization` with the `client` role.
- **List client users (admin)**: `GET /api/v1/auth/clients/{client_id}/users` lists users scoped to a specific client organization.
- **List roles (system admin)**: `GET /api/v1/auth/roles` lists all roles with their attached permissions.
- **List permissions (system admin)**: `GET /api/v1/auth/permissions` lists all defined permissions.
- **Permission guard utilities**: `require_auth` and `require_permission(PermissionType)` FastAPI dependencies enforce authentication and fine-grained RBAC on endpoints.
- **Session validation & refresh**: Session tokens validated server-side with last-accessed timestamp updates to keep sessions fresh until expiration.
- **Audit logging of auth events**: All login/logout/denials/role changes recorded in `audit_logs` with context (IP, user agent, success flag, details).
- **Account lockout policy**: Failed login attempts increment and can lock the account after threshold; reset on successful login or password change.
- **RBAC bootstrap & admin seeding**: `init_rbac_system` creates default permissions, roles, and a default admin user (credentials configurable via env).
- **Role/permission catalog**: Enumerated `RoleType` and `PermissionType` define consistent, granular capabilities across pipeline, agents, reports, config, and client portal.
- **Multi-tenancy access checks (service)**: Helpers to enforce per-client access (admins unrestricted; client users restricted to their `client_id`).



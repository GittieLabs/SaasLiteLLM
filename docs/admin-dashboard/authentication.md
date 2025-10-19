# Admin Dashboard Authentication

Learn how to authenticate with the Admin Dashboard using JWT tokens with role-based access control (RBAC) or legacy MASTER_KEY authentication.

## Overview

The Admin Dashboard now uses **JWT (JSON Web Token) authentication** with role-based access control. This provides secure, session-based authentication with proper user management, audit logging, and granular permissions.

**Two authentication methods are supported:**

1. **JWT Bearer Token (Preferred)**: Email/password login with role-based permissions
2. **Legacy X-Admin-Key (Backward Compatibility)**: Direct MASTER_KEY authentication

!!! info "JWT Authentication Benefits"
    - **User Management**: Create admin users with different roles (owner, admin, user)
    - **Session Tracking**: Track active sessions, revoke access, monitor activity
    - **Audit Logging**: Complete audit trail of all admin actions
    - **Role-Based Access Control**: Fine-grained permissions based on user roles
    - **Secure**: Password hashing, token expiration, session revocation

!!! warning "Admin vs Team Authentication"
    - **Admin JWT/X-Admin-Key**: Admin access to dashboard and management APIs
    - **Virtual Keys**: Team access to make LLM requests (via `Authorization: Bearer sk-team-key`)

    These are completely separate authentication systems!

## New JWT Authentication System

### Initial Setup

#### 1. First-Time Owner Account Creation

When no users exist, the setup endpoint allows creating the first owner account:

![Admin Setup](../images/admin-setup.png)
*First-time admin setup screen - create your owner account*

**URL**: `POST /api/admin-users/setup`

**No authentication required** (only works when no users exist)

```bash
curl -X POST http://localhost:8004/api/admin-users/setup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "display_name": "Admin User",
    "password": "SecurePassword123!"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "...",
    "email": "admin@example.com",
    "display_name": "Admin User",
    "role": "owner",
    "is_active": true,
    "created_at": "2025-10-15T...",
    "last_login": "2025-10-15T..."
  }
}
```

#### 2. Login Flow

After setup, users login with email/password:

**URL**: `POST /api/admin-users/login`

```bash
curl -X POST http://localhost:8004/api/admin-users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "...",
    "email": "admin@example.com",
    "display_name": "Admin User",
    "role": "owner",
    "is_active": true
  }
}
```

Store the `access_token` and include it in subsequent requests:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8004/api/admin-users/me
```

### User Roles

Three roles with different permission levels:

| Role | Permissions |
|------|-------------|
| **owner** | Full access to all features, can create/modify/delete any user |
| **admin** | Manage organizations, teams, models, credits. Can create 'user' role accounts but not owners/admins |
| **user** | Read-only access to dashboard, can view but not modify resources |

### Role-Based Endpoint Access

```python
# All admin users can access (owner, admin, user)
GET /api/admin-users/me

# Owner and admin can access
GET /api/admin-users
POST /api/admin-users
PUT /api/admin-users/{id}
DELETE /api/admin-users/{id}

# Role restrictions enforced:
# - Admins can only create "user" role
# - Admins cannot modify owner/admin users
# - Owners have no restrictions
```

## Admin Dashboard Login

### 1. Navigate to Dashboard

Open the admin dashboard URL:

```
http://localhost:3002  (local)
https://admin.your-saas.com  (production)
```

### 2. Setup Detection

The dashboard automatically checks if setup is needed:

```http
GET /api/admin-users/setup/status
```

Response:
```json
{
  "needs_setup": false,
  "has_users": true
}
```

If `needs_setup: true`, the dashboard shows the setup form. Otherwise, shows login.

### 3. Login/Setup

**Setup Screen** (first time):
- Enter email, display name, and password
- Creates owner account automatically
- Returns JWT token and redirects to dashboard

**Login Screen** (subsequent):
- Enter email and password
- Validates credentials and returns JWT token
- Token stored in localStorage
- Redirects to dashboard

### 4. Authenticated Requests

All subsequent API requests include the JWT token:

```typescript
// admin-panel/lib/api-client.ts
const token = localStorage.getItem('authToken');

const response = await fetch(`${API_URL}${endpoint}`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
```

## Legacy X-Admin-Key Authentication

For backward compatibility, the old MASTER_KEY authentication still works:

```bash
curl -H "X-Admin-Key: sk-admin-local-dev-change-in-production" \
  http://localhost:8004/api/teams
```

**Use Cases for Legacy Auth:**
- Existing scripts/integrations not yet updated
- CI/CD pipelines
- Server-to-server communication
- Temporary admin access

**Migration Path:**
1. Create admin user accounts via JWT system
2. Update scripts to use JWT tokens
3. Eventually deprecate X-Admin-Key (not yet scheduled)

## Protected Endpoints

### JWT-Only Endpoints

User management requires JWT authentication:

```bash
# List users (requires owner or admin role)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/admin-users

# Create user (requires owner or admin role)
curl -X POST http://localhost:8004/api/admin-users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "display_name": "New User",
    "password": "SecurePass123!",
    "role": "user"
  }'

# Get current user info
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/admin-users/me

# Logout (revokes current session)
curl -X POST http://localhost:8004/api/admin-users/logout \
  -H "Authorization: Bearer $TOKEN"

# View audit logs (requires owner or admin role)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/admin-users/audit-logs
```

### Dual Authentication Endpoints

Management endpoints support both JWT and X-Admin-Key:

#### Organization Management
```bash
# JWT (preferred)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/organizations

# Legacy X-Admin-Key (still works)
curl -H "X-Admin-Key: sk-admin-local-dev-change-in-production" \
  http://localhost:8004/api/organizations
```

#### Team Management
```bash
# JWT
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/teams

# Legacy
curl -H "X-Admin-Key: $MASTER_KEY" \
  http://localhost:8004/api/teams
```

#### Model Group Management
```bash
# JWT
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/model-groups

# Legacy
curl -H "X-Admin-Key: $MASTER_KEY" \
  http://localhost:8004/api/model-groups
```

#### Credit Management
```bash
# JWT
curl -X POST http://localhost:8004/api/credits/teams/team_engineering/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"credits": 100, "reason": "Monthly allocation"}'

# Legacy
curl -X POST http://localhost:8004/api/credits/teams/team_engineering/add \
  -H "X-Admin-Key: $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"credits": 100, "reason": "Monthly allocation"}'
```

## Session Management

### JWT Token Details

- **Expiration**: 24 hours from creation
- **Storage**: Database session tracking with token hash
- **Revocation**: Sessions can be revoked via logout endpoint
- **Validation**: Every request checks session validity

### Session Tracking

Each login creates a session record:

```python
# Database: admin_sessions table
session = AdminSession(
    user_id=user.user_id,
    token_hash=create_token_hash(token),  # SHA256 hash
    expires_at=datetime.utcnow() + timedelta(hours=24),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    is_revoked=False
)
```

### Auto-Logout

The frontend automatically logs out on:
- JWT token expiration (401 response)
- Session revocation
- Manual logout

```typescript
// admin-panel/lib/api-client.ts
if (response.status === 401) {
  localStorage.removeItem('authToken');
  localStorage.removeItem('user');
  window.location.href = '/login';
}
```

## Audit Logging

All admin actions are logged:

```bash
# View audit logs
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8004/api/admin-users/audit-logs?limit=50"
```

**Logged Actions:**
- setup_owner, login, logout
- created_user, updated_user, deleted_user
- changed_password
- All actions include IP address, timestamp, user_id, and details

**Response:**

```json
[
  {
    "audit_id": "...",
    "user_id": "...",
    "action": "created_user",
    "resource_type": "admin_user",
    "resource_id": "...",
    "details": {
      "email": "newuser@example.com",
      "role": "user"
    },
    "ip_address": "127.0.0.1",
    "created_at": "2025-10-15T..."
  }
]
```

## Security Best Practices

### 1. Strong Passwords

Enforce password requirements:
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not common/dictionary words
- Unique per user

### 2. JWT Secret Key

The JWT secret is derived from MASTER_KEY:

```bash
# .env
MASTER_KEY=sk-admin-GENERATE-SECURE-KEY-HERE

# JWT secret is: MASTER_KEY value
# Tokens signed with HS256 algorithm
```

**Generate secure MASTER_KEY:**
```bash
openssl rand -hex 32
# Use output: sk-admin-<generated-hex>
```

### 3. Environment Separation

Use different keys for each environment:

```bash
# Development
MASTER_KEY=sk-admin-dev-key-here

# Staging
MASTER_KEY=sk-admin-staging-key-here

# Production
MASTER_KEY=sk-admin-prod-key-here
```

### 4. User Management

**Best Practices:**
- Create individual accounts for each admin
- Use appropriate roles (don't make everyone owner)
- Deactivate users when they leave
- Regular audit log reviews
- Password rotation policy

### 5. Session Security

- HTTPS only in production
- Short token expiration (24 hours)
- Session revocation on logout
- IP and user agent tracking
- Monitor for suspicious activity

## Setting Up MASTER_KEY

### Local Development

1. **Copy `.env.example` to `.env`**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and set MASTER_KEY**:
   ```bash
   MASTER_KEY=sk-admin-local-dev-change-in-production
   ```

3. **Restart the SaaS API**:
   ```bash
   python3 -m uvicorn src.saas_api:app --port 8004 --reload
   ```

### Production (Railway)

1. **Go to Railway Dashboard**:
   - Select your SaaS API service
   - Navigate to "Variables" tab

2. **Add MASTER_KEY variable**:
   ```bash
   MASTER_KEY=sk-admin-GENERATE-SECURE-KEY-HERE
   ```

3. **Generate a secure key**:
   ```bash
   openssl rand -hex 32
   # Use output: sk-admin-<generated-hex>
   ```

4. **Deploy**:
   - Railway auto-deploys on variable changes

### Admin Panel Configuration

The admin panel needs the API URL:

```bash
# admin-panel/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8004
```

## Troubleshooting

### "Invalid credentials" on Login

**Problem**: Login fails with invalid credentials

**Solutions**:
1. Verify email is correct (case-sensitive)
2. Check password (minimum 8 characters)
3. Ensure user account exists and is active
4. Check if setup is needed: `GET /api/admin-users/setup/status`

### "Setup already completed"

**Problem**: Trying to access setup when users exist

**Solution**: Use the login endpoint instead of setup

### "Token expired" Error

**Problem**: JWT token has expired (24 hour lifetime)

**Solution**: Login again to get a new token

### "Insufficient permissions"

**Problem**: User role doesn't have access to endpoint

**Solutions**:
1. Check user role: `GET /api/admin-users/me`
2. Verify role requirements for endpoint
3. Contact owner to upgrade role if needed

### Legacy Auth Not Working

**Problem**: X-Admin-Key authentication fails

**Solutions**:
1. Verify MASTER_KEY is set in environment
2. Check for typos in header name: `X-Admin-Key`
3. Restart API after changing MASTER_KEY
4. Test with curl:
   ```bash
   curl -H "X-Admin-Key: $MASTER_KEY" \
     http://localhost:8004/api/model-groups
   ```

## Migration from Legacy to JWT

### Step 1: Create Admin Users

```bash
# Setup owner account (first time)
curl -X POST http://localhost:8004/api/admin-users/setup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "display_name": "Admin User",
    "password": "SecurePassword123!"
  }'

# Create additional admin users
curl -X POST http://localhost:8004/api/admin-users \
  -H "Authorization: Bearer $OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "display_name": "Team User",
    "password": "SecurePass456!",
    "role": "admin"
  }'
```

### Step 2: Update Scripts

Replace X-Admin-Key with JWT tokens:

```python
# Old method
headers = {
    "X-Admin-Key": "sk-admin-local-dev-change-in-production"
}

# New method
# 1. Login once
login_response = requests.post(
    "http://localhost:8004/api/admin-users/login",
    json={
        "email": "admin@example.com",
        "password": "SecurePassword123!"
    }
)
token = login_response.json()["access_token"]

# 2. Use token for subsequent requests
headers = {
    "Authorization": f"Bearer {token}"
}
```

### Step 3: Update Dashboard

The admin panel automatically supports JWT. Just login with email/password.

### Step 4: Monitor Legacy Usage

Check audit logs to see if X-Admin-Key is still being used:

```bash
# JWT requests are logged with user_id
# Legacy requests have no user_id in logs
```

## Testing

The JWT authentication system has been thoroughly tested with comprehensive integration tests:

**Test Script**: `scripts/test_jwt_integration.py`

**What's Tested**:
- Setup/login flows
- JWT and legacy authentication
- Dual auth on all endpoints
- Role-based access control
- Security features
- Session management
- Audit logging

**Test Results**: All 12 integration tests passed (100% success rate)

For detailed test information, see:
- **[Integration Tests Documentation](../testing/integration-tests.md)** - How to run the tests
- **[Integration Test Results](../INTEGRATION_TEST_RESULTS.md)** - Detailed test results

## Next Steps

Now that you understand admin authentication:

1. **[User Management](user-management.md)** - Manage admin users and roles
2. **[Manage Organizations](organizations.md)** - Create and configure organizations
3. **[Manage Teams](teams.md)** - Set up teams with virtual keys
4. **[Configure Model Access](model-access-groups.md)** - Control model permissions
5. **[Monitor Usage](monitoring.md)** - Track system activity

## Additional Resources

- **[Environment Variables Guide](../deployment/environment-variables.md)** - Complete env var reference
- **[Team Authentication](../integration/authentication.md)** - How teams authenticate (different from admin)
- **[API Reference: Admin Users](../api-reference/admin-users.md)** - Complete API documentation
- **[Integration Tests](../testing/integration-tests.md)** - Testing the authentication system

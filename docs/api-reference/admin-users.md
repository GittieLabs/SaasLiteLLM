# Admin Users API Reference

Complete API reference for admin user management, JWT authentication, and audit logging endpoints.

## Authentication

All admin user endpoints (except `/setup` and `/login`) require authentication via:

1. **JWT Bearer Token** (Preferred):
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **Legacy X-Admin-Key** (Management endpoints only):
   ```
   X-Admin-Key: sk-admin-your-master-key
   ```

!!! note "JWT vs Legacy Auth"
    - User management endpoints (admin-users, audit logs) require JWT authentication
    - Management endpoints (organizations, teams, credits) support both JWT and X-Admin-Key

## Setup & Authentication Endpoints

### Check Setup Status

Check if initial setup is needed (i.e., if any admin users exist).

**Endpoint**: `GET /api/admin-users/setup/status`

**Authentication**: None required

**Response**:
```json
{
  "needs_setup": true,
  "has_users": false
}
```

**Status Codes**:
- `200`: Success

---

### Setup Owner Account

Create the first owner account. Only works when no users exist.

**Endpoint**: `POST /api/admin-users/setup`

**Authentication**: None required (only works when no users exist)

**Request Body**:
```json
{
  "email": "admin@example.com",
  "display_name": "Admin User",
  "password": "SecurePassword123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "ae89197e-e24a-4e55-a9e2-70ba9a273730",
    "email": "admin@example.com",
    "display_name": "Admin User",
    "role": "owner",
    "is_active": true,
    "created_at": "2025-10-16T10:30:00Z",
    "last_login": "2025-10-16T10:30:00Z",
    "metadata": {}
  }
}
```

**Status Codes**:
- `200`: Owner account created successfully
- `400`: Setup already completed (users exist)
- `422`: Invalid email or password (minimum 8 characters)

**Example**:
```bash
curl -X POST http://localhost:8004/api/admin-users/setup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "display_name": "Admin User",
    "password": "SecurePassword123!"
  }'
```

---

### Login

Authenticate with email and password to receive a JWT token.

**Endpoint**: `POST /api/admin-users/login`

**Authentication**: None required

**Request Body**:
```json
{
  "email": "admin@example.com",
  "password": "SecurePassword123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "ae89197e-e24a-4e55-a9e2-70ba9a273730",
    "email": "admin@example.com",
    "display_name": "Admin User",
    "role": "owner",
    "is_active": true,
    "created_at": "2025-10-16T10:30:00Z",
    "last_login": "2025-10-16T11:45:00Z",
    "metadata": {}
  }
}
```

**Status Codes**:
- `200`: Login successful
- `401`: Invalid email or password
- `403`: Account is inactive

**Example**:
```bash
curl -X POST http://localhost:8004/api/admin-users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePassword123!"
  }'
```

---

### Logout

Revoke the current JWT session.

**Endpoint**: `POST /api/admin-users/logout`

**Authentication**: JWT Bearer token required

**Request**: No body required

**Response**:
```json
{
  "message": "Logged out successfully"
}
```

**Status Codes**:
- `200`: Session revoked successfully
- `401`: Invalid or missing JWT token

**Example**:
```bash
curl -X POST http://localhost:8004/api/admin-users/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Current User

Get information about the currently authenticated user.

**Endpoint**: `GET /api/admin-users/me`

**Authentication**: JWT Bearer token required

**Response**:
```json
{
  "user_id": "ae89197e-e24a-4e55-a9e2-70ba9a273730",
  "email": "admin@example.com",
  "display_name": "Admin User",
  "role": "owner",
  "is_active": true,
  "created_at": "2025-10-16T10:30:00Z",
  "last_login": "2025-10-16T11:45:00Z",
  "metadata": {}
}
```

**Status Codes**:
- `200`: Success
- `401`: Invalid or missing JWT token

**Example**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/admin-users/me
```

## User Management Endpoints

### List Admin Users

List all admin users. Requires owner or admin role.

**Endpoint**: `GET /api/admin-users`

**Authentication**: JWT Bearer token required (owner or admin role)

**Response**:
```json
[
  {
    "user_id": "ae89197e-e24a-4e55-a9e2-70ba9a273730",
    "email": "admin@example.com",
    "display_name": "Admin User",
    "role": "owner",
    "is_active": true,
    "created_at": "2025-10-16T10:30:00Z",
    "last_login": "2025-10-16T11:45:00Z",
    "metadata": {}
  },
  {
    "user_id": "f1e753ec-7e92-4767-8de8-e9a5bed22840",
    "email": "user@example.com",
    "display_name": "Regular User",
    "role": "user",
    "is_active": true,
    "created_at": "2025-10-16T12:00:00Z",
    "last_login": "2025-10-16T13:00:00Z",
    "metadata": {}
  }
]
```

**Status Codes**:
- `200`: Success
- `401`: Invalid or missing JWT token
- `403`: Insufficient permissions (requires owner or admin role)

**Example**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/admin-users
```

---

### Create Admin User

Create a new admin user. Requires owner or admin role.

**Endpoint**: `POST /api/admin-users`

**Authentication**: JWT Bearer token required (owner or admin role)

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "display_name": "New User",
  "password": "SecurePass456!",
  "role": "user",
  "metadata": {
    "department": "Engineering"
  }
}
```

**Response**:
```json
{
  "user_id": "b2c3d4e5-6789-4abc-def0-123456789abc",
  "email": "newuser@example.com",
  "display_name": "New User",
  "role": "user",
  "is_active": true,
  "created_at": "2025-10-16T14:00:00Z",
  "last_login": null,
  "metadata": {
    "department": "Engineering"
  }
}
```

**Role Restrictions**:
- **Owner**: Can create any role (owner, admin, user)
- **Admin**: Can only create "user" role

**Status Codes**:
- `200`: User created successfully
- `400`: Email already registered
- `401`: Invalid or missing JWT token
- `403`: Insufficient permissions
- `422`: Invalid email or password (minimum 8 characters)

**Example**:
```bash
curl -X POST http://localhost:8004/api/admin-users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "display_name": "New User",
    "password": "SecurePass456!",
    "role": "user"
  }'
```

---

### Update Admin User

Update an existing admin user. Requires owner or admin role.

**Endpoint**: `PUT /api/admin-users/{user_id}`

**Authentication**: JWT Bearer token required (owner or admin role)

**Request Body** (all fields optional):
```json
{
  "display_name": "Updated Name",
  "role": "admin",
  "is_active": false,
  "metadata": {
    "department": "Management"
  }
}
```

**Response**:
```json
{
  "user_id": "b2c3d4e5-6789-4abc-def0-123456789abc",
  "email": "newuser@example.com",
  "display_name": "Updated Name",
  "role": "admin",
  "is_active": false,
  "created_at": "2025-10-16T14:00:00Z",
  "last_login": "2025-10-16T15:00:00Z",
  "metadata": {
    "department": "Management"
  }
}
```

**Role Restrictions**:
- **Owner**: Can update any user
- **Admin**: Cannot update owner or admin users

**Status Codes**:
- `200`: User updated successfully
- `401`: Invalid or missing JWT token
- `403`: Insufficient permissions
- `404`: User not found

**Example**:
```bash
curl -X PUT http://localhost:8004/api/admin-users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Updated Name",
    "is_active": false
  }'
```

---

### Delete Admin User

Delete an admin user. Requires owner or admin role.

**Endpoint**: `DELETE /api/admin-users/{user_id}`

**Authentication**: JWT Bearer token required (owner or admin role)

**Response**:
```json
{
  "message": "User deleted successfully"
}
```

**Role Restrictions**:
- **Owner**: Can delete any user except themselves
- **Admin**: Cannot delete owner or admin users

**Status Codes**:
- `200`: User deleted successfully
- `400`: Cannot delete yourself
- `401`: Invalid or missing JWT token
- `403`: Insufficient permissions
- `404`: User not found

**Example**:
```bash
curl -X DELETE http://localhost:8004/api/admin-users/$USER_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

### Change Password

Change password for the current user or another user (owner only).

**Endpoint**: `POST /api/admin-users/{user_id}/change-password`

**Authentication**: JWT Bearer token required

**Request Body**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Note**: `current_password` is only required when changing your own password.

**Response**:
```json
{
  "message": "Password changed successfully"
}
```

**Status Codes**:
- `200`: Password changed successfully
- `400`: Invalid current password
- `401`: Invalid or missing JWT token
- `403`: Insufficient permissions
- `404`: User not found
- `422`: Invalid new password (minimum 8 characters)

**Example (change own password)**:
```bash
curl -X POST http://localhost:8004/api/admin-users/me/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewPassword456!"
  }'
```

**Example (owner changing another user's password)**:
```bash
curl -X POST http://localhost:8004/api/admin-users/$USER_ID/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "NewPassword456!"
  }'
```

## Audit Log Endpoints

### View Audit Logs

View audit logs of admin actions. Requires owner or admin role.

**Endpoint**: `GET /api/admin-users/audit-logs`

**Authentication**: JWT Bearer token required (owner or admin role)

**Query Parameters**:
- `limit` (optional): Maximum number of logs to return (default: 50, max: 100)
- `user_id` (optional): Filter logs by user ID
- `action` (optional): Filter logs by action type

**Response**:
```json
[
  {
    "audit_id": "c3d4e5f6-7890-4abc-def0-234567890def",
    "user_id": "ae89197e-e24a-4e55-a9e2-70ba9a273730",
    "action": "created_user",
    "resource_type": "admin_user",
    "resource_id": "b2c3d4e5-6789-4abc-def0-123456789abc",
    "details": {
      "email": "newuser@example.com",
      "role": "user"
    },
    "ip_address": "127.0.0.1",
    "created_at": "2025-10-16T14:00:00Z"
  },
  {
    "audit_id": "d4e5f6a7-8901-4bcd-ef01-345678901ef0",
    "user_id": "ae89197e-e24a-4e55-a9e2-70ba9a273730",
    "action": "login",
    "resource_type": "admin_user",
    "resource_id": "ae89197e-e24a-4e55-a9e2-70ba9a273730",
    "details": {
      "success": true
    },
    "ip_address": "127.0.0.1",
    "created_at": "2025-10-16T11:45:00Z"
  }
]
```

**Logged Actions**:
- `setup_owner`: Initial owner account creation
- `login`: User login
- `logout`: User logout
- `created_user`: New user created
- `updated_user`: User updated
- `deleted_user`: User deleted
- `changed_password`: Password changed

**Status Codes**:
- `200`: Success
- `401`: Invalid or missing JWT token
- `403`: Insufficient permissions (requires owner or admin role)

**Example**:
```bash
# Get last 50 audit logs
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8004/api/admin-users/audit-logs?limit=50"

# Get logs for specific user
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8004/api/admin-users/audit-logs?user_id=$USER_ID"

# Get logs for specific action
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8004/api/admin-users/audit-logs?action=login"
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes**:
- `400`: Bad Request (invalid input, duplicate email, etc.)
- `401`: Unauthorized (missing/invalid authentication)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (user doesn't exist)
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

## Role-Based Access Control

### Role Hierarchy

1. **Owner**: Full access to all features
   - Create/modify/delete any user (including other owners and admins)
   - Change any user's password
   - View all audit logs
   - All management operations

2. **Admin**: Management access with restrictions
   - Create/modify/delete "user" role accounts only
   - Cannot modify owner or admin users
   - View all audit logs
   - All management operations

3. **User**: Read-only access
   - View own profile
   - Change own password
   - View dashboard (read-only)
   - Cannot create/modify/delete users

### Endpoint Access Matrix

| Endpoint | Owner | Admin | User |
|----------|-------|-------|------|
| GET /api/admin-users/me | ✅ | ✅ | ✅ |
| GET /api/admin-users | ✅ | ✅ | ❌ |
| POST /api/admin-users | ✅ (any role) | ✅ (user role only) | ❌ |
| PUT /api/admin-users/{id} | ✅ (any user) | ✅ (user role only) | ❌ |
| DELETE /api/admin-users/{id} | ✅ (any user except self) | ✅ (user role only) | ❌ |
| POST /api/admin-users/{id}/change-password | ✅ (any user) | ✅ (own password) | ✅ (own password) |
| GET /api/admin-users/audit-logs | ✅ | ✅ | ❌ |

## Testing

### Integration Tests

Comprehensive integration tests verify all endpoints:

**Test Script**: `scripts/test_jwt_integration.py`

**Run Tests**:
```bash
python3 scripts/test_jwt_integration.py
```

**Test Coverage**:
- Setup and login flows
- JWT and legacy authentication
- All CRUD operations
- Role-based permissions
- Security validation
- Audit logging

See [Integration Tests Documentation](../testing/integration-tests.md) for details.

## Related Documentation

- **[Admin Dashboard Authentication Guide](../admin-dashboard/authentication.md)** - User guide for authentication
- **[Integration Tests](../testing/integration-tests.md)** - How to test the API
- **[Environment Variables](../deployment/environment-variables.md)** - Configuration options

# Authentication

Secure admin dashboard access using JWT-based authentication with role-based permissions.

## Overview

The Admin Dashboard uses JWT (JSON Web Token) authentication to secure access to administrative functions. Only authenticated administrators can manage organizations, teams, model aliases, and provider credentials.

## Authentication System

### JWT-Based Authentication

The system uses **JWT tokens** for stateless authentication:

- **Secure** - Tokens are cryptographically signed
- **Stateless** - No server-side session storage required
- **Expiring** - Tokens automatically expire after a set time
- **Role-Based** - Tokens include user role for authorization

### Admin User Roles

| Role | Permissions | Description |
|------|-------------|-------------|
| **owner** | Full access | Can manage all resources and other admins |
| **admin** | Most access | Can manage organizations, teams, models (cannot manage other admins) |
| **viewer** | Read-only | Can view all data but cannot make changes |

## Initial Setup

### First-Time Setup

On a fresh installation, create the initial admin user:

1. Navigate to the Admin Dashboard URL
2. You'll be redirected to the setup page
3. Fill in the initial admin details:
   - **Username** - Admin username (e.g., "admin")
   - **Email** - Admin email address
   - **Password** - Strong password (min 8 characters)
   - **Full Name** - Admin's full name
4. Click **"Create Admin Account"**
5. The initial user is automatically assigned the **owner** role

**API Endpoint:**
```http
POST /api/admin-users/setup
Content-Type: application/json

{
  "username": "admin",
  "email": "admin@example.com",
  "password": "secure-password-123",
  "full_name": "Admin User"
}
```

**Response:**
```json
{
  "message": "Initial admin user created successfully",
  "username": "admin",
  "email": "admin@example.com",
  "role": "owner"
}
```

!!! warning "One-Time Only"
    The setup endpoint can only be used once. After the first admin is created, you must use the dashboard to add additional admins.

## Logging In

### Web Dashboard Login

1. Navigate to the Admin Dashboard
2. Enter your **username** and **password**
3. Click **"Sign In"**
4. JWT token is stored in browser localStorage
5. Token automatically included in all API requests

### API Login

```http
POST /api/admin-users/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "owner",
    "is_active": true
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid username or password"
}
```

### Using the Token

Include the JWT token in the Authorization header for all authenticated requests:

```http
GET /api/organizations
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Logging Out

### Web Dashboard

- Click your username in the top right
- Select **"Logout"**
- JWT token is removed from localStorage
- You'll be redirected to the login page

### Manual Token Removal

Since JWTs are stateless, logout is handled client-side:

```javascript
// Remove token from localStorage
localStorage.removeItem('authToken');

// Redirect to login
window.location.href = '/login';
```

## Managing Admin Users

### Creating Additional Admins

**Prerequisites:** Must be logged in as **owner** role

1. Navigate to **Admin Users** (if available in UI)
2. Click **"Add Admin User"**
3. Fill in user details:
   - Username
   - Email
   - Password
   - Full Name
   - Role (admin or viewer)
4. Click **"Create"**

**API Endpoint:**
```http
POST /api/admin-users
Authorization: Bearer <owner-token>
Content-Type: application/json

{
  "username": "new-admin",
  "email": "new-admin@example.com",
  "password": "secure-password",
  "full_name": "New Admin",
  "role": "admin"
}
```

### Updating Admin Users

Change user details or role:

```http
PUT /api/admin-users/{user_id}
Authorization: Bearer <owner-token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "role": "viewer"
}
```

### Deactivating Admin Users

Disable access without deleting:

```http
PUT /api/admin-users/{user_id}/deactivate
Authorization: Bearer <owner-token>
```

The user can no longer log in until reactivated.

### Deleting Admin Users

Permanently remove an admin:

```http
DELETE /api/admin-users/{user_id}
Authorization: Bearer <owner-token>
```

## Password Management

### Changing Your Password

1. Navigate to **Profile Settings**
2. Enter current password
3. Enter new password (twice for confirmation)
4. Click **"Update Password"**

**API Endpoint:**
```http
PUT /api/admin-users/password
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "current_password": "old-password",
  "new_password": "new-secure-password"
}
```

### Password Reset (Admin-Initiated)

**Prerequisites:** Must be logged in as **owner**

An owner can reset another admin's password:

```http
PUT /api/admin-users/{user_id}/reset-password
Authorization: Bearer <owner-token>
Content-Type: application/json

{
  "new_password": "temporary-password-123"
}
```

!!! note "No Email Reset"
    The current system does not include email-based password reset. This is an admin-managed system where owners can reset passwords manually.

## Token Expiration

### Default Settings

- **Access Token Lifetime**: 24 hours (configurable)
- **Automatic Refresh**: Not implemented (re-login required)
- **Token Validation**: On every API request

### When Token Expires

If your token expires:
1. API requests return `401 Unauthorized`
2. Dashboard redirects to login page
3. Log in again to receive a new token

### Extending Token Lifetime

Set the `JWT_EXPIRATION_HOURS` environment variable:

```env
# Default: 24 hours
JWT_EXPIRATION_HOURS=24

# Extended: 7 days
JWT_EXPIRATION_HOURS=168
```

!!! warning "Security Trade-off"
    Longer token lifetimes are more convenient but less secure. Balance based on your security requirements.

## Security Best Practices

### Password Requirements

✅ **DO:**
- Use minimum 8 characters
- Include uppercase, lowercase, numbers, symbols
- Use unique passwords (not reused from other services)
- Use a password manager
- Change passwords every 90 days

❌ **DON'T:**
- Use common passwords (admin123, password, etc.)
- Share passwords between users
- Store passwords in plain text
- Use default passwords in production

### Account Security

✅ **DO:**
- Create individual accounts for each admin
- Use least-privilege principle (viewer role when possible)
- Deactivate accounts for departed staff immediately
- Regular audit of active admin accounts
- Monitor login activity

❌ **DON'T:**
- Share admin accounts
- Leave test accounts active in production
- Grant owner role unnecessarily
- Use weak passwords for convenience

### Token Security

✅ **DO:**
- Store tokens in httpOnly cookies (if possible) or secure localStorage
- Use HTTPS for all admin dashboard access
- Clear tokens on logout
- Implement token refresh before expiration
- Monitor for suspicious API activity

❌ **DON'T:**
- Store tokens in URL parameters
- Log tokens to console or files
- Share tokens between users
- Use tokens across different environments

## Troubleshooting

### Cannot Access Setup Page

**Issue:** Setup page redirects to login

**Cause:** Initial admin already created

**Solution:** Use the login page with existing credentials. Contact system administrator if you don't have credentials.

### Login Fails with Correct Credentials

**Issue:** "Invalid username or password" error

**Possible Causes:**
1. Account is deactivated - Contact owner to reactivate
2. Password recently changed - Use updated password
3. Typing error - Double-check username and password

### Token Expired Errors

**Issue:** Constant 401 errors, forced to re-login

**Cause:** Token lifetime too short or system clock skew

**Solution:**
1. Check server and client clocks are synchronized
2. Increase `JWT_EXPIRATION_HOURS` if needed
3. Implement token refresh mechanism

### Cannot Create Admin Users

**Issue:** 403 Forbidden when creating admins

**Cause:** Only owners can create admin users

**Solution:** Log in with an owner account or ask an owner to create the account for you.

## API Reference

### Authentication Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/admin-users/setup` | POST | Create initial admin (one-time) | No |
| `/api/admin-users/login` | POST | Login and get JWT token | No |
| `/api/admin-users` | GET | List all admin users | Yes (owner) |
| `/api/admin-users` | POST | Create new admin user | Yes (owner) |
| `/api/admin-users/{id}` | PUT | Update admin user | Yes (owner) |
| `/api/admin-users/{id}/deactivate` | PUT | Deactivate user | Yes (owner) |
| `/api/admin-users/{id}/activate` | PUT | Activate user | Yes (owner) |
| `/api/admin-users/{id}` | DELETE | Delete user | Yes (owner) |
| `/api/admin-users/password` | PUT | Change own password | Yes (any) |
| `/api/admin-users/{id}/reset-password` | PUT | Reset user password | Yes (owner) |

### Example: Complete Login Flow

```python
import requests

API_URL = "https://your-saas-api.com"

# 1. Login
response = requests.post(
    f"{API_URL}/api/admin-users/login",
    json={
        "username": "admin",
        "password": "secure-password"
    }
)

if response.status_code == 200:
    data = response.json()
    token = data["access_token"]
    user = data["user"]

    print(f"Logged in as: {user['username']} ({user['role']})")

    # 2. Make authenticated request
    headers = {"Authorization": f"Bearer {token}"}

    orgs_response = requests.get(
        f"{API_URL}/api/organizations",
        headers=headers
    )

    organizations = orgs_response.json()
    print(f"Found {len(organizations)} organizations")
else:
    print("Login failed:", response.json()["detail"])
```

## Related Pages

- **[Organizations](organizations.md)** - Manage organizations after authentication
- **[Teams](teams.md)** - Manage teams with proper authorization
- **[Security](../../SECURITY.md)** - Overall security considerations
- **[Deployment](../deployment/railway.md)** - Production deployment security

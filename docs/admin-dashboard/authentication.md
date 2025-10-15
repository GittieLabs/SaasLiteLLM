# Admin Dashboard Authentication

Learn how to authenticate with the Admin Dashboard using your MASTER_KEY and best practices for admin access management.

## Overview

The Admin Dashboard uses **MASTER_KEY** authentication to protect administrative endpoints. This is separate from team virtual keys and provides full access to manage organizations, teams, model groups, and system configuration.

!!! warning "Admin vs Team Authentication"
    - **MASTER_KEY**: Admin access to dashboard and management APIs (via `X-Admin-Key` header)
    - **Virtual Keys**: Team access to make LLM requests (via `Authorization: Bearer` header)

    These are completely separate authentication systems!

## Accessing the Admin Dashboard

### Local Development

**URL**: http://localhost:3000

**Default MASTER_KEY**: `sk-admin-local-dev-change-in-production`

### Production

**URL**: Your Railway/Vercel deployment URL

**MASTER_KEY**: Must be set in environment variables (Railway/Vercel dashboard)

## Login Flow

### 1. Navigate to Dashboard

Open the admin dashboard URL in your browser:

```
http://localhost:3000  (local)
https://admin.your-saas.com  (production)
```

### 2. Enter MASTER_KEY

The login page prompts for the admin key:

![Login Screen](../assets/admin-login.png)

Enter your `MASTER_KEY` value (without the `X-Admin-Key:` prefix):

```
sk-admin-local-dev-change-in-production
```

### 3. Authentication Validation

The dashboard validates your key by making a test request to:

```http
GET /api/model-groups
X-Admin-Key: sk-admin-your-key
```

If successful:
- ✅ Key is saved to localStorage
- ✅ User is redirected to dashboard
- ✅ All subsequent API requests include the key

If failed:
- ❌ "Invalid admin key" error shown
- ❌ User stays on login page

## How It Works

### Backend Validation

The SaaS API validates admin requests using the `verify_admin_key` dependency:

```python
# src/auth/dependencies.py
async def verify_admin_key(x_admin_key: str = Header(...)):
    """Verify X-Admin-Key header matches MASTER_KEY"""
    if x_admin_key != settings.master_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return None
```

### Frontend Implementation

The admin panel client automatically includes the key:

```typescript
// admin-panel/lib/api-client.ts
function getAdminKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('adminKey');
}

async function request(endpoint: string, options: RequestInit = {}) {
  const adminKey = getAdminKey();

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(adminKey ? { 'X-Admin-Key': adminKey } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Auto-logout on auth failure
      localStorage.removeItem('adminKey');
      window.location.href = '/login';
    }
    throw new Error('Request failed');
  }
  return response.json();
}
```

## Protected Endpoints

All admin endpoints require the `X-Admin-Key` header:

### Organization Management
- `POST /api/organizations/create`
- `GET /api/organizations`
- `GET /api/organizations/{id}`
- `GET /api/organizations/{id}/teams`

### Team Management
- `POST /api/teams/create`
- `GET /api/teams`
- `GET /api/teams/{id}`
- `PUT /api/teams/{id}/model-groups`

### Model Group Management
- `POST /api/model-groups/create`
- `GET /api/model-groups`
- `GET /api/model-groups/{name}`
- `PUT /api/model-groups/{name}/models`
- `DELETE /api/model-groups/{name}`

### Credit Management
- `POST /api/credits/teams/{id}/add`

!!! info "Security Fix"
    As of October 2025, all list endpoints (`GET /api/teams`, `GET /api/organizations`, `GET /api/model-groups`) now require authentication. Previously these were unprotected, exposing sensitive data including team virtual keys.

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
   python3 -m uvicorn src.saas_api:app --reload
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
   - Verify in logs: No "Using default MASTER_KEY" warning

### Admin Panel Configuration

The admin panel only needs the API URL:

```bash
# admin-panel/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8003
```

The MASTER_KEY is entered by users at login time and stored in browser localStorage.

## Security Best Practices

### 1. Strong Keys

Generate strong random keys:

```bash
# Generate 32-byte random hex
openssl rand -hex 32

# Format with prefix
MASTER_KEY=sk-admin-<generated-hex>
```

**Minimum Requirements**:
- At least 32 characters
- Random/unpredictable
- Unique per environment
- Changed regularly (quarterly)

### 2. Environment Separation

Use different keys for each environment:

```bash
# Development
MASTER_KEY=sk-admin-dev-key-here

# Staging
MASTER_KEY=sk-admin-staging-key-here

# Production
MASTER_KEY=sk-admin-prod-key-here
```

### 3. Key Storage

**❌ DON'T**:
- Commit keys to git
- Share keys via email/chat
- Store in plaintext files
- Reuse across environments
- Log keys in application logs

**✅ DO**:
- Use environment variables
- Store in secrets manager (Railway Variables, AWS Secrets Manager, etc.)
- Add `.env` to `.gitignore`
- Use password manager for personal storage
- Rotate keys regularly

### 4. Access Control

**Limit who has access**:
- Only share MASTER_KEY with trusted admins
- Use separate keys for different admin roles (if implementing RBAC)
- Revoke access immediately when admins leave
- Monitor admin activity logs

### 5. Network Security

**Production deployments**:
- Always use HTTPS
- Consider VPN-only access for dashboard
- Implement IP whitelisting if possible
- Enable rate limiting on login endpoint
- Set up alerts for failed login attempts

### 6. Session Management

The dashboard stores the admin key in localStorage:

**Browser Storage**: `localStorage.getItem('adminKey')`

**Auto-logout**: On 401 responses from API

**Manual logout**: Clear localStorage and redirect to login

```typescript
// Logout function
export function logout() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('adminKey');
  localStorage.removeItem('user');
  window.location.href = '/login';
}
```

## Troubleshooting

### "Invalid admin key" Error

**Problem**: Login fails with "Invalid admin key"

**Solutions**:
1. Verify MASTER_KEY is set in SaaS API environment:
   ```bash
   # Check if variable is loaded
   curl http://localhost:8003/api/model-groups \
     -H "X-Admin-Key: sk-admin-local-dev-change-in-production"
   ```

2. Check for typos (no extra spaces, correct prefix)

3. Restart SaaS API after changing `.env`

4. Verify admin panel is pointing to correct API URL:
   ```bash
   # admin-panel/.env.local
   NEXT_PUBLIC_API_URL=http://localhost:8003
   ```

### "API connection failed"

**Problem**: Dashboard can't connect to API

**Solutions**:
1. Verify SaaS API is running:
   ```bash
   curl http://localhost:8003/health
   ```

2. Check `NEXT_PUBLIC_API_URL` in `admin-panel/.env.local`

3. Check browser console for CORS errors

4. Verify firewall isn't blocking connections

### Auto-logout After Login

**Problem**: Successfully login but immediately logged out

**Solutions**:
1. Check that all API endpoints are accepting the `X-Admin-Key` header

2. Verify no CORS issues (check browser console)

3. Check SaaS API logs for 401 errors:
   ```bash
   # Should NOT see these after login
   401 Unauthorized - Missing X-Admin-Key header
   ```

### "Using default MASTER_KEY" Warning

**Problem**: Logs show security warning about default key

**Solutions**:
1. Set MASTER_KEY environment variable:
   ```bash
   export MASTER_KEY=sk-admin-your-secure-key
   ```

2. Verify it's loaded:
   ```python
   from src.config.settings import settings
   print(settings.master_key)
   ```

3. Restart the application

## API Testing

Test admin authentication manually:

### Without Authentication (Should Fail)

```bash
curl http://localhost:8003/api/teams
# Returns: 401 Unauthorized
```

### With Authentication (Should Succeed)

```bash
curl -H "X-Admin-Key: sk-admin-local-dev-change-in-production" \
  http://localhost:8003/api/teams
# Returns: 200 OK with team data
```

### Invalid Key (Should Fail)

```bash
curl -H "X-Admin-Key: wrong-key" \
  http://localhost:8003/api/teams
# Returns: 401 Unauthorized
```

## Key Rotation

Rotate MASTER_KEY periodically:

### Rotation Process

1. **Generate New Key**:
   ```bash
   openssl rand -hex 32
   MASTER_KEY=sk-admin-<new-generated-hex>
   ```

2. **Update Environment Variables**:
   - Railway: Update variable in dashboard
   - Local: Update `.env` file

3. **Notify Admins**:
   - Send new key to all admins securely
   - Set deadline for switching

4. **Deploy Changes**:
   - Railway: Auto-deploys on variable change
   - Local: Restart services

5. **Verify**:
   - Test login with new key
   - Monitor logs for auth failures
   - Confirm all admins have switched

**Recommended Schedule**:
- Development: Every 90 days
- Production: Every 30-60 days
- After security incident: Immediately
- After admin leaves: Immediately

## Next Steps

Now that you understand admin authentication:

1. **[Manage Organizations](organizations.md)** - Create and configure organizations
2. **[Manage Teams](teams.md)** - Set up teams with virtual keys
3. **[Configure Model Access](model-access-groups.md)** - Control model permissions
4. **[Monitor Usage](monitoring.md)** - Track system activity

## Additional Resources

- **[Environment Variables Guide](../deployment/environment-variables.md)** - Complete env var reference
- **[Security Test Results](../../SECURITY_TEST_FINAL.md)** - Recent security fixes
- **[Team Authentication](../integration/authentication.md)** - How teams authenticate (different from admin)

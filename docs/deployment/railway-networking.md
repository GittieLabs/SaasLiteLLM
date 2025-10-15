# Railway Networking Guide

Understanding Railway's internal and public URLs for proper SaasLiteLLM deployment.

## Overview

Railway provides **two types of URLs** for each service:

| URL Type | Format | Accessibility | Used For |
|----------|--------|---------------|----------|
| **Public URL** | `https://service-name-xxx.up.railway.app` | Internet-accessible | External clients, admin panel, LiteLLM UI |
| **Internal URL** | `http://service-name.railway.internal:port` | Railway-only | Service-to-service communication |

!!! warning "Critical"
    Using the wrong URL type will cause connection failures!

    - **External clients cannot access `.railway.internal` URLs**
    - **Internal services should use `.railway.internal` for better performance**

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Internet / Clients                    │
└─────────────────────────┬───────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            │ Public URLs │             │
            ▼             ▼             ▼
    ┌──────────────┐  ┌──────────┐  ┌──────────────┐
    │  Admin Panel │  │   Teams  │  │   Admins     │
    │  (Next.js)   │  │  (API    │  │  (LiteLLM   │
    │              │  │  Clients)│  │   UI)        │
    └──────┬───────┘  └─────┬────┘  └──────┬───────┘
           │                │               │
           │ Public URL     │ Public URL    │ Public URL
           │                │               │
           ▼                ▼               │
    ┌─────────────────────────────────┐    │
    │   SaaS API Service               │    │
    │   https://saas-api-xxx.up.       │    │
    │   railway.app (PUBLIC)           │    │
    └──────────────┬──────────────────┘    │
                   │                        │
                   │ Internal URL           │
                   │ (Faster, Private)      │
                   ▼                        ▼
    ┌─────────────────────────────────┐────┘
    │   LiteLLM Proxy Service         │
    │   Internal: http://litellm-     │
    │   proxy.railway.internal:4000   │
    │   Public: https://litellm-      │
    │   proxy-xxx.up.railway.app      │
    └────────────┬────────────────────┘
                 │
                 ▼
          OpenAI/Anthropic/etc.
```

## Service Configuration

### 1. SaaS API Service

**Environment Variables:**

```bash
# Database (provided by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Admin Authentication
MASTER_KEY=sk-admin-SECURE-KEY-HERE
LITELLM_MASTER_KEY=sk-litellm-SECURE-KEY-HERE

# LiteLLM Connection (INTERNAL URL)
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000

# Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Public URL:**
- Railway auto-generates: `https://saas-api-production-abc123.up.railway.app`
- Used by: Admin panel, team clients, external apps
- Enable in: Settings → Networking → Generate Domain

**Port:** 8080 (or Railway's `PORT` variable)

### 2. LiteLLM Proxy Service

**Environment Variables:**

```bash
# Database (same as SaaS API)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Authentication
LITELLM_MASTER_KEY=sk-litellm-SECURE-KEY-HERE

# Storage
STORE_MODEL_IN_DB=True

# Redis (if using)
REDIS_HOST=${{Redis.REDISHOST}}
REDIS_PORT=${{Redis.REDISPORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}
REDIS_URL=${{Redis.REDIS_URL}}

# Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Public URL:**
- Railway auto-generates: `https://litellm-proxy-xyz789.up.railway.app`
- Used by: Admins accessing `/ui` for model configuration
- Enable in: Settings → Networking → Generate Domain

**Internal URL:**
- Automatically available: `http://litellm-proxy.railway.internal:4000`
- Used by: SaaS API to proxy LLM requests
- No configuration needed - Railway provides this automatically

**Port:** 4000 (LiteLLM default)

### 3. Admin Panel Service

**Environment Variables:**

```bash
# SaaS API URL (PUBLIC URL - NOT internal!)
NEXT_PUBLIC_API_URL=https://saas-api-production-abc123.up.railway.app

# Or use Railway reference (recommended):
NEXT_PUBLIC_API_URL=${{saas-api.RAILWAY_PUBLIC_DOMAIN}}
```

**Important:** Must use the SaaS API's **PUBLIC** URL, not internal!

**Public URL:**
- Railway auto-generates: `https://admin-panel-def456.up.railway.app`
- Used by: Admins to manage organizations/teams
- Enable in: Settings → Networking → Generate Domain

**Port:** 3000 (Next.js default)

## Finding Your Railway URLs

### Method 1: Railway Dashboard

1. Go to your Railway project
2. Click on a service (e.g., "saas-api")
3. Look at the top - you'll see:
   ```
   https://saas-api-production-abc123.up.railway.app
   ```
4. Copy this URL for external use

### Method 2: Railway Variables

Use Railway's built-in variable references:

```bash
# In any service's environment variables:
${{service-name.RAILWAY_PUBLIC_DOMAIN}}

# Example:
NEXT_PUBLIC_API_URL=https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}
```

**Available Railway Variables:**
- `RAILWAY_PUBLIC_DOMAIN` - Public domain (e.g., `saas-api-xxx.up.railway.app`)
- `RAILWAY_PRIVATE_DOMAIN` - Internal domain (e.g., `saas-api.railway.internal`)
- `RAILWAY_TCP_PROXY_PORT` - Port for TCP proxy
- `PORT` - Port your service should listen on

### Method 3: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Get service info
railway status

# Get service URL
railway domain
```

## Common URL Configurations

### Team API Clients

Teams making LLM requests use the **SaaS API public URL**:

```python
# Team client configuration
API_URL = "https://saas-api-production-abc123.up.railway.app"
VIRTUAL_KEY = "sk-team-virtual-key"

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{API_URL}/api/jobs/create",
    headers=headers,
    json={"team_id": "acme-corp", "job_type": "analysis"}
)
```

### Admin Panel

Admin panel uses the **SaaS API public URL**:

```bash
# admin-panel/.env.local (DO NOT use .railway.internal!)
NEXT_PUBLIC_API_URL=https://saas-api-production-abc123.up.railway.app
```

### SaaS API to LiteLLM

SaaS API uses **LiteLLM internal URL** for better performance:

```bash
# SaaS API environment
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
```

### Admins Configuring Models

Admins use **LiteLLM public URL** to access UI:

```
https://litellm-proxy-xyz789.up.railway.app/ui
```

Login with: `LITELLM_MASTER_KEY`

## Troubleshooting

### "Cannot connect to service"

**Problem:** External client can't reach service

**Check:**
1. Are you using the **public URL**?
   - ❌ `http://saas-api.railway.internal:8080`
   - ✅ `https://saas-api-production-abc123.up.railway.app`

2. Is the service's public domain enabled?
   - Go to service → Settings → Networking
   - Click "Generate Domain" if none exists

3. Is the service deployed and running?
   - Check service logs for errors
   - Verify deployment succeeded

### "Connection refused from Railway service"

**Problem:** Service-to-service communication failing

**Check:**
1. Are you using the **internal URL** for service-to-service?
   - ❌ `https://litellm-proxy-xyz.up.railway.app`
   - ✅ `http://litellm-proxy.railway.internal:4000`

2. Is the target service running?
   - Check if LiteLLM proxy deployed successfully
   - Verify it's listening on the correct port

3. Is the service name correct?
   - Internal URL format: `http://<service-name>.railway.internal:<port>`
   - Service name matches exactly (check Railway dashboard)

### "CORS errors in browser"

**Problem:** Admin panel can't make requests to SaaS API

**Check:**
1. Is `NEXT_PUBLIC_API_URL` using **public URL**?
   ```bash
   # Correct
   NEXT_PUBLIC_API_URL=https://saas-api-production.up.railway.app

   # Wrong
   NEXT_PUBLIC_API_URL=http://saas-api.railway.internal:8080
   ```

2. Is CORS configured in SaaS API?
   ```python
   # src/saas_api.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://admin-panel-xxx.up.railway.app"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### "Admin panel shows 'API connection failed'"

**Checklist:**
1. ✅ `NEXT_PUBLIC_API_URL` is set to SaaS API **public URL**
2. ✅ SaaS API service is deployed and running
3. ✅ SaaS API public domain is generated and accessible
4. ✅ No typos in the URL
5. ✅ CORS is properly configured

**Test manually:**
```bash
# Should return 401 (auth required, but reachable)
curl https://saas-api-production-abc123.up.railway.app/api/teams
```

## Custom Domains (Optional)

For production, use custom domains instead of Railway-provided URLs:

### Setup Custom Domain

1. **Go to Railway service** → Settings → Networking
2. **Click "Custom Domain"**
3. **Enter your domain:** `api.yourcompany.com`
4. **Update DNS records** (Railway provides instructions):
   ```
   Type: CNAME
   Name: api
   Value: saas-api-production-abc123.up.railway.app
   ```
5. **Wait for DNS propagation** (5-60 minutes)
6. **Update environment variables** to use custom domain

### Update Configurations

After setting custom domains:

**Admin Panel:**
```bash
NEXT_PUBLIC_API_URL=https://api.yourcompany.com
```

**Team Clients:**
```python
API_URL = "https://api.yourcompany.com"
```

**SaaS API to LiteLLM (still internal):**
```bash
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
```

## Best Practices

### 1. Use Internal URLs for Service-to-Service

**Why:** Faster, more secure, no external network hops

```bash
# Good: Internal communication
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000

# Bad: Using public URL for internal communication
LITELLM_PROXY_URL=https://litellm-proxy-xyz.up.railway.app
```

### 2. Use Public URLs for External Access

**Why:** External clients cannot access `.railway.internal`

```bash
# Good: External access
NEXT_PUBLIC_API_URL=https://saas-api-production.up.railway.app

# Bad: External client using internal URL
NEXT_PUBLIC_API_URL=http://saas-api.railway.internal:8080
```

### 3. Use Railway Variables for Dynamic URLs

**Why:** Automatically updates if service is redeployed

```bash
# Good: Dynamic reference
NEXT_PUBLIC_API_URL=https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}

# Bad: Hardcoded URL
NEXT_PUBLIC_API_URL=https://saas-api-production-abc123.up.railway.app
```

### 4. Document Your URLs

Keep a reference of all service URLs:

```
# Production URLs
SaaS API (Public):  https://api.yourcompany.com
SaaS API (Internal): http://saas-api.railway.internal:8080
LiteLLM (Public):   https://litellm.yourcompany.com
LiteLLM (Internal): http://litellm-proxy.railway.internal:4000
Admin Panel:        https://admin.yourcompany.com
```

## Security Considerations

### 1. Internal URLs are Private

- `.railway.internal` URLs are **NOT accessible** from the internet
- Only accessible within your Railway project
- Use for sensitive service-to-service communication

### 2. Public URLs are Exposed

- `.up.railway.app` URLs are **publicly accessible**
- Protect with authentication (MASTER_KEY, virtual keys)
- Consider custom domains with additional DNS security

### 3. HTTPS Everywhere

- Railway provides free HTTPS for all public URLs
- Use HTTPS for all external communication
- Internal Railway communication can use HTTP (secured by Railway network)

## CORS and Authentication

!!! info "Team Clients Are NOT Affected by CORS"
    **Important:** Server-side team clients (Python, Node.js, curl) completely ignore CORS restrictions.

    - ✅ **Team clients** - Use Bearer tokens, work from anywhere, CORS doesn't apply
    - ⚠️ **Admin panel** - Browser-based, must configure CORS properly

    CORS is a browser-only security feature. Your team API clients work regardless of CORS configuration.

    [:octicons-arrow-right-24: Learn more about CORS vs Authentication](cors-and-authentication.md)

**CORS Configuration:**

The SaaS API CORS middleware only allows specific origins (for the browser-based admin panel):

```python
# Only affects browser-based clients (admin panel)
allow_origins=[
    "http://localhost:3000",  # Local admin panel
    "https://admin-panel-xxx.up.railway.app",  # Production admin panel
]
```

**Team API clients (Python, Node.js, curl) completely ignore this configuration.**

## Summary

| Component | Connection Type | URL to Use | CORS Applies? |
|-----------|----------------|------------|---------------|
| Team Client → SaaS API | External | **Public**: `https://saas-api-xxx.up.railway.app` | ❌ No (server-side) |
| Admin Panel → SaaS API | External | **Public**: `https://saas-api-xxx.up.railway.app` | ✅ Yes (browser) |
| SaaS API → LiteLLM | Internal | **Internal**: `http://litellm-proxy.railway.internal:4000` | ❌ No |
| Admin → LiteLLM UI | External | **Public**: `https://litellm-proxy-xxx.up.railway.app/ui` | ✅ Yes (browser) |

## Next Steps

- **[Railway Deployment Guide](railway.md)** - Complete deployment walkthrough
- **[CORS & Authentication Guide](cors-and-authentication.md)** - Understand CORS vs authentication
- **[Environment Variables](environment-variables.md)** - All configuration options
- **[Security Guide](../admin-dashboard/authentication.md)** - Protect your deployment

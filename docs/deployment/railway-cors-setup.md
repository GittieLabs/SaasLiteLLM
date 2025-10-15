# Railway CORS Setup

How to configure CORS in Railway using dynamic service references - no hardcoded URLs needed!

## The Problem with Hardcoded URLs

**You shouldn't need to know your production URLs before deploying.** Railway generates URLs dynamically, and hardcoding them creates issues:

- ❌ Can't commit the code until you know the URL
- ❌ URLs change if you redeploy
- ❌ Manual updates required for each environment

## The Railway Solution: Service References

Railway provides **service references** that automatically resolve to the correct URLs:

```bash
# Instead of hardcoding:
ADMIN_PANEL_URL=https://admin-panel-production-abc123.up.railway.app

# Use Railway service reference:
ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}
```

**Benefits:**
- ✅ No hardcoded URLs
- ✅ Automatically updates if service is redeployed
- ✅ Works immediately after deployment
- ✅ Same config across environments

## How CORS Works in SaaS LiteLLM

### Important: CORS is Browser-Only

**Server-side team clients (Python, Node.js, curl) completely ignore CORS.**

CORS only affects:
- Browser-based admin panel (Next.js client-side requests)
- Any JavaScript running in web browsers

**Team API clients work from anywhere regardless of CORS configuration.**

[:octicons-arrow-right-24: Learn more about CORS vs Authentication](cors-and-authentication.md)

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Admin Panel (Browser-Based)                        │
│  https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}     │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ Client-side fetch() calls
                   │ (Subject to CORS)
                   ▼
┌─────────────────────────────────────────────────────┐
│  SaaS API                                            │
│  https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}        │
│                                                      │
│  CORS allows: admin-panel.RAILWAY_PUBLIC_DOMAIN     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Team Client (Python/Node.js/curl)                  │
│  From anywhere (AWS, Google Cloud, etc.)            │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ Server-side HTTP requests
                   │ (CORS does NOT apply)
                   ▼
┌─────────────────────────────────────────────────────┐
│  SaaS API                                            │
│  https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}        │
│                                                      │
│  Bearer token authentication (no CORS needed)       │
└─────────────────────────────────────────────────────┘
```

## Railway Configuration

### Step 1: SaaS API Service

In your **saas-api** service on Railway, add this environment variable:

```bash
# Railway Environment Variables for saas-api service

# Use Railway service reference to dynamically get admin panel URL
ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}
```

**How it works:**
1. Railway automatically resolves `${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}` to the actual domain
2. Example: `https://admin-panel-production-abc123.up.railway.app`
3. SaaS API reads this and adds it to CORS `allow_origins`
4. Updates automatically if admin panel is redeployed

### Step 2: Admin Panel Service

In your **admin-panel** service on Railway, set the API URL:

```bash
# Railway Environment Variables for admin-panel service

# Point to SaaS API public URL
NEXT_PUBLIC_API_URL=https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}
```

**Note:** Admin panel must use the **public** URL because:
- Browsers can't access `.railway.internal` domains
- CORS requires public URLs for origin checking
- Client-side Next.js code runs in the browser

### Complete Railway Setup

Here's the full environment variable configuration for Railway:

#### saas-api Service

```bash
# Database
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Admin Authentication
MASTER_KEY=sk-admin-GENERATE-SECURE-KEY-HERE
LITELLM_MASTER_KEY=sk-litellm-GENERATE-SECURE-KEY-HERE

# LiteLLM Connection (use INTERNAL for lower latency)
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000

# CORS - Admin Panel (use service reference)
ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}

# Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

#### admin-panel Service

```bash
# SaaS API URL (use service reference)
NEXT_PUBLIC_API_URL=https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}
```

#### litellm-proxy Service

```bash
# Database
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Authentication
LITELLM_MASTER_KEY=sk-litellm-GENERATE-SECURE-KEY-HERE

# Storage
STORE_MODEL_IN_DB=True

# Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Advanced: Multiple Admin Panel Environments

If you have multiple environments (staging, production), use `ADDITIONAL_CORS_ORIGINS`:

### Railway Setup

**saas-api Service:**
```bash
# Primary admin panel
ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}

# Additional environments (comma-separated)
ADDITIONAL_CORS_ORIGINS=https://admin-staging.yourcompany.com,https://admin-dev.yourcompany.com
```

**How it works:**
- `ADMIN_PANEL_URL` adds one origin
- `ADDITIONAL_CORS_ORIGINS` adds multiple (comma-separated)
- All are combined into the CORS `allow_origins` list

## Verification

### Check CORS Configuration

After deploying, verify CORS is working:

**1. Check SaaS API Logs:**

Railway will show the resolved URLs in logs:

```bash
# Railway Logs → saas-api
INFO:     Started server process
INFO:     CORS origins: ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002', 'https://admin-panel-production-abc123.up.railway.app']
```

**2. Test Admin Panel:**

Open your admin panel in the browser:
```
https://admin-panel-production-abc123.up.railway.app
```

Try to log in:
- ✅ If login works → CORS is configured correctly
- ❌ If you see CORS errors in browser console → Check configuration

**3. Test Team Client:**

Test from your development machine (server-side):

```bash
curl -X POST https://saas-api-production-abc123.up.railway.app/api/jobs/create \
  -H "Authorization: Bearer sk-team-virtual-key" \
  -H "Content-Type: application/json" \
  -d '{"team_id": "test", "job_type": "test"}'

# ✅ Should work - CORS doesn't apply to curl
```

## Railway Service Reference Syntax

Railway supports these reference patterns:

### Public Domain

```bash
# Service's public domain (e.g., service-name-xxx.up.railway.app)
${{service-name.RAILWAY_PUBLIC_DOMAIN}}
```

**Use for:**
- Admin panel connecting to SaaS API (browser-based)
- SaaS API allowing admin panel origin (CORS)
- Any external access

### Private Domain

```bash
# Service's internal domain (e.g., service-name.railway.internal)
${{service-name.RAILWAY_PRIVATE_DOMAIN}}
```

**Use for:**
- Service-to-service communication within Railway
- SaaS API connecting to LiteLLM proxy
- Lower latency, more secure

### Other Variables

```bash
# Reference another service's environment variable
${{service-name.ENV_VAR_NAME}}

# Database connection string
${{Postgres.DATABASE_URL}}

# Redis connection
${{Redis.REDIS_URL}}
```

## Troubleshooting

### Issue: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Possible causes:**

1. **Service reference not resolving:**
   - Check Railway logs for the actual resolved URL
   - Verify `admin-panel` service name is correct

2. **Environment variable not set:**
   ```bash
   # Check in Railway dashboard:
   saas-api → Variables → ADMIN_PANEL_URL should show the URL
   ```

3. **Service not deployed:**
   - Ensure admin-panel service deployed successfully
   - `RAILWAY_PUBLIC_DOMAIN` only exists after deployment

**Solution:**

1. **Verify service names in Railway:**
   - Go to Railway project
   - Check exact service names (case-sensitive)
   - Use exact name in reference: `${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}`

2. **Check environment variable:**
   ```bash
   # In saas-api service variables
   ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}

   # Should resolve to something like:
   # https://admin-panel-production-abc123.up.railway.app
   ```

3. **Redeploy saas-api:**
   - Changes to environment variables require redeployment
   - Railway → saas-api → Deploy → Redeploy

### Issue: "Cannot read properties of undefined"

**Cause:** Service reference uses wrong service name.

**Solution:**
1. Get exact service name from Railway dashboard
2. Update reference: `${{exact-service-name.RAILWAY_PUBLIC_DOMAIN}}`

### Issue: Admin panel can't connect to API

**Check:**

1. **Admin panel environment variable:**
   ```bash
   NEXT_PUBLIC_API_URL=https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}
   ```

2. **SaaS API is deployed and running:**
   - Check Railway → saas-api → Logs
   - Verify service is healthy

3. **Public domain is generated:**
   - Railway → saas-api → Settings → Networking
   - "Generate Domain" should show a URL

## Best Practices

### 1. Use Service References Everywhere

**✅ Good:**
```bash
LITELLM_PROXY_URL=http://${{litellm-proxy.RAILWAY_PRIVATE_DOMAIN}}:4000
ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}
```

**❌ Bad:**
```bash
LITELLM_PROXY_URL=http://litellm-proxy-production.up.railway.app:4000
ADMIN_PANEL_URL=https://admin-panel-production-abc123.up.railway.app
```

### 2. Use Internal URLs for Service-to-Service

**✅ Good:**
```bash
# SaaS API → LiteLLM (internal)
LITELLM_PROXY_URL=http://${{litellm-proxy.RAILWAY_PRIVATE_DOMAIN}}:4000
```

**❌ Bad:**
```bash
# Using public URL (slower, unnecessary)
LITELLM_PROXY_URL=https://${{litellm-proxy.RAILWAY_PUBLIC_DOMAIN}}
```

### 3. Use Public URLs for Browser Clients

**✅ Good:**
```bash
# Admin panel (browser) → SaaS API
NEXT_PUBLIC_API_URL=https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}
```

**❌ Bad:**
```bash
# Browsers can't access internal URLs
NEXT_PUBLIC_API_URL=http://${{saas-api.RAILWAY_PRIVATE_DOMAIN}}:8080
```

### 4. Document Your Service Names

Keep a reference of service names in your project:

```yaml
# .railway/service-names.yml
services:
  saas_api: saas-api
  admin_panel: admin-panel
  litellm_proxy: litellm-proxy
  postgres: Postgres
  redis: Redis
```

## Summary

| Configuration | Railway Variable | Resolved Example |
|---------------|------------------|------------------|
| **SaaS API CORS** | `ADMIN_PANEL_URL=https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}` | `https://admin-panel-production-abc123.up.railway.app` |
| **Admin Panel API** | `NEXT_PUBLIC_API_URL=https://${{saas-api.RAILWAY_PUBLIC_DOMAIN}}` | `https://saas-api-production-xyz789.up.railway.app` |
| **SaaS → LiteLLM** | `LITELLM_PROXY_URL=http://${{litellm-proxy.RAILWAY_PRIVATE_DOMAIN}}:4000` | `http://litellm-proxy.railway.internal:4000` |

## Next Steps

- **[Railway Deployment Guide](railway.md)** - Complete deployment walkthrough
- **[Environment Variables Reference](environment-variables.md)** - All configuration options
- **[CORS & Authentication Guide](cors-and-authentication.md)** - Understand CORS in depth
- **[Railway Networking](railway-networking.md)** - Internal vs public URLs

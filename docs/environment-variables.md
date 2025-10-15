# Environment Variables Reference

Complete guide to all environment variables needed for SaasLiteLLM deployment.

## Quick Reference

| Service | Env File | Port | Key Variables |
|---------|----------|------|---------------|
| SaaS API | `.env` (root) | 8003 | `DATABASE_URL`, `MASTER_KEY`, `LITELLM_MASTER_KEY`, `LITELLM_PROXY_URL` |
| LiteLLM Proxy | `.env` (root) | 8002 | `DATABASE_URL`, `LITELLM_MASTER_KEY`, `REDIS_*`, `STORE_MODEL_IN_DB` |
| Admin Panel | `admin-panel/.env.local` | 3002 | `NEXT_PUBLIC_API_URL` |

---

## 1. SaaS API Environment Variables

**File**: `.env` in project root

### Required

```bash
# Database Connection
DATABASE_URL=postgresql://username:password@host:port/database

# Admin Authentication (for SaaS API management endpoints)
# Use this key with X-Admin-Key header to access admin endpoints
MASTER_KEY=sk-admin-your-super-secure-admin-key-here

# LiteLLM Connection
LITELLM_MASTER_KEY=sk-litellm-your-super-secure-litellm-key-here
LITELLM_PROXY_URL=http://localhost:8002
```

### Optional (Provider API Keys)

```bash
# LLM Provider API Keys (optional if configured via LiteLLM UI)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# Add other providers as needed
```

### Optional (Redis Caching)

```bash
# Redis Configuration (optional for SaaS API, but recommended)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379
```

### Optional (Server Configuration)

```bash
# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=1
ENVIRONMENT=development
DEBUG=false
```

---

## 2. LiteLLM Proxy Environment Variables

**File**: `.env` in project root (SAME FILE as SaaS API)

### Required

```bash
# Database Connection (for storing models, teams, keys)
DATABASE_URL=postgresql://username:password@host:port/database

# LiteLLM Authentication
LITELLM_MASTER_KEY=sk-litellm-your-super-secure-litellm-key-here

# Enable database storage for models/teams/keys
STORE_MODEL_IN_DB=True

# Redis Configuration (REQUIRED for LiteLLM caching and rate limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379
```

### Optional (Provider API Keys)

```bash
# LLM Provider API Keys
# Can be configured here OR via LiteLLM UI at http://localhost:8002/ui
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AZURE_API_KEY=...
AZURE_API_BASE=https://...
AZURE_API_VERSION=2024-02-15-preview
# Add other providers as needed
```

---

## 3. Admin Panel Environment Variables

**File**: `admin-panel/.env.local`

### Required

```bash
# SaaS API URL
# Points to where your SaaS API is running
NEXT_PUBLIC_API_URL=http://localhost:8003
```

**Note**: The MASTER_KEY is NOT stored in the admin panel's `.env.local` file. Users enter it in the login page, and it's validated against the SaaS API.

---

## Environment-Specific Configurations

### Local Development

**SaaS API & LiteLLM** (`.env`):
```bash
DATABASE_URL=postgresql://litellm_user:litellm_password@localhost:5432/litellm
MASTER_KEY=sk-admin-local-dev-change-in-production
LITELLM_MASTER_KEY=sk-local-dev-master-key-change-me
LITELLM_PROXY_URL=http://localhost:8002
STORE_MODEL_IN_DB=True

# Redis (from Docker Compose)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379

# Provider keys (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Note**: If you have multiple Redis instances running locally, adjust `REDIS_PORT` to match your instance (e.g., 6380). For Docker Compose users, Redis is exposed on port 6380 on the host but uses 6379 internally.

**Admin Panel** (`admin-panel/.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8003
```

### Railway Deployment

**SaaS API Service**:
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
MASTER_KEY=sk-admin-GENERATE-SECURE-KEY-HERE
LITELLM_MASTER_KEY=sk-litellm-GENERATE-SECURE-KEY-HERE
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000

# Redis (if using Railway Redis)
REDIS_HOST=${{Redis.REDISHOST}}
REDIS_PORT=${{Redis.REDISPORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}
REDIS_URL=${{Redis.REDIS_URL}}

# Provider keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**LiteLLM Proxy Service**:
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=sk-litellm-GENERATE-SECURE-KEY-HERE
STORE_MODEL_IN_DB=True

# Redis (REQUIRED for LiteLLM)
REDIS_HOST=${{Redis.REDISHOST}}
REDIS_PORT=${{Redis.REDISPORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}
REDIS_URL=${{Redis.REDIS_URL}}

# Provider keys (can also be added via UI)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Admin Panel Service**:
```bash
NEXT_PUBLIC_API_URL=https://your-saas-api.railway.app
```

---

## Key Concepts

### 1. Two Master Keys

There are **TWO different master keys**:

| Key | Purpose | Used By |
|-----|---------|---------|
| `MASTER_KEY` | SaaS API admin authentication | Admin Panel, API management tools |
| `LITELLM_MASTER_KEY` | LiteLLM proxy authentication | SaaS API ↔ LiteLLM communication, LiteLLM UI access |

**IMPORTANT**: These must be DIFFERENT keys for security.

### 2. Shared Database

Both SaaS API and LiteLLM Proxy can share the SAME PostgreSQL database:
- SaaS API uses it for: organizations, teams, credits, jobs
- LiteLLM uses it for: models, virtual keys, budgets (when `STORE_MODEL_IN_DB=True`)

They use different tables, so there's no conflict.

### 3. Redis Configuration

Redis serves different purposes:

**For SaaS API** (optional):
- Response caching
- Session management
- Performance optimization

**For LiteLLM** (REQUIRED):
- Request caching
- Rate limiting
- Token counting
- Budget tracking

### 4. STORE_MODEL_IN_DB Flag

When `STORE_MODEL_IN_DB=True`:
- Models are stored in PostgreSQL (not YAML config)
- Teams/keys are persisted in database
- Changes via LiteLLM UI are permanent
- Enables dynamic model management

**This is REQUIRED for production deployments.**

---

## Generating Secure Keys

For production, generate strong random keys:

```bash
# Generate MASTER_KEY
openssl rand -hex 32

# Generate LITELLM_MASTER_KEY
openssl rand -hex 32
```

Then format them with proper prefixes:
```bash
MASTER_KEY=sk-admin-<generated-hex>
LITELLM_MASTER_KEY=sk-litellm-<generated-hex>
```

---

## Validation Checklist

Before deploying, verify:

### SaaS API
- [ ] `DATABASE_URL` connects successfully
- [ ] `MASTER_KEY` is secure and unique
- [ ] `LITELLM_MASTER_KEY` matches LiteLLM proxy
- [ ] `LITELLM_PROXY_URL` is correct for environment
- [ ] Provider API keys are valid (if provided)

### LiteLLM Proxy
- [ ] `DATABASE_URL` connects successfully
- [ ] `LITELLM_MASTER_KEY` is secure and unique
- [ ] `STORE_MODEL_IN_DB=True` is set
- [ ] Redis connection works (`REDIS_HOST`, `REDIS_PORT`)
- [ ] Can access UI at `http://localhost:8002/ui`

### Admin Panel
- [ ] `NEXT_PUBLIC_API_URL` points to correct SaaS API
- [ ] Can log in with `MASTER_KEY`
- [ ] All API requests include `X-Admin-Key` header

---

## Troubleshooting

### "Failed to connect to LiteLLM"
- Check `LITELLM_PROXY_URL` is correct
- Verify `LITELLM_MASTER_KEY` matches in both services
- Ensure LiteLLM proxy is running

### "401 Unauthorized" from SaaS API
- Verify `MASTER_KEY` is correct
- Check `X-Admin-Key` header is being sent
- Ensure admin panel has correct API URL

### "Models not persisting" in LiteLLM
- Verify `STORE_MODEL_IN_DB=True` is set
- Check `DATABASE_URL` is correct
- Restart LiteLLM proxy after changing this setting

### Redis connection errors
- Verify Redis is running
- Check `REDIS_HOST` and `REDIS_PORT`
- For Railway, ensure Redis service is linked

---

## Security Best Practices

1. **Never commit keys to git**
   - Use `.env` files (in `.gitignore`)
   - Use Railway's built-in secret management

2. **Use different keys for different environments**
   - Development keys should differ from production
   - Each Railway environment should have unique keys

3. **Rotate keys regularly**
   - Change `MASTER_KEY` quarterly
   - Change `LITELLM_MASTER_KEY` quarterly
   - Update provider API keys as needed

4. **Limit key access**
   - Only share `MASTER_KEY` with admins
   - End users should NEVER see `MASTER_KEY` or `LITELLM_MASTER_KEY`
   - Use virtual keys for team access

5. **Monitor for unauthorized access**
   - Check logs for 401 errors
   - Monitor unusual API usage patterns
   - Set up alerts for multiple failed auth attempts

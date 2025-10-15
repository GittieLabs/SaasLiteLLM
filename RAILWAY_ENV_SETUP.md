# Railway Environment Variables Setup - URGENT

## Production Crash Fixed ✅

**What happened**: The SaaS API crashed because `MASTER_KEY` was not set in Railway environment variables.

**Fix deployed**: Made `MASTER_KEY` and `LITELLM_MASTER_KEY` optional with default values.

**⚠️ IMPORTANT**: You MUST set proper environment variables in Railway for security!

---

## Required Action: Add Environment Variables to Railway

### For SaaS API Service

Go to Railway > SaasLiteLLM project > saas-api service > Variables tab and add:

```bash
# CRITICAL: Admin Authentication
MASTER_KEY=sk-admin-GENERATE-SECURE-KEY-HERE

# CRITICAL: LiteLLM Connection
LITELLM_MASTER_KEY=sk-litellm-GENERATE-SECURE-KEY-HERE
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000

# Database (should already be set)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (if using Railway Redis)
REDIS_HOST=${{Redis.REDISHOST}}
REDIS_PORT=${{Redis.REDISPORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}
REDIS_URL=${{Redis.REDIS_URL}}

# Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Server Config
ENVIRONMENT=production
DEBUG=false
PORT=8080
```

### For LiteLLM Proxy Service

Go to Railway > SaasLiteLLM project > litellm-proxy service > Variables tab and add:

```bash
# CRITICAL: LiteLLM Authentication
LITELLM_MASTER_KEY=sk-litellm-SAME-KEY-AS-SAAS-API

# Database Storage
DATABASE_URL=${{Postgres.DATABASE_URL}}
STORE_MODEL_IN_DB=True

# Redis (REQUIRED)
REDIS_HOST=${{Redis.REDISHOST}}
REDIS_PORT=${{Redis.REDISPORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}
REDIS_URL=${{Redis.REDIS_URL}}

# Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Generate Secure Keys

**DO NOT use the default keys in production!**

Generate strong keys:

```bash
# Generate MASTER_KEY
openssl rand -hex 32

# Generate LITELLM_MASTER_KEY
openssl rand -hex 32
```

Format them:
```bash
MASTER_KEY=sk-admin-<generated-hex>
LITELLM_MASTER_KEY=sk-litellm-<generated-hex>
```

**IMPORTANT**: The `LITELLM_MASTER_KEY` must be the SAME in both SaaS API and LiteLLM Proxy services!

---

## Deployment Steps

1. **Generate Secure Keys** (see above)

2. **Add to Railway** (both services)
   - Go to Railway dashboard
   - Select your project
   - For each service, go to Variables tab
   - Add the required environment variables
   - Click "Deploy" or wait for auto-deploy

3. **Verify Deployment**
   ```bash
   # Test SaaS API (should return 401 if not authenticated)
   curl https://your-saas-api.railway.app/api/organizations

   # Test with auth
   curl -H "X-Admin-Key: your-master-key" https://your-saas-api.railway.app/api/organizations
   ```

4. **Check Logs**
   - Look for security warnings
   - Should NOT see: "Using default MASTER_KEY"
   - Should NOT see: "Using default LITELLM_MASTER_KEY"

---

## Current Status

✅ **Fix Deployed**: App won't crash anymore
⚠️ **Action Required**: Set proper environment variables
⚠️ **Security Risk**: Default keys are being used until you update them

---

## Troubleshooting

### "Still seeing default key warnings"
- Verify environment variables are set in Railway
- Restart the service after adding variables
- Check logs for loaded environment values

### "401 Unauthorized" errors
- Verify MASTER_KEY matches between client and server
- Check X-Admin-Key header is being sent
- Verify LITELLM_MASTER_KEY is the same in both services

### "Failed to connect to LiteLLM"
- Verify LITELLM_PROXY_URL is correct for Railway
- Should be: `http://litellm-proxy.railway.internal:4000`
- Verify LITELLM_MASTER_KEY matches in both services

---

## Security Checklist

- [ ] Generated secure MASTER_KEY (not default)
- [ ] Generated secure LITELLM_MASTER_KEY (not default)
- [ ] Added MASTER_KEY to Railway (saas-api service)
- [ ] Added LITELLM_MASTER_KEY to Railway (both services, same value)
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=false
- [ ] Verified no "default key" warnings in logs
- [ ] Tested authentication works
- [ ] Saved keys securely (password manager)

---

## Reference

Full documentation: `docs/environment-variables.md`

Railway template variables:
- `${{Postgres.DATABASE_URL}}` - Auto-populated by Railway
- `${{Redis.REDISHOST}}` - Auto-populated by Railway
- `${{Redis.REDISPORT}}` - Auto-populated by Railway
- `${{Redis.REDIS_PASSWORD}}` - Auto-populated by Railway
- `${{Redis.REDIS_URL}}` - Auto-populated by Railway

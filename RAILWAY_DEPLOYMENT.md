# Railway Deployment Guide

This guide covers deploying your LiteLLM SaaS platform to Railway with separate services.

**📖 Using Config-as-Code?** See [RAILWAY_CONFIG_GUIDE.md](RAILWAY_CONFIG_GUIDE.md) for automated deployment setup with `railway.toml`!

## Architecture Overview

Your Railway project will have **4 services**:

1. **PostgreSQL** (Managed Database Addon)
2. **Redis** (Managed Database Addon)
3. **LiteLLM Proxy** (Custom Service)
4. **FastAPI SaaS API** (Custom Service)

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Project                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐      ┌──────────────┐                  │
│  │  PostgreSQL │◄─────┤ LiteLLM Proxy│                  │
│  │  (Managed)  │      │ (Port 4000)  │                  │
│  └──────┬──────┘      └──────┬───────┘                  │
│         │                    │                           │
│         │             ┌──────▼────────┐                 │
│         └─────────────┤  FastAPI SaaS │                 │
│                       │  (Port 8000)  │                 │
│  ┌─────────────┐      └───────────────┘                 │
│  │    Redis    │                                         │
│  │  (Managed)  │◄────────────────────────────────────── │
│  └─────────────┘                                         │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Choose "Empty Project"

### Step 2: Add PostgreSQL

1. Click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway will provision and provide `DATABASE_URL`

### Step 3: Add Redis

1. Click "+ New"
2. Select "Database" → "Redis"
3. Railway will provision and provide `REDIS_URL`

### Step 4: Deploy LiteLLM Proxy Service

1. Click "+ New" → "GitHub Repo"
2. Connect your `SaasLiteLLM` repository
3. Railway will auto-detect `Dockerfile` (no configuration needed!)
4. Name the service: `litellm-proxy`
5. Railway will automatically build and deploy using port `4000`

### Step 5: Deploy FastAPI SaaS API Service

1. Click "+ New" → "GitHub Repo" (same repository)
2. Add as second service from same repo
3. Name the service: `saas-api`
4. **IMPORTANT**: In Variables tab, add:
   ```
   RAILWAY_DOCKERFILE_PATH=Dockerfile.saas
   ```
5. Railway will build using `Dockerfile.saas` and deploy on port `8000`

---

## Environment Variables

### 🔧 LiteLLM Proxy Service

Set these in Railway dashboard for the **LiteLLM Proxy** service:

**Note**: No need to set `RAILWAY_DOCKERFILE_PATH` - Railway auto-detects the root `Dockerfile`!

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `LITELLM_MASTER_KEY` | ✅ | Admin authentication key | `sk-prod-1234567890abcdef` |
| `OPENAI_API_KEY` | ✅ | OpenAI API key | `sk-proj-...` |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key | `sk-ant-...` |
| `REDIS_HOST` | ⚠️ | Redis hostname (Railway internal) | `redis.railway.internal` |
| `REDIS_PORT` | ⚠️ | Redis port | `6379` |
| `REDIS_PASSWORD` | ⚠️ | Redis password (if managed) | Auto from Railway |

**Note**: Railway's managed Redis provides a `REDIS_URL` that includes host, port, and password. You can either:
- Use `REDIS_URL` directly (preferred)
- Or extract and set `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` separately

#### How to Set:

```bash
# In Railway dashboard for LiteLLM service:
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=sk-prod-<generate-secure-random-key>
OPENAI_API_KEY=<your-openai-key>
ANTHROPIC_API_KEY=<your-anthropic-key>
REDIS_URL=${{Redis.REDIS_URL}}
```

---

### 🔧 FastAPI SaaS API Service

Set these in Railway dashboard for the **SaaS API** service:

**CRITICAL**: Must include `RAILWAY_DOCKERFILE_PATH` to use the correct Dockerfile!

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `RAILWAY_DOCKERFILE_PATH` | ✅ | **CRITICAL**: Tells Railway which Dockerfile to use | `Dockerfile.saas` |
| `DATABASE_URL` | ✅ | PostgreSQL connection string (same as LiteLLM) | `postgresql://user:pass@host:5432/db` |
| `LITELLM_MASTER_KEY` | ✅ | Must match LiteLLM proxy's key | `sk-prod-1234567890abcdef` |
| `LITELLM_PROXY_URL` | ✅ | Internal URL to LiteLLM service | `http://litellm-proxy.railway.internal:4000` |
| `PORT` | 🔹 | Railway assigns automatically | `8000` (default) |
| `HOST` | 🔹 | Bind address | `0.0.0.0` |
| `ENVIRONMENT` | 🔹 | Environment name | `production` |
| `DEBUG` | 🔹 | Debug mode | `false` |

#### How to Set:

```bash
# In Railway dashboard for SaaS API service:
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=${{litellm-proxy.LITELLM_MASTER_KEY}}
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
ENVIRONMENT=production
DEBUG=false
```

**Note**: Railway provides private networking. Use `<service-name>.railway.internal` to communicate between services.

---

## Environment Variable Reference

### 📋 Quick Copy for LiteLLM Proxy

```bash
# Copy these to Railway's LiteLLM service environment variables
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=sk-prod-CHANGE-ME-TO-SECURE-RANDOM-KEY
OPENAI_API_KEY=sk-proj-YOUR-OPENAI-KEY
ANTHROPIC_API_KEY=sk-ant-YOUR-ANTHROPIC-KEY
REDIS_URL=${{Redis.REDIS_URL}}
```

### 📋 Quick Copy for FastAPI SaaS API

```bash
# Copy these to Railway's SaaS API service environment variables
RAILWAY_DOCKERFILE_PATH=Dockerfile.saas
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=${{litellm-proxy.LITELLM_MASTER_KEY}}
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
ENVIRONMENT=production
DEBUG=false
```

---

## Generating Secure Master Key

**CRITICAL**: Generate a secure random key for production:

```bash
# Generate a secure 32-character key
python3 -c "import secrets; print(f'sk-prod-{secrets.token_urlsafe(32)}')"
```

Output example:
```
sk-prod-8vN_zK2QmR4tX7wY3jL9pF1nH6cV5bA8
```

Use this same key for both services!

---

## Post-Deployment Steps

### 1. Run Database Migrations

After both services are deployed, SSH into the **SaaS API** service and run:

```bash
# Railway CLI
railway shell

# Inside the shell:
python3 -c "
from src.models.job_tracking import Base
from sqlalchemy import create_engine
import os

engine = create_engine(os.environ['DATABASE_URL'])
Base.metadata.create_all(engine)
print('✅ Job tracking tables created')
"
```

Or create a migration script that runs automatically on deploy.

### 2. Verify LiteLLM Health

```bash
# Check LiteLLM is running
curl https://your-litellm-service.railway.app/health

# Should return:
# {"status": "healthy"}
```

### 3. Verify SaaS API Health

```bash
# Check SaaS API is running
curl https://your-saas-api.railway.app/health

# Should return:
# {"status": "healthy", "service": "saas-llm-api"}
```

### 4. Test End-to-End

```bash
# Create a test job
curl -X POST https://your-saas-api.railway.app/api/jobs/create \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "test-team",
    "job_type": "test",
    "metadata": {"test": true}
  }'

# Should return job_id
```

---

## Railway-Specific Notes

### Private Networking

Railway services can communicate privately using:
```
http://<service-name>.railway.internal:<port>
```

For example:
- FastAPI → LiteLLM: `http://litellm-proxy.railway.internal:4000`
- LiteLLM → PostgreSQL: Auto-configured via `${{Postgres.DATABASE_URL}}`
- LiteLLM → Redis: Auto-configured via `${{Redis.REDIS_URL}}`

### Public URLs

Railway assigns public URLs:
- LiteLLM Proxy: `https://<random>.railway.app` (exposed for admin UI)
- SaaS API: `https://<random>.railway.app` (exposed for your customers)

You can add custom domains in Railway dashboard.

### PORT Environment Variable

Railway automatically sets `PORT` for each service. Your Dockerfiles should use:
```dockerfile
CMD uvicorn src.saas_api:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Database Connection Pooling

For production, consider adding to `DATABASE_URL`:
```
?pool_size=20&max_overflow=10
```

Example:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=10
```

---

## Monitoring

### View Logs

```bash
# Railway CLI
railway logs --service litellm-proxy
railway logs --service saas-api
```

### Metrics

Railway provides metrics for:
- CPU usage
- Memory usage
- Network traffic
- Response times

Access via Railway dashboard → Service → Metrics tab

---

## Troubleshooting

### Issue: LiteLLM can't connect to PostgreSQL

**Check**:
1. `DATABASE_URL` is set correctly
2. PostgreSQL service is healthy
3. Look for Prisma errors in logs

**Fix**:
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:5432/db
```

### Issue: SaaS API can't reach LiteLLM

**Check**:
1. `LITELLM_PROXY_URL` uses Railway internal networking
2. LiteLLM service is running
3. Port is correct (4000)

**Fix**:
```bash
# Use Railway's private networking
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
```

### Issue: Redis connection failed

**Check**:
1. Redis addon is provisioned
2. `REDIS_URL` is set
3. LiteLLM can parse the URL

**Fix**:
```bash
# Use Railway's managed Redis URL
REDIS_URL=${{Redis.REDIS_URL}}
```

### Issue: Database tables not found

**Fix**: Run migrations after first deploy:
```bash
railway shell --service saas-api
python scripts/init_job_tracking_db.py
```

---

## Cost Optimization

### Railway Pricing Tips

1. **Use managed databases** - More reliable than self-hosted
2. **Set resource limits** - Prevent unexpected costs
3. **Enable autoscaling** - Scale down during low traffic
4. **Use Redis caching** - Reduce LLM API calls

### Example Monthly Costs (Estimated)

- **Starter Plan**: $5/month (1 project, managed DB included)
- **PostgreSQL**: Included in Starter
- **Redis**: Included in Starter
- **LiteLLM Service**: ~$5-10/month (depends on traffic)
- **SaaS API Service**: ~$5-10/month (depends on traffic)

**Total**: ~$15-25/month for small-scale production

---

## Security Checklist

- [ ] Generated secure random `LITELLM_MASTER_KEY`
- [ ] Same master key used in both services
- [ ] Real API keys for OpenAI/Anthropic (not placeholders)
- [ ] `DEBUG=false` in production
- [ ] Database URL uses SSL (`?sslmode=require`)
- [ ] Railway services use private networking
- [ ] Environment variables not committed to git
- [ ] Custom domain with HTTPS (optional)
- [ ] Rate limiting enabled in LiteLLM config
- [ ] Team budgets configured

---

## Next Steps After Deployment

1. ✅ Test health endpoints
2. ✅ Run database migrations
3. ✅ Create test job to verify end-to-end
4. ⬜ Set up custom domains
5. ⬜ Configure webhooks for job events
6. ⬜ Add monitoring/alerting (e.g., Sentry)
7. ⬜ Set up CI/CD for auto-deploy
8. ⬜ Create admin dashboard
9. ⬜ Document API for your customers

---

## Support

- **Railway Docs**: https://docs.railway.app
- **LiteLLM Docs**: https://docs.litellm.ai
- **Project Issues**: https://github.com/GittieLabs/SaasLiteLLM/issues

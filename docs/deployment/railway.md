# Railway Deployment

Deploy SaaS LiteLLM to [Railway](https://railway.app) for production use.

## Overview

Railway deployment consists of **3 services**:

1. **PostgreSQL Database** - Managed database
2. **SaaS API** - Main FastAPI application (port 8003)
3. **MkDocs Docs** - Documentation site (port 8004)
4. **Admin Panel** (optional) - Next.js dashboard (port 3000)

## Prerequisites

- Railway account ([signup](https://railway.app))
- GitHub repository with SaasLiteLLM code
- OpenAI API key (or other LLM provider keys)

## Step 1: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your SaasLiteLLM repository
5. Railway will detect the project structure

## Step 2: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database" → "PostgreSQL"**
3. Railway automatically creates and configures the database
4. Note the connection details (or use `${{Postgres.DATABASE_URL}}`)

## Step 3: Configure SaaS API Service

### Service Settings

- **Name:** `saas-api`
- **Root Directory:** (leave empty - uses repository root)
- **Dockerfile Path:** `Dockerfile`

### Environment Variables

Add these variables to the SaaS API service:

```bash
# Database (automatically provided by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# LiteLLM Proxy (use your LiteLLM Cloud or self-hosted URL)
LITELLM_PROXY_BASE_URL=https://your-litellm-proxy.com

# Master Key (generate a secure key)
MASTER_KEY=sk-master-xxxxxxxxxxxxxxxxxxxxxxxx

# LLM Provider Keys
OPENAI_API_KEY=sk-your-openai-key
# Add other provider keys as needed:
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# GOOGLE_API_KEY=xxxxx
# AZURE_API_KEY=xxxxx
```

### Generate Master Key

```bash
python -c "import secrets; print('sk-master-' + secrets.token_urlsafe(32))"
```

### Networking

Railway will automatically:
- Assign a public URL (e.g., `https://saas-api-production-xxxxx.up.railway.app`)
- Expose port 8003
- Enable HTTPS

## Step 4: Run Database Migrations

After the SaaS API deploys:

1. Go to the service **Settings** → **Variables**
2. Add temporary variable for migration:
   ```
   RUN_MIGRATIONS=true
   ```
3. Redeploy the service
4. Check logs to verify migrations ran successfully
5. Remove the `RUN_MIGRATIONS` variable

**Or run migrations manually:**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run psql $DATABASE_URL -f scripts/migrations/001_initial_schema.sql
# Repeat for all migrations...
```

## Step 5: Configure MkDocs Docs Service

### Service Settings

- **Name:** `docs`
- **Root Directory:** `docs-service`
- **Dockerfile Path:** `Dockerfile`

### Environment Variables

None needed - `PORT` is automatically provided by Railway.

### Networking

Railway will assign a public URL for the docs (e.g., `https://docs-xxxxx.up.railway.app`)

## Step 6: Configure Admin Panel (Optional)

### Service Settings

- **Name:** `admin-panel`
- **Root Directory:** `admin-panel`
- **Build Command:** `npm run build`
- **Start Command:** `npm run start`

### Environment Variables

```bash
# API URL (use your SaaS API Railway URL)
NEXT_PUBLIC_API_URL=${{saas-api.RAILWAY_PUBLIC_URL}}

# Node environment
NODE_ENV=production
```

Railway will automatically detect Next.js and configure the build.

## Step 7: Verify Deployment

### Check Health Endpoint

```bash
curl https://your-saas-api-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "litellm_proxy": "reachable"
}
```

### Create Test Organization

```bash
curl -X POST https://your-saas-api-url.railway.app/api/organizations/create \
  -H "Authorization: Bearer sk-master-xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "test-org",
    "org_name": "Test Organization"
  }'
```

### Access Documentation

Visit `https://your-docs-url.railway.app` to see the deployed documentation.

## Environment Management

### Production vs Staging

Create separate Railway projects for different environments:

**Production:**
- Project name: `saas-litellm-production`
- Branch: `main`
- Domain: `api.yourcompany.com` (custom domain)

**Staging:**
- Project name: `saas-litellm-staging`
- Branch: `develop`
- Domain: Railway-provided URL

### Custom Domains

1. Go to service **Settings** → **Networking**
2. Click **"Generate Domain"** or **"Custom Domain"**
3. Add your custom domain (e.g., `api.yourcompany.com`)
4. Update DNS records as instructed by Railway

### Environment Variables

Access via Railway Dashboard:
- **Shared Variables:** Available to all services
- **Service Variables:** Specific to one service
- **Reference Variables:** Use `${{service.VARIABLE_NAME}}`

## Scaling

Railway automatically scales based on usage:

- **Vertical Scaling:** Increase memory/CPU in service settings
- **Horizontal Scaling:** Available on Pro plan
- **Database:** Can upgrade PostgreSQL plan for more resources

## Monitoring

### View Logs

1. Go to service in Railway Dashboard
2. Click **"Logs"** tab
3. Filter by severity, search, or time range

### Metrics

Railway provides built-in metrics:
- CPU usage
- Memory usage
- Network traffic
- Request count

### Alerts

Set up alerts in Railway Dashboard:
- Service crashes
- High resource usage
- Deployment failures

## Backup & Recovery

### Database Backups

Railway provides automatic daily backups for PostgreSQL:

1. Go to database service
2. Click **"Backups"** tab
3. View available backups
4. Restore from backup if needed

### Manual Backup

```bash
# Export database
railway run pg_dump $DATABASE_URL > backup.sql

# Restore database
railway run psql $DATABASE_URL < backup.sql
```

## Troubleshooting

### Deployment Failed

**Check logs:**
1. Go to service → Deployments
2. Click failed deployment
3. View build/deploy logs for errors

**Common issues:**
- Missing environment variables
- Database connection failed
- Docker build errors

### Database Connection Issues

**Check:**
1. `DATABASE_URL` is correctly set
2. PostgreSQL service is running
3. Migrations completed successfully

**Test connection:**
```bash
railway run psql $DATABASE_URL -c "SELECT 1"
```

### Out of Memory

**Solution:**
1. Go to service Settings
2. Increase memory allocation
3. Redeploy service

### LiteLLM Proxy Unreachable

**Check:**
1. `LITELLM_PROXY_BASE_URL` is correct
2. LiteLLM proxy is running and accessible
3. Network connectivity from Railway

## Cost Optimization

Railway pricing is usage-based:

**Tips to reduce costs:**
- Use resource limits
- Scale down staging environments when not in use
- Optimize Docker image size
- Use shared PostgreSQL for development
- Monitor usage in Railway Dashboard

**Typical monthly costs:**
- Hobby plan: $5/month + usage
- Pro plan: $20/month + usage
- Database: ~$5-20/month depending on size

## Next Steps

- **[Environment Variables](environment-variables.md)** - Complete configuration reference
- **[Docker Setup](docker.md)** - Customize Docker builds
- **[Monitoring](../admin-dashboard/monitoring.md)** - Track system health

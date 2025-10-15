# Railway Config-as-Code Setup Guide

This guide explains how to use Railway's config-as-code approach with multiple services from the same repository.

## 📁 Configuration Files

Your repository includes multiple Railway configuration options:

### **Option 1: TOML Format** (Recommended)

```
├── railway.toml           # Default config (LiteLLM service)
├── railway.saas.toml      # SaaS API service config
```

### **Option 2: JSON Format** (With Schema Autocomplete)

```
├── .railway/
│   ├── litellm.json      # LiteLLM service config
│   └── saas.json         # SaaS API service config
```

---

## 🚀 Deployment Setup

### **Service 1: LiteLLM Proxy**

#### Method A: Default railway.toml (Easiest)

1. **Create service** in Railway from GitHub repo
2. **Railway auto-detects** `railway.toml` ✓
3. **Add environment variables**:
   ```bash
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   LITELLM_MASTER_KEY=sk-prod-YOUR-KEY
   OPENAI_API_KEY=sk-proj-YOUR-KEY
   ANTHROPIC_API_KEY=sk-ant-YOUR-KEY
   REDIS_URL=${{Redis.REDIS_URL}}
   ```
4. **Deploy!**

Railway will use:
- Config: `railway.toml`
- Dockerfile: `Dockerfile` (default)
- Health check: `/health`
- Port: `4000`

#### Method B: Using JSON config

1. **Create service** in Railway
2. **Go to Settings** → "Config File Path"
3. **Set path**: `.railway/litellm.json`
4. **Add environment variables** (same as above)
5. **Deploy!**

---

### **Service 2: SaaS API**

Since this is a **second service from the same repo**, you need to specify which config file to use:

#### Method A: Using railway.saas.toml

1. **Create second service** from same GitHub repo
2. **Go to Settings** → "Config File Path"
3. **Set path**: `railway.saas.toml`
4. **Add environment variables**:
   ```bash
   RAILWAY_DOCKERFILE_PATH=Dockerfile.saas
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   LITELLM_MASTER_KEY=${{litellm-proxy.LITELLM_MASTER_KEY}}
   LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
   ENVIRONMENT=production
   DEBUG=false
   ```
5. **Deploy!**

#### Method B: Using .railway/saas.json

1. **Create second service** from same GitHub repo
2. **Go to Settings** → "Config File Path"
3. **Set path**: `.railway/saas.json`
4. **Add environment variables** (same as Method A)
5. **Deploy!**

---

## 📝 Configuration File Details

### **railway.toml** (LiteLLM Proxy)

```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "--config /app/config.yaml --port 4000 --detailed_debug"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
```

**What this does**:
- Uses Dockerfile builder (not Nixpacks)
- Starts LiteLLM with detailed debugging
- Health checks at `/health` endpoint
- Restarts on failure

---

### **railway.saas.toml** (SaaS API)

```toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
```

**What this does**:
- Uses Dockerfile builder
- No custom start command (uses Dockerfile CMD)
- Health checks at `/health` endpoint
- Restarts on failure

**Important**: Must also set `RAILWAY_DOCKERFILE_PATH=Dockerfile.saas` in environment variables!

---

### **JSON Configs** (.railway/*.json)

Same functionality as TOML, but with:
- JSON schema for autocomplete in editors
- Slightly different format (e.g., `"DOCKERFILE"` vs `"dockerfile"`)

---

## 🔧 Why Use Config-as-Code?

### **Benefits**:

✅ **Version controlled** - Configuration lives in git
✅ **Consistent deploys** - Same config every time
✅ **Team collaboration** - Everyone sees the same setup
✅ **Self-documenting** - Config explains deployment
✅ **No manual clicking** - Automated deployment setup

### **What It Configures**:

- **Build method** (Dockerfile vs Nixpacks)
- **Start command** override
- **Health check path** and timeout
- **Restart policy**
- **Pre-deploy commands** (migrations, etc.)

### **What It Doesn't Configure** (Still Need Dashboard):

- ❌ Environment variables
- ❌ Dockerfile path (use `RAILWAY_DOCKERFILE_PATH` variable)
- ❌ Service name
- ❌ Resource limits

---

## 📊 Deployment Flow

### **LiteLLM Service**:

```
Push to GitHub
    ↓
Railway detects railway.toml
    ↓
Builds using Dockerfile (root)
    ↓
Starts with: --config /app/config.yaml --port 4000 --detailed_debug
    ↓
Health check: http://service:4000/health
    ↓
✅ Service running
```

### **SaaS API Service**:

```
Push to GitHub
    ↓
Railway reads railway.saas.toml (from Settings > Config File Path)
    ↓
Reads RAILWAY_DOCKERFILE_PATH=Dockerfile.saas (from Variables)
    ↓
Builds using Dockerfile.saas
    ↓
Starts with: uvicorn src.saas_api:app (from Dockerfile CMD)
    ↓
Health check: http://service:8000/health
    ↓
✅ Service running
```

---

## 🎯 Quick Setup Checklist

### **LiteLLM Service**:
- [ ] Service created from GitHub repo
- [ ] Railway auto-detected `railway.toml`
- [ ] Environment variables added (DATABASE_URL, keys, etc.)
- [ ] Deployed successfully
- [ ] Health check passing at `/health`

### **SaaS API Service**:
- [ ] Second service created from same repo
- [ ] Settings > Config File Path = `railway.saas.toml`
- [ ] `RAILWAY_DOCKERFILE_PATH=Dockerfile.saas` in Variables
- [ ] Environment variables added (DATABASE_URL, LITELLM_PROXY_URL, etc.)
- [ ] Deployed successfully
- [ ] Health check passing at `/health`
- [ ] Can connect to LiteLLM via private networking

---

## 🐛 Troubleshooting

### **Issue**: Railway not detecting railway.toml

**Solution**:
- Ensure `railway.toml` is in repository root
- Check file is committed to git
- Try redeploying after push

---

### **Issue**: Second service using wrong Dockerfile

**Solution**:
1. Go to service Settings > Config File Path
2. Set to: `railway.saas.toml`
3. Go to Variables tab
4. Add: `RAILWAY_DOCKERFILE_PATH=Dockerfile.saas`
5. Redeploy

---

### **Issue**: Health check failing

**Solution**:
- Verify your service exposes `/health` endpoint
- Check `healthcheckTimeout` isn't too short (default: 100s)
- View logs to see if service is starting properly
- Ensure port matches (4000 for LiteLLM, 8000 for SaaS API)

---

### **Issue**: Build command not working

**Solution**:
- For Docker builds, don't set `buildCommand` in railway.toml
- Docker handles build automatically
- Only set `startCommand` if you need to override Dockerfile CMD

---

## 📖 References

- **Railway Config Docs**: https://docs.railway.com/guides/config-as-code
- **Railway Dockerfile Guide**: https://docs.railway.com/guides/dockerfiles
- **JSON Schema**: https://railway.com/railway.schema.json

---

## 🎓 Best Practices

1. **Use TOML for simplicity** - Easier to read and write
2. **Use JSON for IDE autocomplete** - Better developer experience
3. **Keep configs minimal** - Only override what you need
4. **Document environment variables** - Config files don't include secrets
5. **Version control everything** - Commit config changes with code
6. **Test locally with Docker** - Verify Dockerfiles work before deploying

---

## 🔐 Security Note

**Never put secrets in config files!**

Config files should only contain:
- ✅ Build settings
- ✅ Health check paths
- ✅ Restart policies
- ✅ Start commands

Always use Railway's Variables tab for:
- ❌ API keys
- ❌ Database URLs
- ❌ Master keys
- ❌ Any sensitive data

---

## 🚀 You're All Set!

Your Railway deployment is now configured as code. Any changes to `railway.toml` or `railway.saas.toml` will automatically apply on the next deployment.

Happy deploying! 🎉

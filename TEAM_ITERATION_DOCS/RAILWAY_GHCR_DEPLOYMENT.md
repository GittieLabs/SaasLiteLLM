# Railway Deployment with GitHub Container Registry

This guide covers deploying pre-built Docker images from GitHub Container Registry (GHCR) to Railway.

## 🎯 Why This Approach?

**Benefits:**
- ✅ **Faster deployments** - No build time on Railway
- ✅ **Consistent images** - Same image everywhere
- ✅ **Separate build from deploy** - Debug builds independently
- ✅ **Better caching** - GitHub Actions handles layer caching
- ✅ **Free builds** - GitHub Actions has generous free tier
- ✅ **Automatic builds** - Push to main triggers builds

---

## 🏗️ Architecture

```
GitHub Push (main branch)
    ↓
GitHub Actions builds Docker images
    ↓
Images pushed to ghcr.io
    ↓
Railway pulls and runs images
    ↓
✅ Services running
```

### **Images Built:**

1. **LiteLLM Proxy**: `ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest`
2. **SaaS API**: `ghcr.io/gittielabs/saaslitellm/saas-api:latest`

---

## 🚀 Setup Steps

### **Step 1: Enable GitHub Actions** ✓

GitHub Actions workflows are already configured in `.github/workflows/`:
- `build-litellm.yml` - Builds LiteLLM proxy image
- `build-saas.yml` - Builds SaaS API image

**What they do:**
- Trigger on push to `main` branch
- Build Docker images
- Push to GitHub Container Registry
- Cache layers for faster builds
- Tag with `latest` and commit SHA

---

### **Step 2: Make Images Public** (Important!)

After the first GitHub Actions run, you need to make the images public so Railway can pull them without authentication:

1. **Go to**: https://github.com/orgs/GittieLabs/packages
2. **Find package**: `saaslitellm/litellm-proxy`
3. **Click** → Package settings
4. **Scroll down** to "Danger Zone"
5. **Click** "Change visibility" → **Public**
6. **Repeat** for `saaslitellm/saas-api`

**Why?** Railway needs to pull the images without authentication credentials.

---

### **Step 3: Deploy to Railway**

Now deploy using the pre-built images instead of building from source.

#### **Service 1: LiteLLM Proxy**

1. **Create new service** in Railway
2. **Select** "Docker Image" (NOT GitHub repo)
3. **Image URL**:
   ```
   ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest
   ```
4. **Add environment variables**:
   ```bash
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   LITELLM_MASTER_KEY=sk-prod-F7Irajj1REKzQEo1sWeyvVzRVLGoBrD1jCpeSNqkODQ
   OPENAI_API_KEY=your-openai-key
   ANTHROPIC_API_KEY=your-anthropic-key
   REDIS_HOST=${{Redis.REDIS_HOST}}
   REDIS_PORT=${{Redis.REDIS_PORT}}
   ```
5. **Deploy!**

#### **Service 2: SaaS API**

1. **Create new service** in Railway
2. **Select** "Docker Image"
3. **Image URL**:
   ```
   ghcr.io/gittielabs/saaslitellm/saas-api:latest
   ```
4. **Add environment variables**:
   ```bash
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   LITELLM_MASTER_KEY=${{litellm-proxy.LITELLM_MASTER_KEY}}
   LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
   ENVIRONMENT=production
   DEBUG=false
   ```
5. **Deploy!**

---

## 🔄 Automatic Updates

### **How It Works:**

```
1. You push code to main branch
    ↓
2. GitHub Actions automatically builds new images
    ↓
3. Railway detects new image tag
    ↓
4. Railway automatically redeploys
```

**Note**: Railway can auto-deploy on new image tags, but you may need to manually trigger a redeploy after the first push.

---

## 📋 Environment Variables

### **LiteLLM Proxy Service**

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=sk-prod-F7Irajj1REKzQEo1sWeyvVzRVLGoBrD1jCpeSNqkODQ
OPENAI_API_KEY=sk-proj-YOUR-KEY
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
```

### **SaaS API Service**

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
LITELLM_MASTER_KEY=${{litellm-proxy.LITELLM_MASTER_KEY}}
LITELLM_PROXY_URL=http://litellm-proxy.railway.internal:4000
ENVIRONMENT=production
DEBUG=false
```

---

## 🧪 Testing Images Locally

Before deploying to Railway, test the images locally:

### **Pull and run LiteLLM:**

```bash
# Pull from GHCR
docker pull ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest

# Run locally
docker run -p 4000:4000 \
  -e DATABASE_URL="your-db-url" \
  -e LITELLM_MASTER_KEY="sk-prod-F7Irajj1REKzQEo1sWeyvVzRVLGoBrD1jCpeSNqkODQ" \
  -e OPENAI_API_KEY="your-key" \
  ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest

# Test health check
curl http://localhost:4000/health
```

### **Pull and run SaaS API:**

```bash
# Pull from GHCR
docker pull ghcr.io/gittielabs/saaslitellm/saas-api:latest

# Run locally
docker run -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  -e LITELLM_MASTER_KEY="sk-prod-F7Irajj1REKzQEo1sWeyvVzRVLGoBrD1jCpeSNqkODQ" \
  -e LITELLM_PROXY_URL="http://host.docker.internal:4000" \
  ghcr.io/gittielabs/saaslitellm/saas-api:latest

# Test health check
curl http://localhost:8000/health
```

---

## 🔍 Monitoring Builds

### **Check GitHub Actions:**

1. Go to: https://github.com/GittieLabs/SaasLiteLLM/actions
2. Click on latest workflow run
3. View build logs and status

### **Check Images:**

1. Go to: https://github.com/orgs/GittieLabs/packages
2. View available tags and versions
3. Check image size and layers

---

## 🐛 Troubleshooting

### **Issue: GitHub Actions workflow not running**

**Solution:**
- Ensure workflows are enabled in repo settings
- Check if paths in `on.push.paths` match your changes
- Manually trigger with workflow_dispatch

### **Issue: Railway can't pull image**

**Solution:**
- Verify image is set to **Public** in GitHub packages
- Check image URL is correct (case-sensitive!)
- Ensure image exists: `docker pull ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest`

### **Issue: Image builds but fails to run**

**Solution:**
- Check Railway logs for errors
- Test image locally first
- Verify environment variables are set
- Check health check endpoint is responding

### **Issue: Railway not auto-updating on new image**

**Solution:**
- Manually trigger redeploy in Railway
- Or set up webhook from GitHub Actions to Railway
- Or use Railway CLI to deploy: `railway up`

---

## 🎯 Workflow Triggers

Both workflows trigger on:

### **Automatic (on push to main):**
- `build-litellm.yml`: When `Dockerfile`, `Dockerfile.litellm`, or `src/config/**` changes
- `build-saas.yml`: When `Dockerfile.saas`, `src/**`, or `pyproject.toml` changes

### **Manual:**
- Go to Actions tab → Select workflow → "Run workflow"

---

## 📊 Image Tags

Each build creates multiple tags:

- `latest` - Always points to latest main branch
- `main-<sha>` - Specific commit on main branch
- `main` - Latest main branch build

**Example:**
```
ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest
ghcr.io/gittielabs/saaslitellm/litellm-proxy:main
ghcr.io/gittielabs/saaslitellm/litellm-proxy:main-a1b2c3d
```

---

## 🔐 Security Notes

### **Image Visibility:**
- Images must be **public** for Railway to pull without auth
- Alternatively, use Railway secrets to authenticate with GHCR (more complex)

### **Secrets in Images:**
- ❌ Never bake API keys into images
- ✅ Always pass via environment variables
- ✅ Use Railway's Variables tab for secrets

### **GITHUB_TOKEN:**
- Automatically provided by GitHub Actions
- Has permission to push to GHCR
- No manual setup needed

---

## 📈 Next Steps

1. **Push to main** - Triggers automatic image builds
2. **Wait for GitHub Actions** - Takes 2-5 minutes
3. **Make images public** - Required for Railway access
4. **Deploy to Railway** - Use pre-built images
5. **Test endpoints** - Verify health checks pass
6. **Run migrations** - Initialize database tables

---

## 🎓 Best Practices

1. **Tag versions properly** - Use semantic versioning for releases
2. **Test images locally** - Before deploying to Railway
3. **Monitor build times** - Optimize Dockerfiles if needed
4. **Use layer caching** - Already configured in workflows
5. **Review logs** - Check GitHub Actions for build errors
6. **Keep images small** - Remove unnecessary dependencies

---

## 📖 References

- **GitHub Container Registry**: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- **GitHub Actions**: https://docs.github.com/en/actions
- **Railway Docker Images**: https://docs.railway.com/deploy/dockerfiles
- **Your Packages**: https://github.com/orgs/GittieLabs/packages

---

## ✅ Checklist

### **Initial Setup:**
- [ ] Push code to trigger GitHub Actions
- [ ] Wait for workflows to complete
- [ ] Make both images public in GitHub packages
- [ ] Verify images are pullable: `docker pull ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest`

### **Railway Deployment:**
- [ ] Create Railway project with Postgres + Redis
- [ ] Create LiteLLM service from Docker image
- [ ] Add environment variables to LiteLLM
- [ ] Create SaaS API service from Docker image
- [ ] Add environment variables to SaaS API
- [ ] Test health endpoints
- [ ] Run database migrations

### **Verification:**
- [ ] LiteLLM health check: `curl https://your-litellm.railway.app/health`
- [ ] SaaS API health check: `curl https://your-saas.railway.app/health`
- [ ] Create test job via SaaS API
- [ ] Verify LLM calls work
- [ ] Check cost tracking

---

## 🎉 You're All Set!

Your deployment pipeline is now:

```
Code → GitHub → Actions → GHCR → Railway → Production
```

Every push to main automatically builds new images. Railway pulls and runs them. No more build issues! 🚀

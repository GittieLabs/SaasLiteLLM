# LiteLLM SaaS Platform

A production-ready LiteLLM deployment with **job-based cost tracking** for multi-tenant SaaS applications. Build your LLM-powered SaaS without exposing infrastructure complexity to your customers.

## Key Features

### 🎯 SaaS-Ready Architecture
- **Job-Based Tracking** - Group multiple LLM calls into business operations
- **Hidden Complexity** - Teams never see models, pricing, or LiteLLM
- **Cost Aggregation** - Track true costs per job, not per API call
- **Usage Analytics** - Detailed insights per team and job type

### 💰 Business Features
- **Cost Transparency** - See actual LiteLLM costs vs. customer pricing
- **Flexible Pricing** - Flat rate, tiered, or markup-based pricing
- **Budget Controls** - Per-team limits and alerts
- **Profit Tracking** - Calculate margins per job/team

### 🔧 Technical Features
- 🚀 Deploy to Railway with Docker
- 🐘 PostgreSQL database with job tracking schema
- 👥 Team management and isolation
- 🔑 Virtual API key generation (hidden from teams)
- 🔄 Multiple LLM providers (OpenAI, Anthropic, etc.)
- ⚡ Redis caching for performance and cost savings
- 📊 Rate limiting per team (TPM/RPM)
- 🐳 Docker Compose for local development

## Quick Start

### Local Development with Docker

1. **Setup the project:**
   ```bash
   chmod +x setup_env.sh
   ./setup_env.sh
   ```

2. **Start Docker services:**
   ```bash
   ./scripts/docker_setup.sh
   ```

3. **Configure API keys:**
   ```bash
   # Edit .env file and add your API keys
   nano .env
   ```

4. **Start the LiteLLM server:**
   ```bash
   source .venv/bin/activate
   python scripts/start_local.py
   ```

5. **Setup teams (after server is running):**
   ```bash
   python scripts/setup_teams.py
   ```

### SaaS API Setup (Recommended)

For job-based cost tracking:

```bash
# 1. Start Docker services
./scripts/docker_setup.sh

# 2. Create job tracking tables
./scripts/run_migrations.sh

# 3. Activate environment
source .venv/bin/activate

# 4. Start LiteLLM backend (Terminal 1)
python scripts/start_local.py

# 5. Start SaaS API wrapper (Terminal 2)
python scripts/start_saas_api.py
```

> **📖 For detailed setup instructions, see [QUICKSTART.md](QUICKSTART.md)**

**Services:**
- **LiteLLM Backend**: http://localhost:8002 (internal, admin only)
- **SaaS API**: http://localhost:8003 (expose this to your teams)
- **API Documentation**: http://localhost:8003/docs

> **Note**: Local dev uses ports 8002/8003 to avoid conflicts. Production uses standard 8000.
> See [PORT_CONFIG.md](PORT_CONFIG.md) for details.

See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for detailed examples.

### Railway Deployment

**📦 Pre-built Docker Images (Recommended)**

We build Docker images automatically via GitHub Actions and push to GitHub Container Registry. This is the fastest and most reliable deployment method:

1. **Push to main branch** - GitHub Actions automatically builds images
2. **Make images public** - Required for Railway to pull them
3. **Deploy from GHCR**:
   - LiteLLM: `ghcr.io/gittielabs/saaslitellm/litellm-proxy:latest`
   - SaaS API: `ghcr.io/gittielabs/saaslitellm/saas-api:latest`

> **📖 See [RAILWAY_GHCR_DEPLOYMENT.md](RAILWAY_GHCR_DEPLOYMENT.md) for complete step-by-step instructions**

**Alternative: Build from Source**

If you prefer Railway to build from source:

> **📖 See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) or [RAILWAY_CONFIG_GUIDE.md](RAILWAY_CONFIG_GUIDE.md)**

## Local Development

### Docker Services

The project includes Docker Compose configuration for:

- **PostgreSQL 15**: Database server (localhost:5432)
- **Redis 7**: Caching server (localhost:6379) 
- **pgAdmin** (optional): Database management UI (localhost:5050)

### Commands

```bash
# Start Docker services
./scripts/docker_setup.sh

# Stop Docker services  
./scripts/stop_docker.sh

# Start with pgAdmin
docker compose --profile pgadmin up -d

# View logs
docker compose logs -f postgres
docker compose logs -f redis

# Reset database
docker compose down -v
./scripts/docker_setup.sh
```

### Local URLs

- **SaaS API**: http://localhost:8003 (for your teams)
- **SaaS API Docs**: http://localhost:8003/docs
- **LiteLLM Server**: http://localhost:8002 (internal only)
- **LiteLLM Admin UI**: http://localhost:8002/ui
- **LiteLLM API Docs**: http://localhost:8002/docs
- **pgAdmin**: http://localhost:5050 (admin@litellm.local/admin)

## Job-Based API Usage (SaaS Pattern)

### Example: Document Analysis Job

```python
import requests

API = "http://localhost:8003/api"

# 1. Create job for tracking multiple LLM calls
job = requests.post(f"{API}/jobs/create", json={
    "team_id": "acme-corp",
    "user_id": "john@acme.com",
    "job_type": "document_analysis",
    "metadata": {"document_id": "doc_123", "pages": 5}
}).json()

job_id = job["job_id"]

# 2. Make multiple LLM calls for this job
for page in range(1, 6):
    requests.post(f"{API}/jobs/{job_id}/llm-call", json={
        "messages": [
            {"role": "user", "content": f"Analyze page {page}..."}
        ],
        "purpose": f"page_{page}_analysis"
    })

# 3. Complete job and get aggregated costs
result = requests.post(f"{API}/jobs/{job_id}/complete", json={
    "status": "completed"
}).json()

print(f"Total LLM calls: {result['costs']['total_calls']}")
print(f"Total cost: ${result['costs']['total_cost_usd']}")  # Your internal cost
print(f"Customer price: $0.50")  # What you charge
print(f"Profit: ${0.50 - result['costs']['total_cost_usd']}")
```

**Key Benefits:**
- Teams never see model names or actual costs
- You track true costs per business operation
- Set your own pricing (flat rate, markup, tiered)
- Perfect for document processing, chat sessions, data extraction, etc.

See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for more patterns.

### Get Team Usage (Admin/Internal)

```bash
# Get team's usage summary for October 2024
curl "http://localhost:8003/api/teams/acme-corp/usage?period=2024-10"
```

Response:
```json
{
  "team_id": "acme-corp",
  "period": "2024-10",
  "summary": {
    "total_jobs": 250,
    "successful_jobs": 245,
    "total_cost_usd": 18.75,
    "avg_cost_per_job": 0.075
  },
  "job_types": {
    "document_analysis": {"count": 120, "cost_usd": 12.20},
    "chat_session": {"count": 100, "cost_usd": 5.25}
  }
}
```

### Direct LiteLLM API (Legacy/Admin Only)

For direct access to LiteLLM (admin only):

```bash
# Admin UI
http://localhost:8002/ui

# Generate team virtual key
curl -X POST http://localhost:8002/key/generate \
  -H "Authorization: Bearer sk-local-dev-master-key-change-me" \
  -d '{"team_id": "team_dev", "models": ["gpt-3.5-turbo"]}'
```

## Configuration

### Adding New Models
Edit `src/config/litellm_config.yaml`:

```yaml
model_list:
  - model_name: new-model
    litellm_params:
      model: provider/model-name
      api_key: os.environ/PROVIDER_API_KEY
```

### Environment Files

- `.env.local`: Local development with Docker
- `.env.example`: Template for Railway deployment
- `.env`: Your actual environment (not in git)

## Development

### Running Tests
```bash
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

### Code Formatting
```bash
black src/
ruff check src/
```

## Monitoring

- Health check: `/health`
- Metrics: `/metrics` 
- Admin dashboard: `/ui`
- API documentation: `/docs`

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Test connection manually
docker exec -it litellm-postgres psql -U litellm_user -d litellm
```

### Reset Everything
```bash
# Stop services and remove volumes
docker compose down -v

# Restart fresh
./scripts/docker_setup.sh
```

## Architecture Overview

```
┌─────────────────────────────────┐
│   Your SaaS Application         │
│   (Document processing, etc.)   │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   SaaS API (Port 8003)          │  ← Expose this to teams
│   - /api/jobs/create            │
│   - /api/jobs/{id}/llm-call     │
│   - /api/jobs/{id}/complete     │
│   - /api/teams/{id}/usage       │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   LiteLLM Proxy (Port 8002)     │  ← Internal only
│   - Virtual API keys            │
│   - Model routing               │
│   - Redis caching               │
│   - Rate limiting               │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   PostgreSQL Database           │
│   - jobs                        │
│   - llm_calls                   │
│   - job_cost_summaries          │
│   - team_usage_summaries        │
└─────────────────────────────────┘
```

**Why This Architecture?**

1. **Hidden Complexity** - Teams interact with your SaaS API, not LiteLLM
2. **Job-Based Costs** - Track costs for business operations, not individual API calls
3. **Flexible Pricing** - Charge what you want, track actual costs internally
4. **Multi-Tenant** - Isolated teams with their own budgets and limits

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

## Project Structure

```
SaasLiteLLM/
├── src/
│   ├── main.py                    # LiteLLM proxy entry point
│   ├── saas_api.py                # SaaS wrapper API (job tracking)
│   ├── config/
│   │   ├── settings.py            # Environment configuration
│   │   └── litellm_config.yaml    # Models, Redis, rate limits
│   └── models/
│       ├── database.py            # Database utilities
│       └── job_tracking.py        # Job schema (jobs, llm_calls, etc.)
├── scripts/
│   ├── start_local.py             # Start LiteLLM backend
│   ├── start_saas_api.py          # Start SaaS API wrapper
│   ├── init_job_tracking_db.py    # Initialize job tables
│   └── docker_setup.sh            # Start Postgres + Redis
├── docker-compose.yml             # Local dev services
├── Dockerfile                     # Railway deployment
├── ARCHITECTURE.md                # Detailed architecture guide
└── USAGE_EXAMPLES.md              # API usage examples
```

## Support

For issues and questions, please check the LiteLLM documentation or create an issue in this repository.

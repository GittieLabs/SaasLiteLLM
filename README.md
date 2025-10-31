# SaaS LiteLLM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/GittieLabs/SaasLiteLLM)](https://github.com/GittieLabs/SaasLiteLLM/releases)
[![Documentation](https://img.shields.io/badge/docs-github%20pages-blue)](https://gittielabs.github.io/SaasLiteLLM/)

A production-ready multi-tenant SaaS wrapper for [LiteLLM](https://github.com/BerriAI/litellm) with **job-based cost tracking**. Build your LLM-powered SaaS without exposing infrastructure complexity to your customers.

> **Built on [LiteLLM](https://github.com/BerriAI/litellm)** - The unified interface to 100+ LLM providers (OpenAI, Anthropic, Azure, Google, AWS, and more).

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

**Services:**
- **SaaS API**: http://localhost:8003 (expose this to your teams)
- **API Documentation**: http://localhost:8003/docs
- **Admin Panel**: http://localhost:3000 (admin dashboard)

## Documentation

For comprehensive guides, deployment instructions, and API references:

**[📖 Full Documentation](https://gittielabs.github.io/SaasLiteLLM/)**

- **[Getting Started](https://gittielabs.github.io/SaasLiteLLM/getting-started/introduction/)** - Introduction and concepts
- **[Deployment](https://gittielabs.github.io/SaasLiteLLM/deployment/local-development/)** - Local development and Railway deployment
- **[API Reference](https://gittielabs.github.io/SaasLiteLLM/api-reference/jobs/)** - Complete API documentation
- **[Examples](https://gittielabs.github.io/SaasLiteLLM/examples/full-chain/)** - Integration examples and patterns

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
- **Admin Panel**: http://localhost:3000 (admin dashboard)
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

## Configuration

### Adding New Models and Provider Credentials

Models and provider credentials are managed through the Admin Panel:

1. **Navigate to Provider Credentials** (http://localhost:3000/provider-credentials)
   - Add API keys for OpenAI, Anthropic, Gemini, or Fireworks
   - Credentials are encrypted before storage

2. **Navigate to Model Aliases** (http://localhost:3000/models)
   - Create model aliases with custom pricing
   - Set input/output costs per million tokens
   - Assign models to access groups for team-level permissions

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
│   - Model routing & pricing     │
│   - Direct provider integration │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   Admin Panel (Port 3000)       │  ← Management UI
│   - Provider credentials        │
│   - Model pricing overview      │
│   - Team & org management       │
│   - Usage analytics             │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   PostgreSQL Database           │
│   - jobs, llm_calls             │
│   - teams, organizations        │
│   - model_aliases               │
│   - provider_credentials        │
│   - job_cost_summaries          │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   LLM Provider APIs             │
│   OpenAI │ Anthropic │ Gemini   │
│   Fireworks │ (Direct calls)    │
└─────────────────────────────────┘
```

**Why This Architecture?**

1. **Direct Provider Integration** - No proxy layer, lower latency, full control
2. **Hidden Complexity** - Teams interact with your SaaS API, not provider APIs
3. **Job-Based Costs** - Track costs for business operations, not individual API calls
4. **Flexible Pricing** - Charge what you want, track actual costs internally
5. **Multi-Tenant** - Isolated teams with their own budgets and limits
6. **Cost Transparency** - Real provider costs vs customer pricing with detailed margins

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
└── docs/                          # Documentation source (MkDocs)
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up your development environment
- Coding standards and best practices
- Running tests and code quality checks
- Submitting pull requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project is built on [LiteLLM](https://github.com/BerriAI/litellm), an amazing open-source project that provides a unified interface to 100+ LLM providers. Special thanks to the LiteLLM team for their excellent work.

## Support

- **Documentation**: [https://gittielabs.github.io/SaasLiteLLM/](https://gittielabs.github.io/SaasLiteLLM/)
- **Issues**: [GitHub Issues](https://github.com/GittieLabs/SaasLiteLLM/issues)
- **LiteLLM Docs**: [https://docs.litellm.ai/](https://docs.litellm.ai/)

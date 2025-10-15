# Local Development

Run SaaS LiteLLM locally for development and testing.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Git

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/GittieLabs/SaasLiteLLM.git
cd SaasLiteLLM
```

### 2. Set Up Database

```bash
# Start PostgreSQL (if using Docker)
docker run --name saas-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=saas_llm_db \
  -p 5432:5432 \
  -d postgres:14

# Run migrations
PGPASSWORD=postgres psql -h localhost -U postgres -d saas_llm_db \
  -f scripts/migrations/001_initial_schema.sql
# Run all subsequent migrations...
```

### 3. Configure Environment

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/saas_llm_db

# LiteLLM Configuration
LITELLM_PROXY_BASE_URL=http://localhost:4000

# Master Key (for admin operations)
MASTER_KEY=sk-your-master-key-here

# OpenAI API Key (or other provider keys)
OPENAI_API_KEY=sk-your-openai-key
```

### 4. Install Dependencies

```bash
# Using pip
pip install -e .

# Or using uv (faster)
uv pip install -e .
```

### 5. Start Services

**Terminal 1: LiteLLM Proxy**
```bash
litellm --config litellm_config.yaml --port 4000
```

**Terminal 2: SaaS API**
```bash
python -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003 --reload
```

**Terminal 3: Admin Panel (optional)**
```bash
cd admin-panel
npm install
npm run dev
```

**Terminal 4: Documentation (optional)**
```bash
mkdocs serve --dev-addr 0.0.0.0:8004
```

## Verify Installation

### Test SaaS API

```bash
curl http://localhost:8003/health
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
curl -X POST http://localhost:8003/api/organizations/create \
  -H "Authorization: Bearer sk-your-master-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "test-org",
    "org_name": "Test Organization"
  }'
```

### Create Test Team

```bash
curl -X POST http://localhost:8003/api/teams/create \
  -H "Authorization: Bearer sk-your-master-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "test-team",
    "team_name": "Test Team",
    "org_id": "test-org",
    "credits": 1000
  }'
```

Response includes virtual key:
```json
{
  "team_id": "test-team",
  "virtual_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
  "credits": 1000
}
```

### Make Test LLM Call

```bash
# Save the virtual key from previous step
VIRTUAL_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# Create job
JOB_RESPONSE=$(curl -X POST http://localhost:8003/api/jobs/create \
  -H "Authorization: Bearer $VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "test-team",
    "job_type": "test"
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')

# Make LLM call
curl -X POST "http://localhost:8003/api/jobs/$JOB_ID/llm-call" \
  -H "Authorization: Bearer $VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Complete job
curl -X POST "http://localhost:8003/api/jobs/$JOB_ID/complete" \
  -H "Authorization: Bearer $VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

## Development Workflow

### Run Tests

```bash
# Unit tests
pytest tests/

# Integration tests
python scripts/test_full_integration.py
```

### Check Code Quality

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Format code
ruff format src/
```

### Database Migrations

Create new migration:

```bash
# Create file: scripts/migrations/XXX_description.sql
touch scripts/migrations/010_add_new_feature.sql

# Edit with SQL commands
# Run migration
./scripts/run_migrations.sh
```

### Hot Reload

The `--reload` flag enables automatic restart when code changes:
- Edit Python files in `src/`
- Save changes
- API automatically restarts

## Troubleshooting

### Database Connection Failed

**Problem:** `could not connect to database`

**Solutions:**
1. Check PostgreSQL is running: `docker ps` or `brew services list`
2. Verify credentials in `.env`
3. Check port 5432 is not in use: `lsof -i :5432`

### LiteLLM Proxy Not Reachable

**Problem:** `Connection refused to localhost:4000`

**Solutions:**
1. Start LiteLLM proxy: `litellm --config litellm_config.yaml --port 4000`
2. Check `LITELLM_PROXY_BASE_URL` in `.env`
3. Verify config file exists: `ls litellm_config.yaml`

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solutions:**
1. Install in editable mode: `pip install -e .`
2. Set PYTHONPATH: `export PYTHONPATH=/path/to/SaasLiteLLM`

### Port Already in Use

**Problem:** `Address already in use: port 8003`

**Solutions:**
```bash
# Find process using port
lsof -ti:8003

# Kill process
lsof -ti:8003 | xargs kill -9

# Or use different port
uvicorn src.saas_api:app --port 8005
```

## Next Steps

- **[Railway Deployment](railway.md)** - Deploy to production
- **[Environment Variables](environment-variables.md)** - Configure all settings
- **[Docker Setup](docker.md)** - Use Docker for development

# Quick Start Guide

## Initial Setup (First Time Only)

### 1. Install Dependencies

```bash
# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
./scripts/setup_local.sh
```

### 2. Start Docker Services

```bash
# Start PostgreSQL and Redis
./scripts/docker_setup.sh
```

### 3. Create Job Tracking Tables

```bash
# Run database migrations
./scripts/run_migrations.sh
```

You should see:
```
✅ Migration completed: 001_create_job_tracking_tables.sql
🎉 All migrations completed successfully!
```

### 4. Add Your API Keys

```bash
# Edit .env file
nano .env
```

Update these lines:
```bash
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
```

## Running the Services

### Terminal 1: Start LiteLLM Backend

```bash
source .venv/bin/activate
python scripts/start_local.py
```

**First time only:** LiteLLM will create its own tables automatically. You'll see:
```
🚀 Starting LiteLLM proxy server...
🌐 Server will be available at: http://0.0.0.0:8002
```

LiteLLM creates these tables:
- `LiteLLM_VerificationToken` (API keys)
- `LiteLLM_UserTable` (Users)
- `LiteLLM_TeamTable` (Teams)
- `LiteLLM_SpendLogs` (Usage tracking)
- And more...

### Terminal 2: Start SaaS API Wrapper

```bash
source .venv/bin/activate
python scripts/start_saas_api.py
```

You'll see:
```
🚀 Starting SaaS API wrapper service...
🌐 SaaS API will be available at: http://0.0.0.0:8003
```

## Verify Everything Works

### 1. Health Checks

```bash
# LiteLLM backend
curl http://localhost:8002/health

# SaaS API
curl http://localhost:8003/health
```

### 2. Check Database Tables

```bash
# Should show 5+ tables (your job tracking + LiteLLM's tables)
docker exec litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm -c "\dt"'
```

Expected output:
```
 public | job_cost_summaries           (yours)
 public | jobs                         (yours)
 public | llm_calls                    (yours)
 public | team_usage_summaries         (yours)
 public | webhook_registrations        (yours)
 public | LiteLLM_VerificationToken    (LiteLLM's)
 public | LiteLLM_UserTable            (LiteLLM's)
 public | LiteLLM_TeamTable            (LiteLLM's)
 ...
```

### 3. Create a Test Job

```bash
curl -X POST http://localhost:8003/api/jobs/create \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "test-team",
    "user_id": "test-user",
    "job_type": "test",
    "metadata": {"test": true}
  }'
```

You should get a response like:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-10-09T01:30:00.000Z"
}
```

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **SaaS API** | http://localhost:8003 | Your teams use this |
| **SaaS API Docs** | http://localhost:8003/docs | Interactive API docs |
| **LiteLLM Backend** | http://localhost:8002 | Internal only |
| **LiteLLM Admin UI** | http://localhost:8002/ui | Admin dashboard |
| **LiteLLM API Docs** | http://localhost:8002/docs | LiteLLM API reference |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6380 | Cache |

## Daily Usage

After initial setup, just run:

```bash
# Terminal 1
source .venv/bin/activate && python scripts/start_local.py

# Terminal 2
source .venv/bin/activate && python scripts/start_saas_api.py
```

## Common Commands

### Restart Database (Fresh Start)

```bash
# Stop and remove all data
docker compose down -v

# Start fresh
docker compose up -d postgres redis

# Wait for PostgreSQL to initialize
sleep 10

# Re-create job tracking tables
./scripts/run_migrations.sh

# Start services (LiteLLM will recreate its tables)
source .venv/bin/activate
python scripts/start_local.py
```

### View Database

```bash
# Connect to PostgreSQL
docker exec -it litellm-postgres psql -U litellm_user -d litellm

# Useful commands inside psql:
\dt              # List all tables
\d jobs          # Describe jobs table
SELECT * FROM jobs LIMIT 5;  # Query jobs
\q               # Quit
```

### View Logs

```bash
# PostgreSQL logs
docker compose logs -f postgres

# Redis logs
docker compose logs -f redis
```

### Stop Everything

```bash
# Stop Docker services
docker compose down

# Or stop with data removal
docker compose down -v
```

## Troubleshooting

### "Port already in use"

Ports 8002 or 8003 are already taken:

```bash
# Find what's using the port
lsof -i :8002
lsof -i :8003

# Kill the process or change ports in .env
```

### "Database connection failed"

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Restart it
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### "Tables not found"

```bash
# Re-run migrations
./scripts/run_migrations.sh

# Or manually
docker exec -i litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm' < scripts/migrations/001_create_job_tracking_tables.sql
```

### Migration script not executable

```bash
chmod +x scripts/run_migrations.sh
chmod +x scripts/docker_setup.sh
```

### Python import errors

```bash
# Reinstall dependencies
source .venv/bin/activate
uv pip install -e .
```

## File Structure

```
SaasLiteLLM/
├── .env                           # Local environment config (ports 8002/8003)
├── .env.local                     # Template for local dev
├── .env.example                   # Template for Railway
│
├── scripts/
│   ├── docker_setup.sh           # Start Docker services
│   ├── run_migrations.sh         # Run database migrations
│   ├── start_local.py            # Start LiteLLM backend (8002)
│   ├── start_saas_api.py         # Start SaaS API (8003)
│   └── migrations/
│       └── 001_create_job_tracking_tables.sql
│
├── src/
│   ├── main.py                   # LiteLLM proxy entry point
│   ├── saas_api.py               # SaaS API wrapper
│   ├── config/
│   │   ├── settings.py           # Environment configuration
│   │   └── litellm_config.yaml   # Models, Redis, teams
│   └── models/
│       └── job_tracking.py       # Database models
│
├── docker-compose.yml            # PostgreSQL + Redis
├── Dockerfile                    # Railway deployment
│
├── QUICKSTART.md                 # This file
├── DATABASE_SETUP.md             # Database details
├── ARCHITECTURE.md               # System design
├── USAGE_EXAMPLES.md             # API examples
└── PORT_CONFIG.md                # Port configuration
```

## Next Steps

1. ✅ Services running? Test with health checks above
2. ✅ Database tables created? Check with `\dt` command
3. 📖 Learn the API: Open http://localhost:8003/docs
4. 📚 See examples: Read [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
5. 🏗️ Understand design: Read [ARCHITECTURE.md](ARCHITECTURE.md)

## Support

- **Database issues**: See [DATABASE_SETUP.md](DATABASE_SETUP.md)
- **Port conflicts**: See [PORT_CONFIG.md](PORT_CONFIG.md)
- **API usage**: See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)

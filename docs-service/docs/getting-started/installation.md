# Installation

Complete installation guide for SaaS LiteLLM, covering local development setup and all configuration options.

## System Requirements

### Required Software

- **Python 3.9+** - Programming language runtime
- **Docker** - Container platform for PostgreSQL and Redis
- **Docker Compose** - Multi-container orchestration
- **Git** - Version control (for cloning the repository)
- **uv** - Fast Python package installer (installed during setup)

### Recommended

- **PostgreSQL client** (psql) - For database inspection
- **Redis client** (redis-cli) - For cache inspection

### Hardware

- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **CPU**: 2+ cores recommended

## Installation Methods

Choose the installation method that best fits your needs:

=== "Local Development (Recommended)"

    Full development setup with all services running locally via Docker.

    **Best for:**
    - Development and testing
    - Learning the platform
    - Contributing to the project

=== "Docker Only"

    Run everything in Docker containers.

    **Best for:**
    - Production deployments
    - Isolated environments
    - CI/CD pipelines

=== "Railway Deployment"

    Deploy to Railway cloud platform.

    **Best for:**
    - Production hosting
    - Quick deployments
    - Managed infrastructure

## Local Development Setup

### Step 1: Clone or Access Repository

If you have access to the repository:

```bash
cd /path/to/your/SaasLiteLLM
```

### Step 2: Install Python Dependencies

Install `uv` package manager and project dependencies:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell to get uv in PATH
source ~/.bashrc  # or ~/.zshrc

# Run setup script (creates venv and installs dependencies)
./scripts/setup_local.sh
```

This script will:
- Create a Python virtual environment in `.venv/`
- Install all required dependencies
- Set up the project for development

**Manual installation (alternative):**

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Step 3: Start Docker Services

Start PostgreSQL and Redis containers:

```bash
./scripts/docker_setup.sh
```

This will:
- Pull PostgreSQL 15 and Redis 7 images
- Create and start containers
- Initialize PostgreSQL with the correct database

**Verify Docker services:**

```bash
docker compose ps
```

Expected output:
```
NAME                  STATUS
litellm-postgres      Up
litellm-redis         Up
```

### Step 4: Configure Environment Variables

Copy the local environment template:

```bash
cp .env.local .env
```

Edit `.env` and add your API keys:

```bash
# Required: OpenAI API key
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Optional: Other providers
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-google-key-here
```

**Environment file locations:**
- `.env` - Your actual environment (not in git)
- `.env.local` - Template for local development
- `.env.example` - Template for Railway deployment

### Step 5: Run Database Migrations

Create the job tracking tables:

```bash
./scripts/run_migrations.sh
```

Expected output:
```
✅ Migration completed: 001_create_job_tracking_tables.sql
✅ Migration completed: 002_add_teams_table.sql
✅ Migration completed: 003_add_organizations.sql
...
🎉 All migrations completed successfully!
```

**Manual migration (alternative):**

```bash
for file in scripts/migrations/*.sql; do
    docker exec -i litellm-postgres sh -c \
        'PGPASSWORD=litellm_password psql -U litellm_user -d litellm' < "$file"
    echo "✅ Migration completed: $(basename $file)"
done
```

### Step 6: Start the Services

You'll need **two terminal windows**.

**Terminal 1: LiteLLM Backend**

```bash
source .venv/bin/activate
python scripts/start_local.py
```

Wait for:
```
🚀 Starting LiteLLM proxy server...
🌐 Server will be available at: http://0.0.0.0:8002
```

**Terminal 2: SaaS API**

```bash
source .venv/bin/activate
python scripts/start_saas_api.py
```

Wait for:
```
🚀 Starting SaaS API wrapper service...
🌐 SaaS API will be available at: http://0.0.0.0:8003
```

### Step 7: Verify Installation

Check that all services are running:

```bash
# Check LiteLLM backend
curl http://localhost:8002/health

# Check SaaS API
curl http://localhost:8003/health

# Check PostgreSQL
docker exec litellm-postgres pg_isready -U litellm_user

# Check Redis
docker exec litellm-redis redis-cli ping
```

All should return successful responses.

## Database Setup

### PostgreSQL Configuration

The Docker setup creates a PostgreSQL database with these settings:

| Setting | Value |
|---------|-------|
| Host | localhost |
| Port | 5432 |
| Database | litellm |
| User | litellm_user |
| Password | litellm_password |

### Connecting to PostgreSQL

```bash
# Using Docker exec
docker exec -it litellm-postgres psql -U litellm_user -d litellm

# Using local psql client
PGPASSWORD=litellm_password psql -h localhost -U litellm_user -d litellm
```

**Useful psql commands:**

```sql
\dt                  -- List all tables
\d table_name        -- Describe a table
\l                   -- List databases
\du                  -- List users
\q                   -- Quit
```

### Database Tables

After migrations, you'll have these tables:

**Your SaaS Tables:**
- `jobs` - Job tracking
- `llm_calls` - Individual LLM call records
- `job_cost_summaries` - Aggregated costs
- `organizations` - Organization management
- `teams` - Team management
- `model_access_groups` - Model access control
- `model_aliases` - Model configuration
- `credit_transactions` - Credit history

**LiteLLM Tables** (auto-created):
- `LiteLLM_VerificationToken` - API keys
- `LiteLLM_UserTable` - Users
- `LiteLLM_TeamTable` - Teams
- `LiteLLM_SpendLogs` - Usage tracking

### Inspecting Data

```bash
# View recent jobs
docker exec -it litellm-postgres psql -U litellm_user -d litellm \
    -c "SELECT job_id, team_id, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;"

# View teams
docker exec -it litellm-postgres psql -U litellm_user -d litellm \
    -c "SELECT team_id, organization_id, credits_allocated, credits_remaining FROM teams;"
```

## Redis Setup

### Redis Configuration

| Setting | Value |
|---------|-------|
| Host | localhost |
| Port | 6380 (non-standard to avoid conflicts) |
| Password | None |

### Connecting to Redis

```bash
# Using Docker exec
docker exec -it litellm-redis redis-cli

# Using local redis-cli
redis-cli -p 6380
```

**Useful Redis commands:**

```
PING                 -- Test connection
KEYS *               -- List all keys (dev only!)
GET key_name         -- Get a value
FLUSHALL             -- Clear all data (use with caution!)
INFO                 -- Server information
QUIT                 -- Exit
```

## Port Configuration

Default ports for local development:

| Service | Port | URL |
|---------|------|-----|
| SaaS API | 8003 | http://localhost:8003 |
| SaaS API Docs | 8003 | http://localhost:8003/docs |
| LiteLLM Proxy | 8002 | http://localhost:8002 |
| LiteLLM Admin UI | 8002 | http://localhost:8002/ui |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6380 | localhost:6380 |
| Admin Dashboard | 3002 | http://localhost:3002 |

!!! info "Why non-standard ports?"
    We use ports 8002/8003 locally to avoid conflicts with other services. In production (Railway), standard port 8000 is used.

## Optional: Admin Dashboard

If you want to use the Next.js admin dashboard:

```bash
cd admin-dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

Access at: http://localhost:3002

## Troubleshooting

### "uv: command not found"

Install uv manually:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc
```

### "Port already in use"

Find and kill the process:

```bash
# Find what's using the port
lsof -i :8003

# Kill it
kill -9 <PID>
```

### "Docker daemon not running"

Start Docker Desktop or the Docker daemon:

```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

### "PostgreSQL connection refused"

Check PostgreSQL is running:

```bash
docker compose ps postgres
docker compose logs postgres

# Restart if needed
docker compose restart postgres
```

### "Module not found" errors

Reinstall dependencies:

```bash
source .venv/bin/activate
uv pip install -e .
```

### "Migration already exists"

Migrations are idempotent. If you need to reset:

```bash
# Remove all data
docker compose down -v

# Start fresh
docker compose up -d postgres redis
sleep 10
./scripts/run_migrations.sh
```

## Common Operations

### Restart Everything

```bash
# Stop Docker services
docker compose down

# Start Docker services
docker compose up -d

# Restart Python services (Ctrl+C in each terminal, then restart)
```

### View Logs

```bash
# PostgreSQL logs
docker compose logs -f postgres

# Redis logs
docker compose logs -f redis

# SaaS API logs (if redirected to file)
tail -f logs/saas_api.log
```

### Reset Database

```bash
# Complete reset
docker compose down -v
docker compose up -d
sleep 10
./scripts/run_migrations.sh
```

### Update Dependencies

```bash
source .venv/bin/activate
uv pip install -e . --upgrade
```

## Development Tools

### pgAdmin (Optional)

Web-based PostgreSQL management:

```bash
docker compose --profile pgadmin up -d
```

Access at: http://localhost:5050
- Email: admin@litellm.local
- Password: admin

### Redis Commander (Optional)

Add to `docker-compose.yml` if needed for Redis visualization.

## Next Steps

Now that installation is complete:

1. **[Follow the Quickstart](quickstart.md)** - Test your installation
2. **[Learn the Architecture](architecture.md)** - Understand the system
3. **[Integration Guide](../integration/overview.md)** - Start building
4. **[Set up Admin Dashboard](../admin-dashboard/overview.md)** - Manage teams

## Additional Resources

- **[Troubleshooting Guide](../testing/troubleshooting.md)** - Common issues
- **[Environment Variables](../deployment/environment-variables.md)** - Configuration reference
- **[Docker Guide](../deployment/docker.md)** - Docker deployment details

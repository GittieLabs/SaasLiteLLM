# Quickstart Guide

Get SaaS LiteLLM running on your local machine in **5 minutes**. This guide will walk you through the complete setup process.

## Prerequisites

Before you begin, make sure you have:

- **Python 3.9+** installed
- **Docker** and **Docker Compose** installed
- **Git** installed
- An **OpenAI API key** (or other LLM provider key)

## Step 1: Access the Repository

Navigate to your SaasLiteLLM project directory:

```bash
cd SaasLiteLLM
```

## Step 2: Install Dependencies

We use `uv` as our package manager for faster installs:

```bash
# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
./scripts/setup_local.sh
```

!!! tip "What does setup_local.sh do?"
    - Creates a Python virtual environment in `.venv/`
    - Installs all required dependencies using `uv`
    - Sets up the project for local development

## Step 3: Start Docker Services

Start PostgreSQL and Redis using Docker Compose:

```bash
./scripts/docker_setup.sh
```

This will start:
- **PostgreSQL 15** on port 5432
- **Redis 7** on port 6380

Wait a few seconds for the services to initialize.

## Step 4: Create Database Tables

Run the database migrations to create the job tracking tables:

```bash
./scripts/run_migrations.sh
```

You should see:
```
✅ Migration completed: 001_create_job_tracking_tables.sql
✅ Migration completed: 002_add_teams_table.sql
...
🎉 All migrations completed successfully!
```

!!! info "What tables are created?"
    - `jobs` - Job tracking
    - `llm_calls` - Individual LLM call records
    - `job_cost_summaries` - Aggregated costs per job
    - `team_usage_summaries` - Team usage analytics
    - `organizations` - Organization management
    - `teams` - Team management
    - `model_access_groups` - Model access control
    - `model_aliases` - Model configuration

## Step 5: Configure API Keys

Create a `.env` file from the template:

```bash
cp .env.local .env
```

Edit the `.env` file and add your API keys:

```bash
nano .env
```

Update these lines with your actual keys:

```bash
# Required
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Optional (add if you want to use these providers)
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here
```

!!! warning "Keep your API keys secure"
    Never commit your `.env` file to git. It's already in `.gitignore`.

## Step 6: Start the Services

You'll need **two terminal windows** to run the services.

### Terminal 1: Start LiteLLM Backend

```bash
source .venv/bin/activate
python scripts/start_local.py
```

You should see:
```
🚀 Starting LiteLLM proxy server...
🌐 Server will be available at: http://0.0.0.0:8002
```

!!! info "First time only"
    LiteLLM will automatically create its own tables in PostgreSQL on first run. This is normal and expected.

### Terminal 2: Start SaaS API

Open a **new terminal** and run:

```bash
source .venv/bin/activate
python scripts/start_saas_api.py
```

You should see:
```
🚀 Starting SaaS API wrapper service...
🌐 SaaS API will be available at: http://0.0.0.0:8003
```

## Step 7: Verify Everything Works

### Health Checks

In a new terminal, check that both services are running:

=== "SaaS API"

    ```bash
    curl http://localhost:8003/health
    ```

    Expected response:
    ```json
    {"status": "healthy"}
    ```

=== "LiteLLM Backend"

    ```bash
    curl http://localhost:8002/health
    ```

    Expected response:
    ```json
    {"status": "healthy"}
    ```

### Check Database Tables

Verify that all tables were created:

```bash
docker exec litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm -c "\dt"'
```

You should see both your tables and LiteLLM's tables:

```
 public | jobs                          (your tables)
 public | llm_calls
 public | organizations
 public | teams
 public | model_access_groups
 public | model_aliases
 public | LiteLLM_VerificationToken    (LiteLLM's tables)
 public | LiteLLM_TeamTable
 ...
```

### Create a Test Job

Let's create a simple test job to verify the API is working:

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

Expected response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-10-09T01:30:00.000Z"
}
```

!!! success "Congratulations!"
    If you got this response, everything is working correctly!

## Access Points

Here are all the URLs you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **SaaS API** | http://localhost:8003 | Main API for your teams |
| **SaaS API Docs** | http://localhost:8003/docs | Interactive Swagger UI |
| **SaaS API ReDoc** | http://localhost:8003/redoc | Beautiful API documentation |
| **LiteLLM Backend** | http://localhost:8002 | Internal only (admin) |
| **LiteLLM Admin UI** | http://localhost:8002/ui | Admin dashboard |
| **LiteLLM API Docs** | http://localhost:8002/docs | LiteLLM API reference |
| **PostgreSQL** | localhost:5432 | Database (litellm_user/litellm_password) |
| **Redis** | localhost:6380 | Cache |

## Daily Usage

After the initial setup, you only need to start the services:

```bash
# Terminal 1: LiteLLM Backend
source .venv/bin/activate && python scripts/start_local.py

# Terminal 2: SaaS API
source .venv/bin/activate && python scripts/start_saas_api.py
```

!!! tip "Faster startup"
    You can create shell aliases to make this even faster:
    ```bash
    alias start-litellm="cd /path/to/SaasLiteLLM && source .venv/bin/activate && python scripts/start_local.py"
    alias start-saas="cd /path/to/SaasLiteLLM && source .venv/bin/activate && python scripts/start_saas_api.py"
    ```

## Troubleshooting

### Port Already in Use

If you see "Address already in use" errors:

```bash
# Find what's using the port
lsof -i :8002
lsof -i :8003

# Kill the process
kill -9 <PID>
```

### Database Connection Failed

If services can't connect to PostgreSQL:

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres

# View logs
docker compose logs postgres
```

### Tables Not Found

If you see "relation does not exist" errors:

```bash
# Re-run migrations
./scripts/run_migrations.sh
```

### Migration Script Not Executable

If you get "Permission denied" errors:

```bash
chmod +x scripts/run_migrations.sh
chmod +x scripts/docker_setup.sh
chmod +x scripts/setup_local.sh
```

### Python Import Errors

If you see import errors:

```bash
# Reinstall dependencies
source .venv/bin/activate
uv pip install -e .
```

## Common Commands

### Restart Database (Fresh Start)

To completely reset the database:

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

Connect to PostgreSQL to inspect data:

```bash
# Connect to PostgreSQL
docker exec -it litellm-postgres psql -U litellm_user -d litellm
```

Useful commands inside `psql`:
```sql
\dt                           -- List all tables
\d jobs                       -- Describe jobs table
SELECT * FROM jobs LIMIT 5;   -- Query jobs
SELECT * FROM llm_calls;      -- Query LLM calls
\q                            -- Quit
```

### View Logs

Monitor service logs:

```bash
# PostgreSQL logs
docker compose logs -f postgres

# Redis logs
docker compose logs -f redis
```

### Stop Everything

```bash
# Stop Docker services (keeps data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## Next Steps

Now that you have SaaS LiteLLM running, here's what to do next:

1. **[Set up the Admin Dashboard](../admin-dashboard/overview.md)** - Create organizations and teams
2. **[Learn the Integration Workflow](../integration/overview.md)** - Understand how to use the API
3. **[Try the Examples](../examples/basic-usage.md)** - Run working code examples
4. **[Explore the API](http://localhost:8003/docs)** - Interactive API documentation

## Getting Help

If you encounter issues:

- Check the [Troubleshooting Guide](../testing/troubleshooting.md)
- Review [Common Errors](../integration/error-handling.md)

## Optional: Admin Dashboard

If you want to use the Next.js admin dashboard:

```bash
cd admin-dashboard
npm install
npm run dev
```

The dashboard will be available at http://localhost:3002

See the [Admin Dashboard Guide](../admin-dashboard/overview.md) for more details.

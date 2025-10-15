# Database Setup Complete ✅

## What Was Done

1. **Deleted old PostgreSQL instance** - Removed containers and volumes
2. **Created fresh PostgreSQL instance** - Clean database with proper initialization
3. **Created job tracking tables** - All 5 tables for SaaS job tracking
4. **Created migration system** - SQL files for reproducible setup

## Database Tables Created

| Table | Purpose |
|-------|---------|
| **jobs** | Main job tracking (business operations) |
| **llm_calls** | Individual LLM API calls per job |
| **job_cost_summaries** | Aggregated costs per job |
| **team_usage_summaries** | Team-level analytics by period |
| **webhook_registrations** | Webhook configurations for events |

## Database Connection

**Connection String:**
```
postgresql://litellm_user:litellm_password@127.0.0.1:5432/litellm
```

**Docker Access:**
```bash
docker exec -it litellm-postgres psql -U litellm_user -d litellm
```

## Migration Files

Location: `scripts/migrations/`

### Current Migrations:
- `001_create_job_tracking_tables.sql` - Creates all job tracking tables

### Running Migrations:
```bash
# Run all migrations
./scripts/run_migrations.sh

# Or manually:
docker exec -i litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm' < scripts/migrations/001_create_job_tracking_tables.sql
```

## Table Schemas

### jobs
```sql
job_id UUID PRIMARY KEY
team_id VARCHAR(255) NOT NULL
user_id VARCHAR(255)
job_type VARCHAR(100) NOT NULL
status job_status (pending|in_progress|completed|failed|cancelled)
created_at TIMESTAMP
started_at TIMESTAMP
completed_at TIMESTAMP
job_metadata JSONB
error_message VARCHAR(1000)
```

### llm_calls
```sql
call_id UUID PRIMARY KEY
job_id UUID REFERENCES jobs
litellm_request_id VARCHAR(255) UNIQUE
model_used VARCHAR(100)
prompt_tokens INTEGER
completion_tokens INTEGER
total_tokens INTEGER
cost_usd NUMERIC(10,6)
latency_ms INTEGER
created_at TIMESTAMP
purpose VARCHAR(200)
request_data JSONB
response_data JSONB
error VARCHAR(1000)
```

### job_cost_summaries
```sql
job_id UUID PRIMARY KEY REFERENCES jobs
total_calls INTEGER
successful_calls INTEGER
failed_calls INTEGER
total_prompt_tokens INTEGER
total_completion_tokens INTEGER
total_tokens INTEGER
total_cost_usd NUMERIC(12,6)
avg_latency_ms INTEGER
total_duration_seconds INTEGER
calculated_at TIMESTAMP
```

### team_usage_summaries
```sql
id UUID PRIMARY KEY
team_id VARCHAR(255)
period VARCHAR(50)
period_type VARCHAR(20)
total_jobs INTEGER
successful_jobs INTEGER
failed_jobs INTEGER
cancelled_jobs INTEGER
total_cost_usd NUMERIC(12,2)
total_tokens INTEGER
job_type_breakdown JSONB
calculated_at TIMESTAMP
```

### webhook_registrations
```sql
webhook_id UUID PRIMARY KEY
team_id VARCHAR(255)
webhook_url VARCHAR(500)
events JSONB
is_active INTEGER
created_at TIMESTAMP
last_triggered_at TIMESTAMP
auth_header VARCHAR(500)
```

## Verify Setup

```bash
# List all tables
docker exec litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm -c "\dt"'

# Show jobs table structure
docker exec litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm -c "\d jobs"'

# Count records (should be 0 initially)
docker exec litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm -c "SELECT COUNT(*) FROM jobs;"'
```

## Reset Database (If Needed)

```bash
# Stop and remove all data
docker compose down -v

# Start fresh
docker compose up -d postgres redis

# Wait for initialization
sleep 10

# Run migrations
./scripts/run_migrations.sh
```

## Next Steps

1. **Start LiteLLM backend:**
   ```bash
   source .venv/bin/activate
   python scripts/start_local.py
   ```

2. **Start SaaS API:**
   ```bash
   # In another terminal
   source .venv/bin/activate
   python scripts/start_saas_api.py
   ```

3. **Test the setup:**
   ```bash
   # Health checks
   curl http://localhost:8002/health  # LiteLLM
   curl http://localhost:8003/health  # SaaS API

   # Create a test job
   curl -X POST http://localhost:8003/api/jobs/create \
     -H "Content-Type: application/json" \
     -d '{"team_id": "test", "job_type": "test"}'
   ```

## Troubleshooting

### Can't connect to database
```bash
# Check if container is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart
docker compose restart postgres
```

### Tables not found
```bash
# Re-run migrations
./scripts/run_migrations.sh
```

### Port conflicts
The database runs on port 5432. If you have another PostgreSQL instance running, modify `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Use different host port
```

Then update `.env`:
```bash
DATABASE_URL=postgresql://litellm_user:litellm_password@127.0.0.1:5433/litellm
```

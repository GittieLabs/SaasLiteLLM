# Testing Guide - Minimal Version

This guide will walk you through testing the minimal version of the SaaS LiteLLM platform with model groups, organizations, teams, and credits.

## Overview

The minimal version includes:

- **Organizations**: Multi-tenant hierarchy
- **Model Groups**: Named groups of models (ResumeAgent, ParsingAgent, etc.)
- **Teams**: Teams belong to organizations and have assigned model groups
- **Credits**: Credit-based billing system (1 job = 1 credit)
- **API Endpoints**: RESTful API for all CRUD operations

## Prerequisites

1. Docker and Docker Compose installed
2. Python 3.11+ with dependencies installed
3. `.env` file configured with database credentials

## Step 1: Start Docker Services

Start the PostgreSQL database and LiteLLM proxy:

```bash
docker compose up -d
```

Verify containers are running:

```bash
docker compose ps
```

You should see:
- `litellm-postgres` (PostgreSQL database)
- `litellm-proxy` (LiteLLM proxy server)

## Step 2: Run Database Migrations

Execute all database migrations to create the necessary tables:

```bash
./scripts/run_migrations.sh
```

This will create:
- `jobs` - Main job tracking table (extended with new fields)
- `llm_calls` - Individual LLM call records (extended with model group tracking)
- `organizations` - Organization/tenant management
- `model_groups` - Named model group definitions
- `model_group_models` - Models within each group (with priority)
- `team_model_groups` - Junction table for team-model group assignments
- `team_credits` - Credit balances per team
- `credit_transactions` - Credit transaction audit log

Expected output:
```
 Migration completed: 001_create_job_tracking_tables.sql
 Migration completed: 002_create_organizations.sql
 Migration completed: 003_create_model_groups.sql
 Migration completed: 004_create_team_model_groups.sql
 Migration completed: 005_create_credits_tables.sql
 Migration completed: 006_extend_jobs_and_llm_calls.sql

<‰ All migrations completed successfully!
```

## Step 3: Start the SaaS API

In a new terminal window, start the SaaS API server:

```bash
python scripts/start_saas_api.py
```

Or run directly with uvicorn:

```bash
python -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003 --reload
```

The API will be available at:
- **Base URL**: http://localhost:8003
- **API Docs**: http://localhost:8003/docs (Swagger UI)
- **Health Check**: http://localhost:8003/health

## Step 4: Run the Test Script

In another terminal window, run the automated test script:

```bash
python scripts/test_minimal_version.py
```

### What the Test Script Does

The script tests all core functionality in sequence:

1. **Health Check** - Verifies API is running
2. **Create Organization** - Creates "org_test_001" (Test Organization)
3. **Create Model Groups**:
   - `ResumeAgent` - Resume analysis with gpt-4-turbo (primary), gpt-3.5-turbo (fallback)
   - `ParsingAgent` - Document parsing with gpt-3.5-turbo
   - `RAGAgent` - RAG operations with gpt-4-turbo-preview
4. **Create Team** - Creates "team_test_hr" with all model groups and 100 credits
5. **Check Credits** - Retrieves team credit balance
6. **Add Credits** - Adds 50 more credits to the team
7. **Get Model Group** - Retrieves ResumeAgent details
8. **Get Team Details** - Retrieves full team information

### Expected Output

```
############################################################
#  MINIMAL VERSION TEST SUITE
#  Testing Model Groups, Organizations, Teams & Credits
#  Base URL: http://localhost:8003
############################################################

============================================================
  1. Health Check
============================================================

Status: 200
Response: {'status': 'healthy', 'service': 'saas-llm-api'}
 Health check passed

============================================================
  2. Create Organization
============================================================

Status: 200
Response: {
  "organization_id": "org_test_001",
  "name": "Test Organization",
  ...
}
 Organization created

[... more test output ...]

============================================================
  TEST SUMMARY
============================================================

 All tests passed!

Next steps:
1. Run migrations: ./scripts/run_migrations.sh
2. Check API docs: http://localhost:8003/docs
3. Test model resolution and credit deduction with actual jobs
```

## Step 5: Explore the API

### Interactive API Documentation

Open your browser to http://localhost:8003/docs to explore the full API using Swagger UI.

### Key API Endpoints

#### Organizations
- `POST /api/organizations/create` - Create organization
- `GET /api/organizations/{org_id}` - Get organization details
- `PUT /api/organizations/{org_id}` - Update organization
- `GET /api/organizations` - List all organizations

#### Model Groups
- `POST /api/model-groups/create` - Create model group
- `GET /api/model-groups` - List all model groups
- `GET /api/model-groups/{group_name}` - Get model group details
- `PUT /api/model-groups/{group_name}/models` - Update models in group
- `DELETE /api/model-groups/{group_name}` - Delete model group

#### Teams
- `POST /api/teams/create` - Create team with model groups and credits
- `GET /api/teams/{team_id}` - Get team details
- `PUT /api/teams/{team_id}/model-groups` - Assign/update model groups

#### Credits
- `GET /api/credits/teams/{team_id}/balance` - Get credit balance
- `POST /api/credits/teams/{team_id}/add` - Add credits
- `GET /api/credits/teams/{team_id}/transactions` - Get transaction history
- `POST /api/credits/teams/{team_id}/check` - Check if team has sufficient credits

#### Jobs (Original API - Still Available)
- `POST /api/jobs/create` - Create new job
- `POST /api/jobs/{job_id}/llm-call` - Make LLM call within job
- `POST /api/jobs/{job_id}/complete` - Complete job and calculate costs
- `GET /api/jobs/{job_id}` - Get job details
- `GET /api/jobs/{job_id}/costs` - Get job cost breakdown
- `GET /api/teams/{team_id}/jobs` - List team's jobs
- `GET /api/teams/{team_id}/usage` - Get team usage summary

## Manual Testing Examples

### Create a Model Group

```bash
curl -X POST http://localhost:8003/api/model-groups/create \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "SummaryAgent",
    "display_name": "Document Summary Agent",
    "description": "Generates executive summaries",
    "models": [
      {"model_name": "gpt-4-turbo", "priority": 0},
      {"model_name": "gpt-3.5-turbo", "priority": 1}
    ]
  }'
```

### Create an Organization

```bash
curl -X POST http://localhost:8003/api/organizations/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme_corp",
    "name": "ACME Corporation",
    "metadata": {"plan": "enterprise"}
  }'
```

### Create a Team

```bash
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme_corp",
    "team_id": "team_engineering",
    "team_alias": "Engineering Team",
    "model_groups": ["ResumeAgent", "ParsingAgent"],
    "credits_allocated": 500,
    "metadata": {"department": "Engineering"}
  }'
```

### Check Credit Balance

```bash
curl http://localhost:8003/api/credits/teams/team_engineering/balance
```

### Add Credits

```bash
curl -X POST http://localhost:8003/api/credits/teams/team_engineering/add \
  -H "Content-Type: application/json" \
  -d '{
    "credits": 100,
    "reason": "Monthly allocation"
  }'
```

## Troubleshooting

### API Not Starting

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Run from project root:
```bash
cd /Users/keithelliott/repos/SaasLiteLLM
python -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003
```

### Database Connection Failed

**Error**: `Connection refused` or `could not connect to server`

**Solution**:
1. Verify Docker containers are running: `docker compose ps`
2. Check DATABASE_URL in `.env` file
3. Restart containers: `docker compose restart`

### Migration Failed

**Error**: `relation already exists`

**Solution**: This is usually OK - it means the table was already created. The migrations use `CREATE TABLE IF NOT EXISTS`.

To reset and re-run migrations:
```bash
# Drop all tables (WARNING: destroys all data)
docker exec -i litellm-postgres sh -c 'PGPASSWORD=litellm_password psql -U litellm_user -d litellm -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"'

# Re-run migrations
./scripts/run_migrations.sh
```

### Test Script Connection Error

**Error**: `Connection Error: Could not connect to http://localhost:8003`

**Solution**: Make sure the SaaS API is running:
```bash
python scripts/start_saas_api.py
```

## Architecture Overview

```
                                                             
                     Your SaaS Application                    
                        ,                                    
                          HTTP API Calls
                         “
                                                             
                  SaaS LiteLLM API (Port 8003)               
                                                           
    Endpoints:                                             
    " Organizations API                                    
    " Model Groups API                                     
    " Teams API                                            
    " Credits API                                          
    " Jobs API (with model group resolution)              
                                                           
                                                           
    Services:                                              
    " ModelResolver - Resolves model groups to models      
    " CreditManager - Manages credit transactions          
                                                           
                        ,                                    
                          Proxied LLM Calls
                         “
                                                             
              LiteLLM Proxy (Port 8000/8002)                 
  " Routes calls to OpenAI, Anthropic, etc.                  
  " Handles authentication, rate limiting, caching           
  " Tracks token usage and costs                             
                                                             
```

## Database Schema

### Core Tables

- **organizations** - Top-level tenant/organization management
- **model_groups** - Named groups of models (e.g., "ResumeAgent")
- **model_group_models** - Models within each group with priority
- **team_model_groups** - Junction table for team access to model groups
- **team_credits** - Credit balances (with computed `credits_remaining` field)
- **credit_transactions** - Audit log of all credit changes
- **jobs** - Extended with `organization_id`, `external_task_id`, `model_groups_used[]`
- **llm_calls** - Extended with `model_group_used`, `resolved_model`

### Key Relationships

```
organizations (1)   ’ (N) team_credits
model_groups (1)   ’ (N) model_group_models
team_credits (N)   ’ (N) model_groups (via team_model_groups)
team_credits (1)   ’ (N) credit_transactions
team_credits (1)   ’ (N) jobs
jobs (1)   ’ (N) llm_calls
```

## Next Steps

This minimal version provides the foundation. To complete the full implementation:

1. **Integrate Model Resolution**: Update `/api/jobs/{job_id}/llm-call` to:
   - Accept `model_group_name` instead of hardcoded model
   - Use `ModelResolver` to get primary + fallback models
   - Store `model_group_used` and `resolved_model` in LLMCall records

2. **Add Credit Deduction**: Update `/api/jobs/{job_id}/complete` to:
   - Check if team has credits
   - Deduct 1 credit for successful jobs
   - Mark job with `credit_applied=True`
   - Update `model_groups_used[]` array

3. **LiteLLM Virtual Keys**: Generate team-specific virtual keys in LiteLLM:
   - Create virtual key when team is created
   - Store key reference in team metadata
   - Use team key for all LLM calls

4. **Enhanced Error Handling**:
   - Implement fallback model retry logic
   - Handle insufficient credits gracefully
   - Add webhook notifications for job events

5. **Deploy to Railway**:
   - Push Docker images to GHCR
   - Configure Railway environment variables
   - Set up automatic deployments

## Support

For issues or questions:
- Check logs: `docker compose logs -f`
- View API docs: http://localhost:8003/docs
- Check database: `docker exec -it litellm-postgres psql -U litellm_user -d litellm`

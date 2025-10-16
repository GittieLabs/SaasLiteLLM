# Integration Test Guide

## Overview

This guide explains the complete integration test that validates the SaaS LiteLLM API works correctly with LiteLLM proxy and the admin dashboard.

## Test Components

### 1. **Database Clean Slate**
Start with a completely empty database to ensure reproducible results.

### 2. **Test Script** (`scripts/test_full_integration.py`)
Creates a complete team setup and validates all integrations.

### 3. **Admin Dashboard** (http://localhost:3002)
Visual interface to monitor and manage the created resources.

## Test Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CREATE ORGANIZATION                                       │
│    POST /api/organizations/create                            │
│    ├─ organization_id: org_demo_001                         │
│    └─ name: Demo Organization                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CREATE MODEL GROUPS                                       │
│    POST /api/model-groups/create (x2)                       │
│    ├─ ChatAgent (gpt-3.5-turbo, gpt-4)                     │
│    └─ AnalysisAgent (gpt-4)                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CREATE TEAM WITH LITELLM INTEGRATION                     │
│    POST /api/teams/create                                    │
│    ├─ Creates team in LiteLLM proxy                         │
│    ├─ Generates virtual API key                             │
│    ├─ Assigns model groups (ChatAgent, AnalysisAgent)       │
│    └─ Allocates 100 credits                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. VERIFY TEAM IN DATABASE                                  │
│    GET /api/teams/{team_id}                                  │
│    └─ Confirms team exists in SaaS API database             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. CHECK CREDIT BALANCE                                     │
│    GET /api/credits/teams/{team_id}/balance                  │
│    └─ Verifies 100 credits allocated                        │
└─────────────────────────────────────────────────────────────┘
```

## What Gets Created

### In SaaS API Database:

- **Organization**: `org_demo_001`
- **Model Groups**:
  - `ChatAgent` (GPT-3.5 Turbo, GPT-4)
  - `AnalysisAgent` (GPT-4)
- **Team**: `team_demo_engineering`
- **Credits**: 100 allocated to team

### In LiteLLM Proxy:

- **Team**: `team_demo_engineering`
- **Virtual Key**: `sk-...` (automatically generated)
- **Model Access**: Based on assigned model groups

## How to Run the Test

### Step 1: Clear Database (Start Fresh)

```bash
python3 scripts/clear_database.py
```

This will:
- Delete all organizations, model groups, teams
- Clear all jobs, calls, and credit transactions
- Remove teams and keys from LiteLLM proxy

### Step 2: Run Integration Test

```bash
python3 scripts/test_full_integration.py
```

### Step 3: View Results in Admin Dashboard

1. Open: http://localhost:3002
2. Login with: `admin` / `admin123`
3. Navigate through:
   - **Organizations**: See `org_demo_001`
   - **Model Groups**: See `ChatAgent` and `AnalysisAgent`
   - **Teams**: See `team_demo_engineering` with virtual key and credits

### Step 4: View in LiteLLM UI (Optional)

1. Open: http://localhost:8002/ui
2. Login with master key: `sk-local-dev-master-key-change-me`
3. Check:
   - Teams section for `team_demo_engineering`
   - Keys section for generated virtual key

## Expected Output

```bash
======================================================================
  TESTING: Create Team with LiteLLM Integration
======================================================================

1. Creating organization...
   Status: 200
   Created successfully

2. Creating model groups...
   ChatAgent created
   AnalysisAgent created

3. Creating team with LiteLLM integration...
   This will:
   - Create team in LiteLLM
   - Generate virtual API key
   - Assign model groups
   - Allocate 100 credits

   Status: 200

----------------------------------------------------------------------
TEAM CREATED SUCCESSFULLY!
----------------------------------------------------------------------
{
  "team_id": "team_demo_engineering",
  "organization_id": "org_demo_001",
  "team_alias": "Demo Engineering Team",
  "virtual_key": "sk-...",
  "model_groups": ["ChatAgent", "AnalysisAgent"],
  "credits_allocated": 100,
  "credits_used": 0,
  "credits_remaining": 100
}
----------------------------------------------------------------------

KEY INFORMATION:
  Team ID: team_demo_engineering
  Virtual Key: sk-xxx...
  Model Groups: ChatAgent, AnalysisAgent
  Credits Allocated: 100

4. Verifying team in SaaS API database...
   Team verified in database

5. Checking credit balance...
   Credits: 100 remaining

======================================================================
SUCCESS! Team created with full LiteLLM integration
======================================================================
```

## Validating the Integration

### 1. **Organization Hierarchy** ✓
- Organization contains teams
- Teams belong to organizations

### 2. **Model Group Assignment** ✓
- Teams can be assigned multiple model groups
- Model groups define which models teams can access

### 3. **LiteLLM Integration** ✓
- SaaS API creates teams in LiteLLM proxy
- Virtual keys are automatically generated
- Teams can make LLM calls using virtual keys

### 4. **Credit System** ✓
- Credits allocated to teams
- Credit balance tracked
- Ready for job-based credit deduction

### 5. **Admin Dashboard** ✓
- Real-time view of all resources
- No mock data - all from database
- Forms to create new resources

## Troubleshooting

### Test Fails at Organization Creation
```bash
# Check SaaS API is running
curl http://localhost:8003/health
```

### Test Fails at Team Creation
```bash
# Check LiteLLM proxy is running
curl -H "Authorization: Bearer sk-local-dev-master-key-change-me" \
  http://localhost:8002/health
```

### Database Connection Errors
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check database connection
psql postgresql://litellm_user:litellm_password@127.0.0.1:5432/litellm
```

### Admin Dashboard Shows No Data
```bash
# Check API is accessible
curl http://localhost:8003/api/organizations

# Verify data exists
psql postgresql://litellm_user:litellm_password@127.0.0.1:5432/litellm \
  -c "SELECT * FROM organizations;"
```

## Next Steps

After running the integration test successfully:

1. **Test LLM Calls**: Use the generated virtual key to make actual LLM calls
2. **Test Job Creation**: Create jobs and track multiple LLM calls
3. **Test Credit Deduction**: Verify credits decrease after successful jobs
4. **Test Model Fallback**: Configure multiple models in a group and test priority routing

## Services Required

All services must be running:

```bash
# PostgreSQL & Redis
docker compose up -d postgres redis

# LiteLLM Proxy (in Docker)
docker compose up -d litellm

# SaaS API (local)
python3 -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003

# Admin Panel (local)
cd admin-panel && npm run dev -- -p 3002
```

## Service URLs

- **SaaS API**: http://localhost:8003
- **LiteLLM Proxy**: http://localhost:8002
- **Admin Dashboard**: http://localhost:3002
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6380

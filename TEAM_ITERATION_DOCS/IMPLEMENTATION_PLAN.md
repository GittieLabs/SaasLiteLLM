# Implementation Plan: Multi-Tenant LLM Platform with Model Groups & Credit-Based Billing

**Version**: 1.0
**Date**: 2025-10-10
**Status**: Planning Phase

---

## 🎯 Project Goals

Build a production-ready multi-tenant LLM platform enabling:
1. **Model Group Abstraction** - Named groups (ResumeAgent, ParsingAgent) that abstract actual models
2. **Organization Hierarchy** - Organizations → Teams → Users
3. **Credit-Based Billing** - 1 successful job = 1 credit (failed jobs tracked but not charged)
4. **Dynamic Model Routing** - Change models from LiteLLM without redeploying SaaS app
5. **Multi-Model Jobs** - Single job can use multiple model groups
6. **External Task Tracking** - Link back to SaaS app's task/job IDs

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR SAAS APP PLATFORM                       │
│  (Document processing, resume parsing, chat, analytics, etc.)   │
│                                                                   │
│  - Creates organizations                                         │
│  - Creates teams (per customer/client)                          │
│  - Submits jobs/tasks with external_task_id                     │
│  - Sends model group names (ResumeAgent, ParsingAgent)          │
│  - Never knows actual LLM models                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP REST API
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               THIS PROJECT: SaaS API Layer                       │
│                  (src/saas_api.py)                              │
│                                                                   │
│  📋 Job Management                                               │
│     - Create job with organization_id + external_task_id        │
│     - Track multiple model groups used per job                  │
│     - Calculate costs & credits                                 │
│                                                                   │
│  🎯 Model Group Resolution                                       │
│     - "ResumeAgent" → gpt-4-turbo (primary)                     │
│     - Fallback to gpt-3.5-turbo if primary fails                │
│     - All teams using group get updates instantly                │
│                                                                   │
│  💳 Credit Management                                            │
│     - Check credits before job starts                           │
│     - Deduct 1 credit only on successful completion             │
│     - Track failed jobs (no credit deduction)                   │
│                                                                   │
│  🏢 Organization & Team Management                               │
│     - Create organizations                                       │
│     - Create teams with org hierarchy                           │
│     - Assign model groups to teams                              │
│     - Generate virtual API keys                                 │
│                                                                   │
│  Database: PostgreSQL                                            │
│     - organizations                                              │
│     - teams (links to LiteLLM teams)                            │
│     - model_groups                                               │
│     - model_group_models (primary + fallbacks)                  │
│     - team_model_groups (assignments)                           │
│     - jobs (with organization_id, external_task_id)             │
│     - llm_calls (tracks which model_group used)                 │
│     - team_credits                                               │
│     - credit_transactions                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Internal HTTP
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LiteLLM Proxy Service                         │
│                 (Vendor abstraction layer)                       │
│                                                                   │
│  - Routes to actual LLM providers                               │
│  - Handles API keys for OpenAI, Anthropic, etc.                │
│  - Caching (Redis)                                               │
│  - Rate limiting per team                                        │
│  - Cost tracking per call                                        │
│  - Automatic retries & fallbacks                                │
│                                                                   │
│  Database: PostgreSQL (LiteLLM's tables)                        │
│     - LiteLLM_VerificationToken (virtual keys)                  │
│     - LiteLLM_TeamTable (team metadata)                         │
│     - LiteLLM_SpendLogs (usage logs)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Provider APIs                             │
│  OpenAI • Anthropic • Azure • Gemini • etc.                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow: Complete Job Lifecycle

### 1. Organization & Team Setup (One-time)

```
[Your SaaS App]
    ↓
POST /api/organizations/create
{
    "organization_id": "org_acme_corp",
    "name": "Acme Corp",
    "metadata": {"plan": "enterprise"}
}
    ↓
POST /api/teams/create
{
    "organization_id": "org_acme_corp",
    "team_id": "team_acme_hr",
    "team_alias": "Acme HR Department",
    "model_groups": ["ResumeAgent", "ParsingAgent", "RAGAgent"],
    "credit_limit": 1000,
    "metadata": {"department": "HR"}
}
    ↓
[SaaS API] Creates team in LiteLLM → Generates virtual key → Returns:
{
    "team_id": "team_acme_hr",
    "virtual_key": "sk-litellm-abc123...",
    "model_groups_assigned": ["ResumeAgent", "ParsingAgent", "RAGAgent"],
    "credits_allocated": 1000
}
```

### 2. Job Creation

```
[Your SaaS App] User uploads resume for parsing
    ↓
POST /api/jobs/create
{
    "organization_id": "org_acme_corp",
    "team_id": "team_acme_hr",
    "external_task_id": "saas_task_789xyz",  ← YOUR internal task ID
    "job_type": "resume_parsing",
    "user_id": "user_john@acme.com",
    "metadata": {
        "filename": "john_doe_resume.pdf",
        "pages": 2
    }
}
    ↓
[SaaS API]
    - Checks team has credits available
    - Creates Job record in database
    - Status: PENDING
    ↓
Returns:
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "credits_available": 247,
    "created_at": "2025-10-10T10:30:00Z"
}
```

### 3. LLM Calls with Multiple Model Groups

```
[Your SaaS App] Step 1: Parse resume structure
    ↓
POST /api/jobs/{job_id}/llm-call
{
    "model_group": "ParsingAgent",  ← Not actual model name!
    "messages": [
        {"role": "system", "content": "Extract structured data from resume"},
        {"role": "user", "content": "[Resume text...]"}
    ],
    "purpose": "structure_extraction"
}
    ↓
[SaaS API]
    - Looks up model_group "ParsingAgent" for this team
    - Finds: primary = gpt-4-turbo, fallback = gpt-3.5-turbo
    - Resolves to actual model: "gpt-4-turbo"
    - Calls LiteLLM with team's virtual key
    ↓
[LiteLLM] Routes to OpenAI gpt-4-turbo
    ↓
[SaaS API]
    - Records LLMCall in database:
        * model_group_used = "ParsingAgent"
        * actual_model = "gpt-4-turbo"
        * tokens, cost, latency
    - Returns to your app:
{
    "call_id": "call_abc123",
    "response": {
        "content": "{\"name\": \"John Doe\", \"email\": \"...\"}"
    },
    "metadata": {
        "tokens_used": 1250,
        "latency_ms": 850
    }
}

─────────────────────────────────────────────────────

[Your SaaS App] Step 2: Extract contact info
    ↓
POST /api/jobs/{job_id}/llm-call
{
    "model_group": "ResumeAgent",  ← Different model group!
    "messages": [
        {"role": "user", "content": "Extract contact information..."}
    ],
    "purpose": "contact_extraction"
}
    ↓
[SaaS API]
    - Looks up "ResumeAgent" → claude-3-opus (primary)
    - Calls LiteLLM
    ↓
[LiteLLM] Routes to Anthropic Claude
    ↓
[SaaS API] Records call with model_group_used = "ResumeAgent"

─────────────────────────────────────────────────────

[Your SaaS App] Step 3: Generate summary with RAG
    ↓
POST /api/jobs/{job_id}/llm-call
{
    "model_group": "RAGAgent",  ← Third model group!
    "messages": [
        {"role": "user", "content": "Summarize with context..."}
    ],
    "purpose": "summary_generation"
}
    ↓
[SaaS API] Looks up "RAGAgent" → gpt-4-turbo-preview
    ↓
Records call with model_group_used = "RAGAgent"
```

### 4. Job Completion & Credit Deduction

```
[Your SaaS App] All processing complete
    ↓
POST /api/jobs/{job_id}/complete
{
    "status": "completed",
    "metadata": {
        "output_file": "parsed_resume_123.json",
        "confidence_score": 0.95
    }
}
    ↓
[SaaS API] Job Completion Logic:
    1. Retrieve all LLM calls for this job
    2. Check if ANY call failed
    3. Calculate total costs across all calls
    4. Determine credit application:

       IF status == "completed" AND no_failed_calls:
           credit_applied = TRUE
           Deduct 1 credit from team
           Create credit_transaction record
       ELSE:
           credit_applied = FALSE
           Track as failed job (for analysis)

    5. Update job record:
       - model_groups_used = ["ParsingAgent", "ResumeAgent", "RAGAgent"]
       - status = "completed"
       - credit_applied = true
       - completed_at = now()

    6. Create JobCostSummary
    ↓
Returns:
{
    "job_id": "550e8400-...",
    "external_task_id": "saas_task_789xyz",
    "status": "completed",
    "credit_applied": true,
    "credits_remaining": 246,
    "model_groups_used": ["ParsingAgent", "ResumeAgent", "RAGAgent"],
    "costs": {
        "total_calls": 3,
        "successful_calls": 3,
        "total_tokens": 4200,
        "total_cost_usd": 0.0342,  ← Internal cost
        "avg_latency_ms": 920
    },
    "calls": [
        {
            "call_id": "call_abc123",
            "model_group": "ParsingAgent",
            "purpose": "structure_extraction",
            "tokens": 1250
        },
        {
            "call_id": "call_def456",
            "model_group": "ResumeAgent",
            "purpose": "contact_extraction",
            "tokens": 1850
        },
        {
            "call_id": "call_ghi789",
            "model_group": "RAGAgent",
            "purpose": "summary_generation",
            "tokens": 1100
        }
    ]
}
```

### 5. Failed Job Scenario (No Credit Deduction)

```
[Your SaaS App] Job fails during processing
    ↓
POST /api/jobs/{job_id}/complete
{
    "status": "failed",
    "error_message": "Unable to parse PDF format"
}
    ↓
[SaaS API] Job Completion Logic:
    - status = "failed"
    - credit_applied = FALSE
    - No credit deducted
    - Job tracked in database for analysis
    ↓
Returns:
{
    "job_id": "550e8400-...",
    "status": "failed",
    "credit_applied": false,
    "credits_remaining": 246,  ← Same as before
    "costs": {
        "total_calls": 1,
        "failed_calls": 1,
        "total_cost_usd": 0.0012  ← You still paid LiteLLM
    }
}

Note: You absorbed the LLM cost but didn't charge customer
```

---

## 🗄️ Database Schema

### New Tables

#### `organizations`
```sql
CREATE TABLE organizations (
    organization_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `model_groups`
```sql
CREATE TABLE model_groups (
    model_group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_name VARCHAR(100) UNIQUE NOT NULL,  -- "ResumeAgent"
    display_name VARCHAR(200),  -- "Resume Analysis Agent"
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `model_group_models`
```sql
CREATE TABLE model_group_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_group_id UUID REFERENCES model_groups(model_group_id) ON DELETE CASCADE,
    model_name VARCHAR(200) NOT NULL,  -- "gpt-4-turbo", "claude-3-opus"
    priority INT DEFAULT 0,  -- 0 = primary, 1 = first fallback, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_model_group_models_lookup
    ON model_group_models(model_group_id, priority, is_active);
```

#### `team_model_groups`
```sql
CREATE TABLE team_model_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    model_group_id UUID REFERENCES model_groups(model_group_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, model_group_id)
);

CREATE INDEX idx_team_model_groups ON team_model_groups(team_id);
```

#### `team_credits`
```sql
CREATE TABLE team_credits (
    team_id VARCHAR(255) PRIMARY KEY,
    organization_id VARCHAR(255) REFERENCES organizations(organization_id),
    credits_allocated INT DEFAULT 0,
    credits_used INT DEFAULT 0,
    credits_remaining INT GENERATED ALWAYS AS (credits_allocated - credits_used) STORED,
    credit_limit INT,  -- Hard limit
    auto_refill BOOLEAN DEFAULT FALSE,
    refill_amount INT,
    refill_period VARCHAR(50),  -- "monthly", "weekly"
    last_refill_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `credit_transactions`
```sql
CREATE TABLE credit_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id VARCHAR(255) NOT NULL,
    organization_id VARCHAR(255),
    job_id UUID REFERENCES jobs(job_id),
    transaction_type VARCHAR(50),  -- "deduction", "allocation", "refund"
    credits_amount INT NOT NULL,
    credits_before INT NOT NULL,
    credits_after INT NOT NULL,
    reason VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_credit_transactions_team ON credit_transactions(team_id, created_at);
CREATE INDEX idx_credit_transactions_job ON credit_transactions(job_id);
```

### Modified Tables

#### `jobs` (Extended)
```sql
ALTER TABLE jobs ADD COLUMN organization_id VARCHAR(255);
ALTER TABLE jobs ADD COLUMN external_task_id VARCHAR(255);  -- YOUR task ID
ALTER TABLE jobs ADD COLUMN credit_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN model_groups_used TEXT[];  -- Array of group names used

CREATE INDEX idx_jobs_external_task ON jobs(external_task_id);
CREATE INDEX idx_jobs_organization ON jobs(organization_id, created_at);
```

#### `llm_calls` (Extended)
```sql
ALTER TABLE llm_calls ADD COLUMN model_group_used VARCHAR(100);  -- Which group was used
ALTER TABLE llm_calls ADD COLUMN resolved_model VARCHAR(200);  -- Actual model after resolution

CREATE INDEX idx_llm_calls_model_group ON llm_calls(model_group_used);
```

---

## 🔌 API Endpoints

### Organization Management

```
POST   /api/organizations/create
GET    /api/organizations/{org_id}
GET    /api/organizations/{org_id}/teams
GET    /api/organizations/{org_id}/usage
```

### Model Groups Management

```
POST   /api/model-groups/create
    Body: {
        "group_name": "ResumeAgent",
        "display_name": "Resume Analysis Agent",
        "models": [
            {"model_name": "gpt-4-turbo", "priority": 0},
            {"model_name": "gpt-3.5-turbo", "priority": 1}
        ]
    }

GET    /api/model-groups
GET    /api/model-groups/{group_id}
PUT    /api/model-groups/{group_id}
DELETE /api/model-groups/{group_id}

POST   /api/model-groups/{group_id}/models/add
DELETE /api/model-groups/{group_id}/models/{model_id}
PUT    /api/model-groups/{group_id}/models/{model_id}/priority
```

### Team Management (Enhanced)

```
POST   /api/teams/create
    Body: {
        "organization_id": "org_acme",
        "team_id": "team_acme_hr",
        "team_alias": "Acme HR",
        "model_groups": ["ResumeAgent", "ParsingAgent"],
        "credit_limit": 1000,
        "metadata": {}
    }

GET    /api/teams/{team_id}
PUT    /api/teams/{team_id}/model-groups
    Body: {
        "model_groups": ["ResumeAgent", "ParsingAgent", "RAGAgent"]
    }

POST   /api/teams/{team_id}/keys/generate
GET    /api/teams/{team_id}/keys
DELETE /api/teams/{team_id}/keys/{key_id}
```

### Credit Management

```
GET    /api/teams/{team_id}/credits
POST   /api/teams/{team_id}/credits/add
    Body: {
        "credits": 500,
        "reason": "Monthly allocation"
    }

GET    /api/teams/{team_id}/credits/transactions
GET    /api/teams/{team_id}/credits/balance
```

### Job Management (Enhanced)

```
POST   /api/jobs/create
    Body: {
        "organization_id": "org_acme",
        "team_id": "team_acme_hr",
        "external_task_id": "saas_task_123",  ← YOUR task ID
        "job_type": "resume_parsing",
        "user_id": "user@example.com",
        "metadata": {}
    }

POST   /api/jobs/{job_id}/llm-call
    Body: {
        "model_group": "ResumeAgent",  ← Group name, not model
        "messages": [...],
        "purpose": "extraction",
        "temperature": 0.7
    }

POST   /api/jobs/{job_id}/complete
    Body: {
        "status": "completed",  # or "failed"
        "metadata": {},
        "error_message": null
    }

GET    /api/jobs/{job_id}
GET    /api/jobs?external_task_id={id}  ← Query by YOUR task ID
GET    /api/teams/{team_id}/jobs
```

### Usage & Analytics

```
GET    /api/teams/{team_id}/usage?period=2025-10
    Returns: {
        "credits_used": 42,
        "credits_remaining": 958,
        "jobs_completed": 42,
        "jobs_failed": 3,
        "model_group_breakdown": {
            "ResumeAgent": {"calls": 65, "cost_usd": 2.34},
            "ParsingAgent": {"calls": 42, "cost_usd": 1.12}
        }
    }

GET    /api/organizations/{org_id}/usage?period=2025-10
```

---

## 🎯 Model Group Resolution Logic

### Resolution Flow

```python
# When your SaaS app makes this call:
POST /api/jobs/{job_id}/llm-call
{
    "model_group": "ResumeAgent",
    ...
}

# SaaS API does this:

1. Lookup team's assigned model groups
   → Check team_model_groups where team_id = X

2. Verify team has access to "ResumeAgent"
   → If not authorized: Error 403

3. Get primary model for this group
   → Query model_group_models WHERE
       model_group_id = (SELECT id FROM model_groups WHERE group_name = 'ResumeAgent')
       AND priority = 0
       AND is_active = TRUE
   → Result: "gpt-4-turbo"

4. Call LiteLLM with resolved model
   → POST to LiteLLM /chat/completions
   → Authorization: Bearer {team_virtual_key}
   → Body: {"model": "gpt-4-turbo", ...}

5. If call fails and fallback configured:
   → Get priority = 1 model
   → Retry with "gpt-3.5-turbo"

6. Record in llm_calls table:
   → model_group_used = "ResumeAgent"
   → resolved_model = "gpt-4-turbo"
   → Actual costs, tokens, etc.
```

### Updating Model Group (Admin)

```
PUT /api/model-groups/resume-agent-id
{
    "models": [
        {"model_name": "gpt-4o", "priority": 0},  ← NEW primary
        {"model_name": "gpt-4-turbo", "priority": 1}  ← OLD primary now fallback
    ]
}

Effect:
- ALL teams using "ResumeAgent" now get gpt-4o
- No changes needed in your SaaS app
- Next job/task automatically uses new model
```

---

## 💳 Credit System Logic

### Credit Check (Before Job)
```python
def check_credits(team_id: str) -> bool:
    credits = db.query(TeamCredits).filter_by(team_id=team_id).first()

    if not credits:
        raise Exception("Team not found")

    if credits.credits_remaining <= 0:
        raise InsufficientCreditsError(
            f"Team has 0 credits remaining. Allocated: {credits.credits_allocated}"
        )

    return True
```

### Credit Deduction (After Job Completion)
```python
def complete_job(job_id: str, status: str):
    job = get_job(job_id)

    # Check if credit should be applied
    if status == "completed":
        # Check if any LLM call failed
        failed_calls = count_failed_calls(job_id)

        if failed_calls == 0:
            # SUCCESS: Deduct credit
            deduct_credit(
                team_id=job.team_id,
                job_id=job_id,
                reason="Job completed successfully"
            )
            job.credit_applied = True
        else:
            # PARTIAL FAILURE: No credit
            job.credit_applied = False
    else:
        # FAILED: No credit
        job.credit_applied = False

    job.status = status
    job.completed_at = datetime.utcnow()
    db.commit()

def deduct_credit(team_id: str, job_id: str, reason: str):
    credits = db.query(TeamCredits).filter_by(team_id=team_id).first()

    credits_before = credits.credits_remaining
    credits.credits_used += 1
    # credits_remaining auto-calculated by SQL

    # Create transaction record
    transaction = CreditTransaction(
        team_id=team_id,
        job_id=job_id,
        transaction_type="deduction",
        credits_amount=1,
        credits_before=credits_before,
        credits_after=credits_before - 1,
        reason=reason
    )

    db.add(transaction)
    db.commit()
```

### Credit Tracking

| Scenario | Credit Applied? | Tracked? |
|----------|----------------|----------|
| Job completed, all LLM calls succeeded | ✅ Yes | ✅ Yes |
| Job completed, 1+ LLM calls failed | ❌ No | ✅ Yes (for analysis) |
| Job marked as failed | ❌ No | ✅ Yes |
| Job in progress (not completed) | ❌ No | ✅ Yes |

---

## 🧪 Testing Plan (Railway Dev Environment)

### Setup Railway Dev

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create dev environment
railway environment create dev

# Deploy services
railway up --environment dev
```

### Test Sequence

#### Test 1: Model Groups
```bash
# 1. Create model groups
curl -X POST https://dev-saas-api.railway.app/api/model-groups/create \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "ResumeAgent",
    "display_name": "Resume Analysis Agent",
    "models": [
      {"model_name": "gpt-4-turbo", "priority": 0},
      {"model_name": "gpt-3.5-turbo", "priority": 1}
    ]
  }'

# 2. Create more groups
# ParsingAgent, RequirementAgent, ExecutiveSummaryAgent, RAGAgent

# 3. List all groups
curl https://dev-saas-api.railway.app/api/model-groups
```

#### Test 2: Organization & Team
```bash
# 1. Create organization
curl -X POST .../api/organizations/create \
  -d '{"organization_id": "org_test_123", "name": "Test Org"}'

# 2. Create team
curl -X POST .../api/teams/create \
  -d '{
    "organization_id": "org_test_123",
    "team_id": "team_test_hr",
    "model_groups": ["ResumeAgent", "ParsingAgent"],
    "credit_limit": 100
  }'

# Response includes:
# - team_id
# - virtual_key (use for LiteLLM calls)
# - credits_allocated

# 3. Verify team
curl .../api/teams/team_test_hr
```

#### Test 3: Multi-Model Group Job
```bash
# 1. Create job
JOB_ID=$(curl -X POST .../api/jobs/create \
  -d '{
    "organization_id": "org_test_123",
    "team_id": "team_test_hr",
    "external_task_id": "my_app_task_789",
    "job_type": "resume_parsing"
  }' | jq -r '.job_id')

# 2. Call #1: ParsingAgent
curl -X POST .../api/jobs/$JOB_ID/llm-call \
  -d '{
    "model_group": "ParsingAgent",
    "messages": [
      {"role": "user", "content": "Parse this resume structure"}
    ],
    "purpose": "structure_extraction"
  }'

# 3. Call #2: ResumeAgent
curl -X POST .../api/jobs/$JOB_ID/llm-call \
  -d '{
    "model_group": "ResumeAgent",
    "messages": [
      {"role": "user", "content": "Extract contact info"}
    ],
    "purpose": "contact_extraction"
  }'

# 4. Call #3: RAGAgent
curl -X POST .../api/jobs/$JOB_ID/llm-call \
  -d '{
    "model_group": "RAGAgent",
    "messages": [
      {"role": "user", "content": "Summarize with context"}
    ],
    "purpose": "summary"
  }'

# 5. Complete job
curl -X POST .../api/jobs/$JOB_ID/complete \
  -d '{"status": "completed"}'

# Response should show:
# - credit_applied: true
# - credits_remaining: 99
# - model_groups_used: ["ParsingAgent", "ResumeAgent", "RAGAgent"]
```

#### Test 4: Credit Exhaustion
```bash
# 1. Check credits
curl .../api/teams/team_test_hr/credits

# 2. Use all credits (run 100 jobs)

# 3. Try creating job #101
curl -X POST .../api/jobs/create \
  -d '{
    "team_id": "team_test_hr",
    "job_type": "test"
  }'

# Expected: 402 Payment Required
# "Insufficient credits. Team has 0 credits remaining."
```

#### Test 5: Failed Job (No Credit)
```bash
# 1. Create job
JOB_ID=...

# 2. Make LLM call that fails
# (simulate by using invalid model or bad request)

# 3. Complete as failed
curl -X POST .../api/jobs/$JOB_ID/complete \
  -d '{
    "status": "failed",
    "error_message": "Processing error"
  }'

# Verify:
# - credit_applied: false
# - credits_remaining: unchanged
# - Job tracked in database
```

#### Test 6: Model Group Update
```bash
# 1. Update ResumeAgent to use new model
curl -X PUT .../api/model-groups/{group_id} \
  -d '{
    "models": [
      {"model_name": "gpt-4o", "priority": 0},
      {"model_name": "gpt-4-turbo", "priority": 1}
    ]
  }'

# 2. Create new job
# 3. Make call with "ResumeAgent"
# 4. Verify it uses gpt-4o (check llm_calls.resolved_model)
```

#### Test 7: External Task ID Lookup
```bash
# 1. Create job with external_task_id
curl -X POST .../api/jobs/create \
  -d '{
    "team_id": "team_test_hr",
    "external_task_id": "saas_task_unique_123",
    "job_type": "test"
  }'

# 2. Look up by external task ID
curl '.../api/jobs?external_task_id=saas_task_unique_123'

# Should return the job details
```

---

## 📁 Implementation Files

### New Files to Create

```
src/models/
  ├── organizations.py          # Organization schema
  ├── model_groups.py           # Model group schemas
  ├── credits.py                # Credit tracking schemas
  └── teams.py                  # Team extensions

src/api/
  ├── organizations.py          # Organization endpoints
  ├── model_groups.py           # Model group management
  ├── teams.py                  # Enhanced team management
  ├── credits.py                # Credit operations
  └── jobs.py                   # Move job endpoints here

src/services/
  ├── model_resolver.py         # Resolve model groups → actual models
  ├── credit_manager.py         # Credit deduction/allocation logic
  └── team_manager.py           # Team creation with LiteLLM integration

scripts/migrations/
  ├── 002_create_organizations.sql
  ├── 003_create_model_groups.sql
  ├── 004_create_credits.sql
  └── 005_extend_jobs_and_calls.sql

scripts/
  ├── test_railway_dev.py       # Complete test workflow
  ├── seed_model_groups.py      # Seed initial model groups
  └── setup_dev_team.py         # Quick dev team setup

docs/
  └── IMPLEMENTATION_PLAN.md    # This document
```

### Files to Modify

```
src/saas_api.py                 # Add new routers, integrate services
src/models/job_tracking.py      # Extend Job and LLMCall models
src/config/settings.py          # Add new config options
```

---

## ✅ Success Criteria

### Functional Requirements
- [ ] Can create organizations
- [ ] Can create teams with organization_id
- [ ] Can create model groups (ResumeAgent, ParsingAgent, etc.)
- [ ] Can assign primary + fallback models to groups
- [ ] Can assign model groups to teams
- [ ] Can generate virtual keys for teams
- [ ] Team creation creates entry in LiteLLM's database
- [ ] Can create jobs with external_task_id
- [ ] Can make LLM calls with model group names
- [ ] Model group names resolved to actual models
- [ ] Multiple model groups can be used in single job
- [ ] All model groups used tracked in job
- [ ] Credits checked before job creation
- [ ] Credits deducted only on successful completion
- [ ] Failed jobs don't consume credits
- [ ] Can query job by external_task_id
- [ ] Can update model group's models
- [ ] All teams using group get model updates
- [ ] Credit transactions logged
- [ ] Usage analytics by team, org, model group

### Non-Functional Requirements
- [ ] All APIs respond < 500ms
- [ ] Database migrations are reversible
- [ ] Zero downtime model group updates
- [ ] Credit deduction is transactional (no double-charge)
- [ ] Failed LLM calls don't crash job
- [ ] Fallback models work automatically
- [ ] Complete test coverage on Railway dev

---

## 🚀 Deployment Steps

### Local Development
1. Create migrations
2. Run migrations locally
3. Implement model groups
4. Implement organizations & teams
5. Implement credits
6. Test end-to-end locally

### Railway Dev Environment
1. Push code to GitHub
2. Deploy to Railway dev environment
3. Run migrations on Railway Postgres
4. Seed model groups
5. Run complete test suite
6. Verify credit tracking
7. Test model group updates
8. Document any issues

### Production
1. Review test results
2. Create production checklist
3. Deploy to Railway production
4. Monitor for 24 hours
5. Enable for limited teams
6. Full rollout

---

## 📊 Estimated Timeline

| Phase | Tasks | Time Estimate |
|-------|-------|---------------|
| **Phase 1** | Database schemas & migrations | 4-6 hours |
| **Phase 2** | Model groups implementation | 4-5 hours |
| **Phase 3** | Organizations & teams | 4-5 hours |
| **Phase 4** | Credits system | 5-6 hours |
| **Phase 5** | Job enhancements | 3-4 hours |
| **Phase 6** | Railway dev setup & testing | 4-5 hours |
| **Phase 7** | Documentation & refinement | 2-3 hours |
| **Total** | | **26-34 hours** |

---

## 📝 Open Questions

1. **Credit refill automation**: Should credits auto-refill monthly, or manual?
2. **Credit overage**: Allow teams to go negative or hard stop?
3. **Model group permissions**: Can teams create their own groups, or admin-only?
4. **Fallback chain**: How many fallback models per group?
5. **Cost pass-through**: Do you want to expose actual LLM costs to orgs?
6. **Webhooks**: Should job completion trigger webhooks to your SaaS app?

---

## 🎯 Next Steps

After approval:
1. Create database migration files
2. Implement model groups API
3. Implement organizations & teams API
4. Implement credit system
5. Integrate into existing SaaS API
6. Deploy to Railway dev
7. Run complete test suite
8. Document results and iterate

Ready to proceed? 🚀

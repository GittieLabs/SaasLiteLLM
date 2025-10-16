# LiteLLM Call Tracking & Budgeting Architecture

## Current Implementation ✅

### What's Already Working

The system **ALREADY tracks LiteLLM calls to jobs** with full bi-directional linking:

**1. LiteLLM → SaaS API Tracking**
- Every LiteLLM response includes a unique request ID
- Stored in `LLMCall.litellm_request_id` (src/models/job_tracking.py:106)
- This allows querying LiteLLM's database for detailed logs

**2. SaaS API → LiteLLM Tracking**
- Each `LLMCall` record links to `job_id` via foreign key
- Can trace all LLM calls for any job
- Can aggregate costs per job

**3. What Gets Tracked Per Call**
```python
LLMCall:
  - litellm_request_id: "chatcmpl-xyz123"  # LiteLLM's unique ID
  - job_id: "uuid-of-job"                   # SaaS job ID
  - model_used: "gpt-4o"                    # Actual model used
  - model_group_used: "chat-fast"           # Model alias requested
  - resolved_model: "openai/gpt-4o"         # Provider/model combo
  - prompt_tokens: 150
  - completion_tokens: 75
  - total_tokens: 225
  - cost_usd: 0.004500                      # ISSUE: Hardcoded estimate
  - latency_ms: 1250
  - request_data: {...}                     # Full request
  - response_data: {...}                    # Full LiteLLM response
```

## Critical Issue ⚠️

**Location:** src/saas_api.py:326-328

```python
# Calculate cost (LiteLLM includes this in response metadata)
# For now, estimate: gpt-3.5-turbo is $0.0005/1K prompt, $0.0015/1K completion
cost_usd = (prompt_tokens * 0.0005 / 1000) + (completion_tokens * 0.0015 / 1000)
```

**Problem:** Using hardcoded pricing instead of LiteLLM's actual calculated costs!

LiteLLM calculates accurate costs based on:
- Model-specific pricing from model aliases
- Provider-specific rates
- Volume discounts
- Streaming vs non-streaming

The response includes the actual cost in `_hidden_params.response_cost` or similar fields.

## Solution: Extract Real Costs from LiteLLM

LiteLLM's response structure (varies by version):
```python
{
  "id": "chatcmpl-xyz",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 75,
    "total_tokens": 225
  },
  "_hidden_params": {
    "response_cost": 0.004500,
    "model_id": "model_xyz",
    "...": "..."
  }
}
```

**Fix:** Extract real cost from LiteLLM response instead of estimating.

## Budgeting Modes

### Mode 1: Job-Based Credits (Current Implementation)
- 1 successful job = 1 credit
- Simple, predictable for users
- Already implemented in src/saas_api.py:380-447
- Team has X credits, each completed job deducts 1

**Implementation:**
```python
if (request.status == "completed" and
    costs["failed_calls"] == 0 and
    not job.credit_applied):
    credit_manager.deduct_credit(
        team_id=job.team_id,
        job_id=job.job_id,
        credits_amount=1,  # Fixed: 1 credit per job
        reason=f"Job {job.job_type} completed successfully"
    )
```

### Mode 2: Consumption-Based Budgeting (New Requirement)

**Options:**

**A. USD-Based Budget**
- Team has max_budget in LiteLLM (e.g., $100.00)
- Each LLM call deducts actual cost from budget
- LiteLLM enforces the limit automatically
- SaaS API just tracks for reporting

**B. Token-Based Budget**
- Team has max tokens (e.g., 1,000,000 tokens)
- Each call deducts actual tokens used
- Need custom enforcement in SaaS API

**C. Hybrid: Credits = $ Amount**
- 1 credit = $0.10 (or configurable)
- Jobs deduct actual cost converted to credits
- Flexible: `credits_to_deduct = actual_cost_usd / 0.10`

## Recommended Implementation

### Step 1: Fix Cost Calculation (Immediate)
Extract real costs from LiteLLM response:

```python
# In call_litellm() or make_llm_call():
litellm_response = await call_litellm(...)

# Extract actual cost from LiteLLM
cost_usd = 0.0
if "_hidden_params" in litellm_response:
    cost_usd = litellm_response["_hidden_params"].get("response_cost", 0.0)

# Fallback: calculate from usage if cost not provided
if not cost_usd:
    # Use model-specific pricing from database
    cost_usd = calculate_cost_from_model_pricing(
        model=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens
    )
```

### Step 2: Add Budget Mode to Teams

Add `budget_mode` field to TeamCredits:
```python
budget_mode: "job_based" | "consumption_usd" | "consumption_tokens"
```

### Step 3: Flexible Credit Deduction

```python
if team.budget_mode == "job_based":
    # Current behavior: 1 credit per job
    credits_to_deduct = 1
elif team.budget_mode == "consumption_usd":
    # Credits = dollars * 10 (1 credit = $0.10)
    credits_to_deduct = int(costs["total_cost_usd"] * 10)
elif team.budget_mode == "consumption_tokens":
    # 1 credit = 10,000 tokens
    credits_to_deduct = costs["total_tokens"] // 10000
```

### Step 4: Use LiteLLM's Max Budget

LiteLLM teams already have `max_budget` in USD:
```python
await litellm_service.create_team(
    team_id=team_id,
    max_budget=100.00  # $100 limit
)
```

For consumption-based teams:
- Set appropriate max_budget in LiteLLM
- LiteLLM will enforce limits automatically
- SaaS API tracks for billing/reporting

## Data Flow

### Request Flow
```
1. Client -> POST /api/jobs/create
   └─> Creates Job record with status=PENDING

2. Client -> POST /api/jobs/{job_id}/llm-call
   ├─> Resolves model alias to actual model
   ├─> Calls LiteLLM proxy with team's virtual_key
   │   └─> LiteLLM tracks: team, model, tokens, cost
   ├─> Receives response with:
   │   - id: "chatcmpl-xyz"
   │   - usage: {tokens...}
   │   - _hidden_params.response_cost: 0.004500
   └─> Creates LLMCall record:
       - litellm_request_id = "chatcmpl-xyz"
       - job_id = job's UUID
       - Actual cost from LiteLLM
       - Full request/response stored

3. Client -> POST /api/jobs/{job_id}/complete
   ├─> Aggregates all LLMCall records for job
   ├─> Calculates total cost, tokens
   ├─> Deducts credits based on budget_mode
   └─> Creates JobCostSummary record
```

### Query Capabilities

**Track by Job:**
```sql
SELECT * FROM llm_calls WHERE job_id = 'uuid';
-- Returns all LLM calls for this job
```

**Track by LiteLLM Request:**
```sql
SELECT * FROM llm_calls WHERE litellm_request_id = 'chatcmpl-xyz';
-- Links LiteLLM's logs to our job
```

**Team Usage:**
```sql
SELECT j.team_id, SUM(l.cost_usd), SUM(l.total_tokens)
FROM jobs j
JOIN llm_calls l ON l.job_id = j.job_id
WHERE j.team_id = 'team_123'
  AND j.created_at >= '2025-10-01'
GROUP BY j.team_id;
```

**Model Alias Usage:**
```sql
SELECT model_group_used, COUNT(*), SUM(cost_usd)
FROM llm_calls
WHERE job_id IN (
  SELECT job_id FROM jobs WHERE team_id = 'team_123'
)
GROUP BY model_group_used;
```

## Implementation Priority

1. **✅ Already Working:**
   - Job → LLM Call linking
   - LiteLLM request ID tracking
   - Token usage tracking
   - Model alias tracking

2. **⚠️ Critical Fix Needed:**
   - Extract real costs from LiteLLM response
   - Stop using hardcoded pricing

3. **🎯 Enhancement for Flexibility:**
   - Add budget_mode to teams
   - Support consumption-based billing
   - Configurable credit-to-dollar ratio

4. **📊 Reporting:**
   - Already have all data needed
   - Can generate any report by team/model/period
   - Just need frontend dashboards

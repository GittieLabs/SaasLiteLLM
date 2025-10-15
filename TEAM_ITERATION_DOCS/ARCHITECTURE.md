# SaaS Job-Based Cost Tracking Architecture

## Overview

This architecture abstracts LiteLLM behind your SaaS API, enabling:
- Job-based cost tracking (multiple LLM calls per job)
- Team isolation without direct LiteLLM access
- Hidden model selection and pricing
- Per-job cost aggregation and analytics

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│  Your SaaS Application Frontend                 │
│  (Teams never see LiteLLM/models/pricing)       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  SaaS API Layer (NEW - This Project)            │
│  - /api/jobs/create                             │
│  - /api/jobs/{job_id}/llm-call                  │
│  - /api/jobs/{job_id}/complete                  │
│  - /api/jobs/{job_id}/costs                     │
│  - /api/teams/{team_id}/usage                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  LiteLLM Proxy (Backend Service)                │
│  - Hidden from teams                            │
│  - Handles actual LLM routing                   │
│  - Tracks individual call costs                 │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  PostgreSQL Database                            │
│  - jobs: Job metadata and status                │
│  - llm_calls: Individual LLM calls per job      │
│  - job_costs: Aggregated costs per job          │
│  - team_usage: Team-level usage analytics       │
└─────────────────────────────────────────────────┘
```

## Database Schema

### jobs
- `job_id` (UUID, PK)
- `team_id` (string) - Your SaaS team identifier
- `user_id` (string) - Your SaaS user identifier
- `job_type` (string) - e.g., "document_analysis", "chat_session"
- `status` (enum) - pending, in_progress, completed, failed
- `created_at` (timestamp)
- `completed_at` (timestamp)
- `metadata` (jsonb) - Custom job data

### llm_calls
- `call_id` (UUID, PK)
- `job_id` (UUID, FK)
- `model_used` (string) - Internal tracking only
- `prompt_tokens` (int)
- `completion_tokens` (int)
- `cost_usd` (decimal)
- `latency_ms` (int)
- `created_at` (timestamp)
- `litellm_request_id` (string) - For debugging

### job_costs (aggregated view)
- `job_id` (UUID, FK)
- `total_calls` (int)
- `total_prompt_tokens` (int)
- `total_completion_tokens` (int)
- `total_cost_usd` (decimal)
- `avg_latency_ms` (int)

### team_usage (analytics)
- `team_id` (string)
- `period` (string) - e.g., "2024-10"
- `total_jobs` (int)
- `successful_jobs` (int)
- `failed_jobs` (int)
- `total_cost_usd` (decimal)

## API Endpoints (Your SaaS Layer)

### Job Management

#### POST /api/jobs/create
Create a new job for tracking multiple LLM calls.

**Request:**
```json
{
  "team_id": "acme-corp",
  "user_id": "user_123",
  "job_type": "document_analysis",
  "metadata": {
    "document_id": "doc_456",
    "pages": 10
  }
}
```

**Response:**
```json
{
  "job_id": "job_789abc",
  "status": "pending",
  "created_at": "2024-10-08T20:00:00Z"
}
```

#### POST /api/jobs/{job_id}/llm-call
Make an LLM call within a job context.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Analyze this document..."}
  ],
  "purpose": "document_summary",  // Your internal categorization
  "temperature": 0.7
}
```

**Response:**
```json
{
  "call_id": "call_xyz",
  "response": {
    "content": "...",
    "finish_reason": "stop"
  },
  "metadata": {
    "tokens_used": 1500,
    "latency_ms": 850
  }
}
```
*Note: No model or cost info exposed to client*

#### POST /api/jobs/{job_id}/complete
Mark job as complete and get aggregated costs.

**Request:**
```json
{
  "status": "completed",  // or "failed"
  "metadata": {
    "result": "success",
    "output_file": "output_789.pdf"
  }
}
```

**Response:**
```json
{
  "job_id": "job_789abc",
  "status": "completed",
  "completed_at": "2024-10-08T20:05:00Z",
  "costs": {
    "total_calls": 5,
    "total_tokens": 7500,
    "total_cost_usd": 0.0234,  // Internal use - not shown to teams
    "avg_latency_ms": 920
  },
  "calls": [
    {
      "call_id": "call_xyz",
      "purpose": "document_summary",
      "tokens": 1500,
      "latency_ms": 850
    }
    // ... other calls
  ]
}
```

#### GET /api/jobs/{job_id}/costs
Get detailed cost breakdown for a job (admin/internal only).

**Response:**
```json
{
  "job_id": "job_789abc",
  "costs": {
    "total_cost_usd": 0.0234,
    "breakdown": [
      {
        "call_id": "call_xyz",
        "model": "gpt-3.5-turbo",  // Internal only
        "cost_usd": 0.0045,
        "tokens": 1500
      }
    ]
  }
}
```

### Team Analytics

#### GET /api/teams/{team_id}/usage
Get team usage summary (for your internal billing/analytics).

**Query Params:**
- `period`: "2024-10", "2024-10-08", etc.

**Response:**
```json
{
  "team_id": "acme-corp",
  "period": "2024-10",
  "summary": {
    "total_jobs": 150,
    "successful_jobs": 145,
    "failed_jobs": 5,
    "total_cost_usd": 12.45,
    "total_tokens": 425000,
    "avg_cost_per_job": 0.083
  },
  "job_types": {
    "document_analysis": {
      "count": 80,
      "cost_usd": 8.20
    },
    "chat_session": {
      "count": 70,
      "cost_usd": 4.25
    }
  }
}
```

### Webhook Support

#### POST /api/webhooks/register
Register webhook for job completion events.

**Request:**
```json
{
  "team_id": "acme-corp",
  "webhook_url": "https://your-saas.com/webhooks/job-complete",
  "events": ["job.completed", "job.failed"]
}
```

**Webhook Payload:**
```json
{
  "event": "job.completed",
  "job_id": "job_789abc",
  "team_id": "acme-corp",
  "timestamp": "2024-10-08T20:05:00Z",
  "data": {
    "total_calls": 5,
    "duration_seconds": 45
  }
}
```

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Create database schema (jobs, llm_calls, job_costs tables)
2. Build SaaS API wrapper service
3. Implement job lifecycle management
4. Add LLM call proxying with job_id tracking

### Phase 2: Cost Tracking
1. Capture costs from LiteLLM responses
2. Aggregate costs per job
3. Build analytics queries
4. Create admin cost dashboards

### Phase 3: Advanced Features
1. Webhook system for job events
2. Cost alerts and budget limits per team
3. Usage-based pricing calculator
4. Cost optimization recommendations

## Security Model

### API Keys
- **Your SaaS → LiteLLM**: Use team-specific virtual keys (already configured)
- **Teams → Your SaaS**: Your own JWT/API key system
- **LiteLLM Admin UI**: Completely hidden from teams (internal only)

### Data Isolation
- All queries filtered by `team_id`
- Job IDs are UUIDs (non-guessable)
- LiteLLM master key never exposed
- Model pricing completely abstracted

## Cost Management Strategy

### Markup Pricing
```python
# Example: Add 30% markup to actual costs
actual_cost_usd = 0.0234
your_price_usd = actual_cost_usd * 1.30  # $0.0304

# Or flat rate per job type
job_type_pricing = {
    "document_analysis": 0.10,  # Flat $0.10 per job
    "chat_session": 0.05        # Flat $0.05 per session
}
```

### Budget Controls
- Set monthly budget per team (already in config)
- Alert when team reaches 80% of budget
- Auto-disable team at 100% budget
- Track actual costs vs. customer billing

## Benefits of This Architecture

✅ **Teams never see LiteLLM** - Complete abstraction
✅ **Job-based cost tracking** - True cost per business operation
✅ **Model flexibility** - Change models without affecting clients
✅ **Pricing control** - Set your own markup/pricing
✅ **Usage analytics** - Detailed insights per team/job type
✅ **Budget protection** - Prevent runaway costs
✅ **Multi-call jobs** - Track related LLM calls as single unit

## Example Usage Flow

```python
# Your SaaS application code
import requests

# 1. Create a job
job = requests.post("https://api.your-saas.com/api/jobs/create", json={
    "team_id": "acme-corp",
    "user_id": "user_123",
    "job_type": "document_analysis"
}).json()

job_id = job["job_id"]

# 2. Make multiple LLM calls for this job
for page in document.pages:
    requests.post(f"https://api.your-saas.com/api/jobs/{job_id}/llm-call", json={
        "messages": [{"role": "user", "content": f"Analyze page: {page.text}"}],
        "purpose": f"page_{page.number}_analysis"
    })

# 3. Complete the job and get costs
result = requests.post(f"https://api.your-saas.com/api/jobs/{job_id}/complete", json={
    "status": "completed"
}).json()

# result["costs"]["total_cost_usd"] = 0.0234 (internal tracking)
# You charge customer: $0.10 (flat rate or markup)
# Your profit: $0.0766
```

## Next Steps

Choose what to implement:
1. **Database schema** - Create tables for job tracking
2. **API wrapper service** - FastAPI app with job endpoints
3. **Cost aggregation** - Utilities to sum costs per job
4. **Admin dashboard** - View costs/jobs (internal only)
5. **Webhook system** - Notify your app on job completion

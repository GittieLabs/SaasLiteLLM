# SaaS LiteLLM API Integration Guide

Complete guide for integrating the SaaS LiteLLM API into your projects.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Integration Flow](#integration-flow)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)

---

## Overview

The SaaS LiteLLM API provides a job-based abstraction layer for LLM calls with:

- **Multi-tenant architecture**: Organizations → Teams → Users
- **Credit-based billing**: 1 credit per successful job
- **Model groups**: Named collections of models with fallbacks
- **Cost tracking**: Track actual LLM costs vs credits charged
- **Virtual keys**: Team-specific API keys with budget limits

### Architecture

```
Your SaaS App → SaaS API → LiteLLM Proxy → LLM Providers
                    ↓
                PostgreSQL (tracking, billing)
```

---

## Quick Start

### Base URL

```
Production: https://saas-api-production-5b42.up.railway.app
```

### 1. Set Up Organization & Team

```bash
# Create organization
curl -X POST https://saas-api-production-5b42.up.railway.app/api/organizations/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_your_company",
    "name": "Your Company",
    "metadata": {"tier": "premium"}
  }'

# Create model groups
curl -X POST https://saas-api-production-5b42.up.railway.app/api/model-groups/create \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "ChatAgent",
    "display_name": "Chat Agent",
    "description": "General purpose chat",
    "models": [
      {"model_name": "gpt-3.5-turbo", "priority": 0},
      {"model_name": "gpt-4", "priority": 1}
    ]
  }'

# Create team with credits
curl -X POST https://saas-api-production-5b42.up.railway.app/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_your_company",
    "team_id": "team_engineering",
    "team_alias": "Engineering Team",
    "model_groups": ["ChatAgent"],
    "credits_allocated": 1000,
    "metadata": {"department": "engineering"}
  }'
```

### 2. Make LLM Calls

```bash
# Create a job
JOB_ID=$(curl -s -X POST https://saas-api-production-5b42.up.railway.app/api/jobs/create \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "team_engineering",
    "user_id": "user_123",
    "job_type": "document_analysis",
    "metadata": {"document_id": "doc_456"}
  }' | jq -r '.job_id')

# Make LLM call
curl -X POST "https://saas-api-production-5b42.up.railway.app/api/jobs/$JOB_ID/llm-call" \
  -H "Content-Type: application/json" \
  -d '{
    "model_group": "ChatAgent",
    "messages": [
      {"role": "user", "content": "Analyze this document..."}
    ],
    "purpose": "initial_analysis"
  }'

# Complete job (deducts credit)
curl -X POST "https://saas-api-production-5b42.up.railway.app/api/jobs/$JOB_ID/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "metadata": {"result": "success"}
  }'
```

---

## API Endpoints

### Organizations API

#### Create Organization
```http
POST /api/organizations/create
```

**Request Body:**
```json
{
  "organization_id": "org_unique_id",
  "name": "Organization Name",
  "metadata": {}  // Optional custom metadata
}
```

**Response:**
```json
{
  "organization_id": "org_unique_id",
  "name": "Organization Name",
  "status": "active",
  "metadata": {},
  "created_at": "2025-10-13T12:00:00",
  "updated_at": "2025-10-13T12:00:00"
}
```

#### Get Organization
```http
GET /api/organizations/{organization_id}
```

#### List Organization Teams
```http
GET /api/organizations/{organization_id}/teams
```

#### Get Organization Usage
```http
GET /api/organizations/{organization_id}/usage?period=2025-10
```

---

### Model Groups API

#### Create Model Group
```http
POST /api/model-groups/create
```

**Request Body:**
```json
{
  "group_name": "ResumeAgent",
  "display_name": "Resume Analysis Agent",
  "description": "Specialized for resume parsing and analysis",
  "models": [
    {
      "model_name": "gpt-3.5-turbo",
      "priority": 0,
      "config": {}
    },
    {
      "model_name": "gpt-4",
      "priority": 1,
      "config": {}
    }
  ],
  "metadata": {}
}
```

**Models are tried in priority order (0 = first). If primary fails, fallback to next priority.**

**Response:**
```json
{
  "model_group_id": "uuid",
  "group_name": "ResumeAgent",
  "display_name": "Resume Analysis Agent",
  "description": "...",
  "status": "active",
  "models": [...],
  "created_at": "2025-10-13T12:00:00"
}
```

#### List Model Groups
```http
GET /api/model-groups
```

#### Get Model Group
```http
GET /api/model-groups/{group_name}
```

#### Get Model Group Models
```http
GET /api/model-groups/{group_name}/models
```

---

### Teams API

#### Create Team
```http
POST /api/teams/create
```

**Request Body:**
```json
{
  "organization_id": "org_unique_id",
  "team_id": "team_engineering",
  "team_alias": "Engineering Team",
  "model_groups": ["ResumeAgent", "ChatAgent"],
  "credits_allocated": 1000,
  "metadata": {
    "department": "engineering",
    "cost_center": "CC-001"
  }
}
```

**What happens:**
1. Creates team in LiteLLM with budget (credits × $0.10)
2. Generates virtual API key for team
3. Assigns model groups to team
4. Allocates credits

**Response:**
```json
{
  "team_id": "team_engineering",
  "organization_id": "org_unique_id",
  "model_groups": ["ResumeAgent", "ChatAgent"],
  "credits_allocated": 1000,
  "credits_remaining": 1000,
  "virtual_key": "sk-xxx...",
  "message": "Team created successfully with LiteLLM integration"
}
```

#### Get Team
```http
GET /api/teams/{team_id}
```

**Response:**
```json
{
  "team_id": "team_engineering",
  "organization_id": "org_unique_id",
  "credits": {
    "credits_allocated": 1000,
    "credits_used": 45,
    "credits_remaining": 955
  },
  "model_groups": ["ResumeAgent", "ChatAgent"]
}
```

#### Assign Model Groups to Team
```http
PUT /api/teams/{team_id}/model-groups
```

**Request Body:**
```json
["ResumeAgent", "ChatAgent", "NewAgent"]
```

---

### Credits API

#### Get Credit Balance
```http
GET /api/credits/teams/{team_id}/balance
```

**Response:**
```json
{
  "team_id": "team_engineering",
  "credits_allocated": 1000,
  "credits_used": 45,
  "credits_remaining": 955,
  "credit_limit": null,
  "auto_refill": false
}
```

#### Add Credits
```http
POST /api/credits/teams/{team_id}/add
```

**Request Body:**
```json
{
  "credits_amount": 500,
  "reason": "Monthly refill",
  "metadata": {"invoice_id": "INV-123"}
}
```

#### Check Credit Availability
```http
POST /api/credits/teams/{team_id}/check
```

**Request Body:**
```json
{
  "credits_required": 1
}
```

**Response:**
```json
{
  "available": true,
  "credits_remaining": 955
}
```

#### Get Credit Transactions
```http
GET /api/credits/teams/{team_id}/transactions?limit=50&offset=0
```

**Response:**
```json
{
  "team_id": "team_engineering",
  "total_transactions": 46,
  "transactions": [
    {
      "transaction_id": "uuid",
      "team_id": "team_engineering",
      "transaction_type": "deduction",
      "credits_amount": 1,
      "balance_after": 955,
      "reason": "Job document_analysis completed successfully",
      "job_id": "uuid",
      "created_at": "2025-10-13T12:30:00"
    }
  ]
}
```

---

### Jobs API

#### Create Job
```http
POST /api/jobs/create
```

**Request Body:**
```json
{
  "team_id": "team_engineering",
  "user_id": "user_123",  // Optional: your app's user ID
  "job_type": "document_analysis",
  "metadata": {
    "document_id": "doc_456",
    "filename": "resume.pdf"
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "created_at": "2025-10-13T12:00:00"
}
```

#### Make LLM Call
```http
POST /api/jobs/{job_id}/llm-call
```

**Request Body:**
```json
{
  "model_group": "ResumeAgent",
  "messages": [
    {"role": "system", "content": "You are a resume analyzer."},
    {"role": "user", "content": "Analyze this resume: ..."}
  ],
  "purpose": "initial_parsing",  // Optional: for tracking
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "call_id": "uuid",
  "response": {
    "content": "Here is the analysis...",
    "finish_reason": "stop"
  },
  "metadata": {
    "tokens_used": 450,
    "latency_ms": 1250,
    "model_group": "ResumeAgent"
  }
}
```

**Note:** Model and costs are NOT exposed to clients. You track via `model_group`.

#### Complete Job
```http
POST /api/jobs/{job_id}/complete
```

**Request Body:**
```json
{
  "status": "completed",  // or "failed"
  "metadata": {
    "result": "success",
    "output_file": "result.json"
  },
  "error_message": null  // If failed, provide reason
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "completed_at": "2025-10-13T12:05:00",
  "costs": {
    "total_calls": 3,
    "successful_calls": 3,
    "failed_calls": 0,
    "total_tokens": 1250,
    "total_cost_usd": 0.0025,
    "avg_latency_ms": 1100,
    "credit_applied": true,
    "credits_remaining": 999
  },
  "calls": [
    {
      "call_id": "uuid",
      "purpose": "initial_parsing",
      "model_group": "ResumeAgent",
      "tokens": 450,
      "latency_ms": 1250,
      "error": null
    }
  ]
}
```

**Credit Deduction Logic:**
- Credits are ONLY deducted if:
  1. Job status is "completed" (not "failed")
  2. No failed LLM calls in the job
  3. Credit hasn't already been applied
- 1 credit per successful job, regardless of number of LLM calls

#### Get Job
```http
GET /api/jobs/{job_id}
```

#### List Team Jobs
```http
GET /api/teams/{team_id}/jobs?limit=100&offset=0&status=completed
```

---

## Integration Flow

### Recommended Integration Pattern

```javascript
// 1. Initialize with team context
const teamId = "team_engineering";
const userId = getCurrentUserId();

// 2. Create job for tracking
const job = await fetch(`${API_BASE}/api/jobs/create`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    team_id: teamId,
    user_id: userId,
    job_type: 'document_analysis',
    metadata: {
      task_id: taskId,
      document_name: document.name
    }
  })
}).then(r => r.json());

const jobId = job.job_id;

try {
  // 3. Make one or more LLM calls
  const parseResult = await fetch(`${API_BASE}/api/jobs/${jobId}/llm-call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model_group: 'ResumeAgent',
      messages: [
        { role: 'system', content: 'You are a resume parser.' },
        { role: 'user', content: documentContent }
      ],
      purpose: 'parsing'
    })
  }).then(r => r.json());

  const analysisResult = await fetch(`${API_BASE}/api/jobs/${jobId}/llm-call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model_group: 'ResumeAgent',
      messages: [
        { role: 'user', content: 'Analyze: ' + parseResult.response.content }
      ],
      purpose: 'analysis'
    })
  }).then(r => r.json());

  // 4. Complete job successfully
  const completion = await fetch(`${API_BASE}/api/jobs/${jobId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      status: 'completed',
      metadata: {
        result: 'success',
        calls_made: 2
      }
    })
  }).then(r => r.json());

  console.log(`Credits remaining: ${completion.costs.credits_remaining}`);

} catch (error) {
  // 5. Complete job as failed (no credit deduction)
  await fetch(`${API_BASE}/api/jobs/${jobId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      status: 'failed',
      error_message: error.message
    })
  });
}
```

---

## Code Examples

### Python Integration

```python
import requests
from typing import Dict, List, Any

class SaasLLMClient:
    def __init__(self, base_url: str, team_id: str):
        self.base_url = base_url
        self.team_id = team_id

    def create_job(self, job_type: str, user_id: str = None, metadata: Dict = None) -> str:
        """Create a new job and return job_id"""
        response = requests.post(
            f"{self.base_url}/api/jobs/create",
            json={
                "team_id": self.team_id,
                "user_id": user_id,
                "job_type": job_type,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return response.json()["job_id"]

    def llm_call(
        self,
        job_id: str,
        model_group: str,
        messages: List[Dict],
        purpose: str = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Make an LLM call within a job context"""
        response = requests.post(
            f"{self.base_url}/api/jobs/{job_id}/llm-call",
            json={
                "model_group": model_group,
                "messages": messages,
                "purpose": purpose,
                "temperature": temperature
            }
        )
        response.raise_for_status()
        return response.json()

    def complete_job(
        self,
        job_id: str,
        status: str = "completed",
        metadata: Dict = None,
        error_message: str = None
    ) -> Dict[str, Any]:
        """Complete a job and get cost summary"""
        response = requests.post(
            f"{self.base_url}/api/jobs/{job_id}/complete",
            json={
                "status": status,
                "metadata": metadata or {},
                "error_message": error_message
            }
        )
        response.raise_for_status()
        return response.json()

    def get_credits(self) -> Dict[str, Any]:
        """Get team credit balance"""
        response = requests.get(
            f"{self.base_url}/api/credits/teams/{self.team_id}/balance"
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SaasLLMClient(
    base_url="https://saas-api-production-5b42.up.railway.app",
    team_id="team_engineering"
)

# Document analysis workflow
job_id = client.create_job(
    job_type="document_analysis",
    user_id="user_123",
    metadata={"document_id": "doc_456"}
)

try:
    # Parse document
    parse_result = client.llm_call(
        job_id=job_id,
        model_group="ResumeAgent",
        messages=[
            {"role": "system", "content": "You are a resume parser."},
            {"role": "user", "content": document_content}
        ],
        purpose="parsing"
    )

    # Analyze parsed content
    analysis_result = client.llm_call(
        job_id=job_id,
        model_group="ResumeAgent",
        messages=[
            {"role": "user", "content": f"Analyze: {parse_result['response']['content']}"}
        ],
        purpose="analysis"
    )

    # Complete successfully
    completion = client.complete_job(
        job_id=job_id,
        status="completed",
        metadata={"result": "success"}
    )

    print(f"Job completed. Credits remaining: {completion['costs']['credits_remaining']}")

except Exception as e:
    # Complete as failed (no credit charge)
    client.complete_job(
        job_id=job_id,
        status="failed",
        error_message=str(e)
    )
```

### Node.js Integration

```javascript
class SaasLLMClient {
  constructor(baseUrl, teamId) {
    this.baseUrl = baseUrl;
    this.teamId = teamId;
  }

  async createJob(jobType, userId = null, metadata = {}) {
    const response = await fetch(`${this.baseUrl}/api/jobs/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_id: this.teamId,
        user_id: userId,
        job_type: jobType,
        metadata
      })
    });

    if (!response.ok) throw new Error(`Job creation failed: ${await response.text()}`);
    const data = await response.json();
    return data.job_id;
  }

  async llmCall(jobId, modelGroup, messages, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/llm-call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_group: modelGroup,
        messages,
        purpose: options.purpose,
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens
      })
    });

    if (!response.ok) throw new Error(`LLM call failed: ${await response.text()}`);
    return await response.json();
  }

  async completeJob(jobId, status = 'completed', metadata = {}, errorMessage = null) {
    const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status,
        metadata,
        error_message: errorMessage
      })
    });

    if (!response.ok) throw new Error(`Job completion failed: ${await response.text()}`);
    return await response.json();
  }

  async getCredits() {
    const response = await fetch(`${this.baseUrl}/api/credits/teams/${this.teamId}/balance`);
    if (!response.ok) throw new Error(`Failed to get credits: ${await response.text()}`);
    return await response.json();
  }
}

// Usage
const client = new SaasLLMClient(
  'https://saas-api-production-5b42.up.railway.app',
  'team_engineering'
);

async function analyzeDocument(documentContent) {
  const jobId = await client.createJob('document_analysis', 'user_123', {
    document_id: 'doc_456'
  });

  try {
    const parseResult = await client.llmCall(
      jobId,
      'ResumeAgent',
      [
        { role: 'system', content: 'You are a resume parser.' },
        { role: 'user', content: documentContent }
      ],
      { purpose: 'parsing' }
    );

    const analysisResult = await client.llmCall(
      jobId,
      'ResumeAgent',
      [{ role: 'user', content: `Analyze: ${parseResult.response.content}` }],
      { purpose: 'analysis' }
    );

    const completion = await client.completeJob(jobId, 'completed', {
      result: 'success'
    });

    console.log(`Credits remaining: ${completion.costs.credits_remaining}`);
    return analysisResult.response.content;

  } catch (error) {
    await client.completeJob(jobId, 'failed', {}, error.message);
    throw error;
  }
}
```

---

## Best Practices

### 1. Job Lifecycle Management

✅ **DO:**
- Always create a job before making LLM calls
- Complete jobs even if they fail (prevents zombie jobs)
- Use meaningful `job_type` and `purpose` for tracking
- Store your app's task/request ID in job metadata

❌ **DON'T:**
- Make LLM calls without a job context
- Leave jobs incomplete (complete as "failed" if errors occur)
- Reuse job IDs across multiple business operations

### 2. Credit Management

✅ **DO:**
- Check credit balance before starting expensive operations
- Monitor credit usage via transactions endpoint
- Set up alerts when credits are low
- Use the `check` endpoint to verify sufficient credits

❌ **DON'T:**
- Assume credits are unlimited
- Start jobs without checking credit availability
- Forget to handle insufficient credits errors

### 3. Model Groups

✅ **DO:**
- Create model groups for different use cases ("ChatAgent", "AnalysisAgent")
- Use priority ordering for fallbacks (cheaper models first)
- Assign only necessary model groups to teams
- Use descriptive names that match your business logic

❌ **DON'T:**
- Give all teams access to all model groups
- Use generic names like "Group1", "Group2"
- Skip fallback models (always have at least 2)

### 4. Error Handling

```python
try:
    result = client.llm_call(job_id, "ChatAgent", messages)
except requests.HTTPError as e:
    if e.response.status_code == 403:
        # Team doesn't have access to this model group
        handle_access_denied()
    elif e.response.status_code == 404:
        # Job or team not found
        handle_not_found()
    elif e.response.status_code == 500:
        # LLM call failed or insufficient credits
        error_detail = e.response.json()
        handle_llm_error(error_detail)
```

### 5. Metadata Usage

Use metadata fields to bridge your app's context:

```python
# Job metadata - link to your app's entities
client.create_job(
    job_type="resume_analysis",
    metadata={
        "task_id": "task_123",              # Your app's task ID
        "user_email": "john@example.com",   # For support
        "document_name": "resume.pdf",       # User-facing name
        "priority": "high",                  # For your tracking
        "source": "upload"                   # How it was created
    }
)

# Completion metadata - record outcomes
client.complete_job(
    job_id=job_id,
    status="completed",
    metadata={
        "output_file": "results/analysis_123.json",
        "confidence_score": 0.95,
        "warnings": ["Low quality image"]
    }
)
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request format |
| 403 | Forbidden | Team lacks access to model group |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | LLM error or system issue |

### Common Errors

#### Insufficient Credits
```json
{
  "detail": "Insufficient credits. Required: 1, Available: 0"
}
```
**Solution:** Add credits to team or notify user

#### Model Group Access Denied
```json
{
  "detail": "Team 'team_xxx' does not have access to model group 'ChatAgent'"
}
```
**Solution:** Assign model group to team or use different group

#### LLM Call Failed
```json
{
  "detail": "LLM call failed: Rate limit exceeded"
}
```
**Solution:** Implement retry with exponential backoff

### Retry Strategy

```python
import time
from requests.exceptions import RequestException

def llm_call_with_retry(client, job_id, model_group, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.llm_call(job_id, model_group, messages)
        except RequestException as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff
            wait_time = 2 ** attempt
            print(f"Retry {attempt + 1} after {wait_time}s...")
            time.sleep(wait_time)
```

---

## Monitoring & Analytics

### Check Team Usage

```bash
# Get current month usage
curl "https://saas-api-production-5b42.up.railway.app/api/teams/team_engineering/usage?period=2025-10"
```

**Response:**
```json
{
  "team_id": "team_engineering",
  "period": "2025-10",
  "summary": {
    "total_jobs": 150,
    "successful_jobs": 145,
    "failed_jobs": 5,
    "total_cost_usd": 12.50,
    "total_tokens": 450000,
    "avg_cost_per_job": 0.0833
  },
  "job_types": {
    "document_analysis": {
      "count": 100,
      "cost_usd": 8.50
    },
    "chat_session": {
      "count": 50,
      "cost_usd": 4.00
    }
  }
}
```

### Track Credit Transactions

```bash
curl "https://saas-api-production-5b42.up.railway.app/api/credits/teams/team_engineering/transactions?limit=10"
```

---

## Support

### API Issues
- Check service health: `GET /health`
- Review your request format matches docs
- Verify team has access to model groups
- Check credit balance

### Questions
- GitHub Issues: https://github.com/GittieLabs/SaasLiteLLM/issues

---

## Changelog

### v2.0.0 (Current)
- Full LiteLLM integration
- Virtual key generation per team
- Credit-based billing
- Model group resolution
- Multi-tenant support

### v1.0.0
- Initial job tracking API
- Basic cost tracking

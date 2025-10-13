# SaaS LiteLLM API Integration Guide

Complete guide for integrating the SaaS LiteLLM API into your projects.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Understanding Jobs & Credits](#understanding-jobs--credits)
- [Integration Patterns](#integration-patterns)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Integration Flow](#integration-flow)
- [Complete Example: Resume Parsing Workflow](#complete-example-resume-parsing-workflow)
- [Code Examples](#code-examples)
- [Model Resolution API](#model-resolution-api-recommended-for-openai-sdk)
- [Direct OpenAI-Compatible Integration (Pattern B)](#direct-openai-compatible-integration-pattern-b)
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
- **Secure authentication**: All API calls require virtual key authentication

### Architecture

```
Your SaaS App → SaaS API → LiteLLM Proxy → LLM Providers
                    ↓
                PostgreSQL (tracking, billing)
```

---

## Authentication

All API endpoints (except organization and model group creation) require authentication using your team's virtual API key.

### Getting Your Virtual Key

When you create a team, the API returns a `virtual_key`:

```bash
curl -X POST https://llm-saas.usegittie.com/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_your_company",
    "team_id": "team_engineering",
    "team_alias": "Engineering Team",
    "model_groups": ["ChatAgent"],
    "credits_allocated": 1000
  }'
```

**Response:**
```json
{
  "team_id": "team_engineering",
  "virtual_key": "sk-xxx...",
  "credits_allocated": 1000,
  "credits_remaining": 1000
}
```

**Important:** Save the `virtual_key` - this is your team's API key for all subsequent requests.

### Using the Virtual Key

Include the virtual key in the `Authorization` header for all API calls:

```http
Authorization: Bearer sk-xxx...
```

### Example API Calls with Authentication

```bash
# Create a job (with authentication)
curl -X POST https://llm-saas.usegittie.com/api/jobs/create \
  -H "Authorization: Bearer sk-xxx..." \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "team_engineering",
    "job_type": "document_analysis",
    "metadata": {}
  }'

# Make an LLM call (with authentication)
curl -X POST "https://llm-saas.usegittie.com/api/jobs/{job_id}/llm-call" \
  -H "Authorization: Bearer sk-xxx..." \
  -H "Content-Type: application/json" \
  -d '{
    "model_group": "ChatAgent",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Check credit balance (with authentication)
curl -X GET "https://llm-saas.usegittie.com/api/credits/teams/team_engineering/balance" \
  -H "Authorization: Bearer sk-xxx..."
```

### Security Notes

✅ **DO:**
- Store virtual keys securely (environment variables, secrets manager)
- Never commit keys to version control
- Use different keys for different teams/environments
- Rotate keys periodically

❌ **DON'T:**
- Hardcode keys in your application code
- Share keys across multiple teams
- Expose keys in client-side JavaScript

### Authentication Errors

**Missing Authorization Header:**
```json
{
  "detail": "Missing Authorization header. Expected: 'Authorization: Bearer sk-xxx...'"
}
```

**Invalid API Key:**
```json
{
  "detail": "Invalid API key"
}
```

**Wrong Team:**
```json
{
  "detail": "API key does not belong to team 'team_xxx'"
}
```

---

## Understanding Jobs & Credits

### What is a Job?

A **Job** is a logical grouping of related LLM calls that represent a single business operation or workflow. Instead of tracking and billing individual LLM calls, the platform groups them into jobs for simplified cost management.

### Real-World Example: Resume Parsing

Your resume analysis tool performs multiple LLM operations as part of one workflow:

```
Job: "resume_analysis"
├── LLM Call 1: Parse resume text
├── LLM Call 2: Compare requirements with candidate qualifications
└── LLM Call 3: Generate executive summary

Result: 1 Job = 1 Credit charged (not 3 credits)
```

**Key Benefits:**
- **Simplified Billing**: Pay per job completion, not per LLM call
- **Cost Aggregation**: Track total cost across multiple calls
- **Usage Analytics**: Understand which workflows are expensive
- **Failure Handling**: Failed jobs don't consume credits

### Job Lifecycle

```javascript
// 1. CREATE JOB - Start tracking
const job = await saas_api.createJob({
  team_id: "team_engineering",
  job_type: "resume_analysis",
  metadata: { document_id: "resume_123" }
});
// Returns: { job_id: "uuid", status: "pending" }

// 2. MAKE LLM CALLS - All associated with job_id
await saas_api.llmCall(job.job_id, "ResumeAgent", parse_messages);
await saas_api.llmCall(job.job_id, "ResumeAgent", compare_messages);
await saas_api.llmCall(job.job_id, "ResumeAgent", summary_messages);

// 3. COMPLETE JOB - Triggers credit deduction
const result = await saas_api.completeJob(job.job_id, "completed");
// Returns: {
//   costs: {
//     total_calls: 3,
//     total_cost_usd: 0.0045,
//     credit_applied: true,    // 1 credit deducted
//     credits_remaining: 999
//   }
// }
```

### Credit Deduction Rules

Credits are **ONLY** deducted when:
1. ✅ Job status is "completed" (not "failed")
2. ✅ All LLM calls succeeded
3. ✅ Credit hasn't already been applied

**1 Job = 1 Credit**, regardless of:
- Number of LLM calls (could be 1 or 100)
- Actual USD cost (tracked separately for analytics)
- Models used (different models in same job)
- Time duration (seconds or hours)

### Job Architecture

```
┌─────────────┐
│ Your Client │
└──────┬──────┘
       │ 1. Create job
       │    (get job_id)
       ▼
┌─────────────────────┐
│    SaaS API         │
│  ┌───────────────┐  │
│  │ Job: uuid     │  │
│  │ Status: pending│ │
│  │ Calls: []     │  │
│  └───────────────┘  │
└──────┬──────────────┘
       │ 2. Make LLM calls
       │    (SaaS API tracks each call under job_id)
       ▼
┌─────────────────────┐
│  LiteLLM Proxy      │
│  (no knowledge of   │
│   jobs or job_id)   │
└──────┬──────────────┘
       │ 3. Execute LLM calls
       ▼
┌─────────────────────┐
│  OpenAI, Anthropic  │
│  Google, etc.       │
└─────────────────────┘
```

**Important**: The `job_id` lives in the SaaS API database, NOT passed to LiteLLM proxy. The SaaS API handles:
- Tracking all calls under the job_id
- Calling LiteLLM on your behalf
- Aggregating costs per job
- Deducting credits on completion

---

## Integration Patterns

There are **two ways** to integrate with the SaaS LiteLLM API:

### Pattern A: Job-Based API 🌟 RECOMMENDED

**Client → SaaS API (with job_id) → LiteLLM Proxy → LLM Providers**

This is the **primary integration pattern** for the SaaS LLM platform. It's specifically designed for multi-step workflows where you need to:
- Group multiple LLM calls into logical business operations
- Track costs per workflow (not per call)
- Simplify billing (1 credit per job, not per call)
- Aggregate usage analytics by workflow type

**Key Features:**
- ✅ **Job-based tracking**: Create job_id, associate all calls with it
- ✅ **Simple credit model**: 1 credit per completed job (regardless of # of calls)
- ✅ **Cost aggregation**: View total USD cost across all calls in a job
- ✅ **Model group abstraction**: Use semantic names ("ResumeAgent") not models
- ✅ **Automatic fallbacks**: SaaS API handles model failover
- ✅ **Usage analytics**: Track which workflows are expensive

**Perfect for:**
- ✅ Resume parsing (parse → compare → summarize)
- ✅ Document analysis (extract → classify → enrich)
- ✅ Chat workflows (intent → context → response → validation)
- ✅ Any multi-step LLM pipeline

**Architecture:**
The `job_id` is tracked in the SaaS API database. Your client passes job_id with each API call. The SaaS API:
1. Tracks all calls under that job_id
2. Calls LiteLLM proxy on your behalf
3. Aggregates costs and metrics
4. Deducts 1 credit when job completes successfully

### Pattern B: Direct OpenAI-Compatible Calls
**Client → LiteLLM Proxy directly**

- ✅ Use **actual model names** (e.g., "gpt-3.5-turbo", "gpt-4")
- ✅ Standard OpenAI SDK compatible
- ✅ Lower latency (no intermediate layer)
- ❌ No automatic credit tracking
- ❌ No job-based aggregation
- ❌ Manual fallback handling

**Use this for**: Simple single-shot calls, OpenAI SDK drop-in replacement, streaming responses

---

## Quick Start

### Base URL

```
Production: https://llm-saas.usegittie.com
```

### 1. Set Up Organization & Team

```bash
# Create organization
curl -X POST https://llm-saas.usegittie.com/api/organizations/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_your_company",
    "name": "Your Company",
    "metadata": {"tier": "premium"}
  }'

# Create model groups
curl -X POST https://llm-saas.usegittie.com/api/model-groups/create \
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
curl -X POST https://llm-saas.usegittie.com/api/teams/create \
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
# Set your virtual key from step 1
VIRTUAL_KEY="sk-xxx..."

# Create a job
JOB_ID=$(curl -s -X POST https://llm-saas.usegittie.com/api/jobs/create \
  -H "Authorization: Bearer $VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "team_engineering",
    "user_id": "user_123",
    "job_type": "document_analysis",
    "metadata": {"document_id": "doc_456"}
  }' | jq -r '.job_id')

# Make LLM call
curl -X POST "https://llm-saas.usegittie.com/api/jobs/$JOB_ID/llm-call" \
  -H "Authorization: Bearer $VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model_group": "ChatAgent",
    "messages": [
      {"role": "user", "content": "Analyze this document..."}
    ],
    "purpose": "initial_analysis"
  }'

# Complete job (deducts credit)
curl -X POST "https://llm-saas.usegittie.com/api/jobs/$JOB_ID/complete" \
  -H "Authorization: Bearer $VIRTUAL_KEY" \
  -H "Content-Type": application/json" \
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
const virtualKey = "sk-xxx...";  // Your team's virtual API key

const headers = {
  'Authorization': `Bearer ${virtualKey}`,
  'Content-Type': 'application/json'
};

// 2. Create job for tracking
const job = await fetch(`${API_BASE}/api/jobs/create`, {
  method: 'POST',
  headers,
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
    headers,
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
    headers,
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
    headers,
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
    headers,
    body: JSON.stringify({
      status: 'failed',
      error_message: error.message
    })
  });
}
```

---

## Complete Example: Resume Parsing Workflow

This example demonstrates the exact use case you mentioned: a resume analysis tool that performs parsing, requirements comparison, and executive summary generation as **one job = one credit**.

### Setup

```python
import requests
from typing import Dict, List

class ResumeAnalyzer:
    def __init__(self, base_url: str, team_id: str, virtual_key: str):
        self.base_url = base_url
        self.team_id = team_id
        self.virtual_key = virtual_key
        self.headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json"
        }

    def analyze_resume(self, resume_text: str, job_requirements: List[str]) -> Dict:
        """
        Complete resume analysis workflow: parse → compare → summarize
        3 LLM calls = 1 Job = 1 Credit
        """
        # Step 1: Create job
        job_response = requests.post(
            f"{self.base_url}/api/jobs/create",
            headers=self.headers,
            json={
                "team_id": self.team_id,
                "job_type": "resume_analysis",
                "metadata": {
                    "resume_length": len(resume_text),
                    "num_requirements": len(job_requirements)
                }
            }
        )
        job_id = job_response.json()["job_id"]
        print(f"✓ Created job: {job_id}")

        try:
            # Step 2: Parse resume (LLM Call #1)
            parse_response = requests.post(
                f"{self.base_url}/api/jobs/{job_id}/llm-call",
                headers=self.headers,
                json={
                    "model_group": "ResumeAgent",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a resume parser. Extract: name, email, skills, experience."
                        },
                        {
                            "role": "user",
                            "content": f"Parse this resume:\n\n{resume_text}"
                        }
                    ],
                    "purpose": "parsing"
                }
            )
            parsed_data = parse_response.json()["response"]["content"]
            print(f"✓ Parsed resume (Call 1/3)")

            # Step 3: Compare requirements (LLM Call #2)
            compare_response = requests.post(
                f"{self.base_url}/api/jobs/{job_id}/llm-call",
                headers=self.headers,
                json={
                    "model_group": "ResumeAgent",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Compare candidate qualifications against job requirements."
                        },
                        {
                            "role": "user",
                            "content": f"Candidate: {parsed_data}\n\nRequirements: {', '.join(job_requirements)}\n\nDo they meet requirements?"
                        }
                    ],
                    "purpose": "requirements_comparison"
                }
            )
            comparison_result = compare_response.json()["response"]["content"]
            print(f"✓ Compared requirements (Call 2/3)")

            # Step 4: Generate executive summary (LLM Call #3)
            summary_response = requests.post(
                f"{self.base_url}/api/jobs/{job_id}/llm-call",
                headers=self.headers,
                json={
                    "model_group": "ResumeAgent",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Create a concise executive summary for hiring managers."
                        },
                        {
                            "role": "user",
                            "content": f"Resume: {parsed_data}\n\nFit Analysis: {comparison_result}\n\nCreate 3-sentence summary."
                        }
                    ],
                    "purpose": "executive_summary"
                }
            )
            exec_summary = summary_response.json()["response"]["content"]
            print(f"✓ Generated summary (Call 3/3)")

            # Step 5: Complete job (triggers 1 credit deduction)
            completion_response = requests.post(
                f"{self.base_url}/api/jobs/{job_id}/complete",
                headers=self.headers,
                json={
                    "status": "completed",
                    "metadata": {
                        "result": "success",
                        "summary_length": len(exec_summary)
                    }
                }
            )
            completion_data = completion_response.json()

            print(f"\n✅ Job completed!")
            print(f"   Total calls: {completion_data['costs']['total_calls']}")
            print(f"   Total USD cost: ${completion_data['costs']['total_cost_usd']:.4f}")
            print(f"   Credit charged: {completion_data['costs']['credit_applied']}")
            print(f"   Credits remaining: {completion_data['costs']['credits_remaining']}")

            return {
                "parsed_data": parsed_data,
                "comparison": comparison_result,
                "executive_summary": exec_summary,
                "costs": completion_data["costs"]
            }

        except Exception as e:
            # If anything fails, mark job as failed (no credit charge)
            requests.post(
                f"{self.base_url}/api/jobs/{job_id}/complete",
                headers=self.headers,
                json={
                    "status": "failed",
                    "error_message": str(e)
                }
            )
            print(f"❌ Job failed: {e} (no credit charged)")
            raise

# Usage
analyzer = ResumeAnalyzer(
    base_url="https://llm-saas.usegittie.com",
    team_id="team_hr",
    virtual_key="sk-xxx..."  # Your team's virtual API key
)

result = analyzer.analyze_resume(
    resume_text="John Doe | john@example.com | Software Engineer with 5 years Python...",
    job_requirements=["Python", "REST APIs", "PostgreSQL", "5+ years experience"]
)

print("\n" + "="*50)
print("EXECUTIVE SUMMARY")
print("="*50)
print(result["executive_summary"])
```

### Output Example

```
✓ Created job: 7f3d9a8b-4c21-4e89-b5d3-2a1c8f6e9b0d
✓ Parsed resume (Call 1/3)
✓ Compared requirements (Call 2/3)
✓ Generated summary (Call 3/3)

✅ Job completed!
   Total calls: 3
   Total USD cost: $0.0045
   Credit charged: True
   Credits remaining: 99

==================================================
EXECUTIVE SUMMARY
==================================================
John Doe is a strong candidate with 5 years of Python experience
and proven REST API development skills. He meets all core requirements
including PostgreSQL expertise. Recommended for interview.
```

### Key Takeaways

1. **3 LLM calls = 1 credit**: You're only charged once for the complete workflow
2. **Cost tracking**: See actual USD cost ($0.0045) vs credit charged (1)
3. **Job metadata**: Track custom context (resume length, requirements count)
4. **Purpose tracking**: Each call labeled (parsing, requirements_comparison, executive_summary)
5. **Failure handling**: If any call fails, complete as "failed" → no credit charged
6. **Cost visibility**: View all calls and their costs in the completion response

### Viewing Job Details Later

```bash
# Get full job details with all calls
curl "https://llm-saas.usegittie.com/api/jobs/7f3d9a8b-4c21-4e89-b5d3-2a1c8f6e9b0d"
```

**Response shows all calls:**
```json
{
  "job_id": "7f3d9a8b-4c21-4e89-b5d3-2a1c8f6e9b0d",
  "status": "completed",
  "job_type": "resume_analysis",
  "calls": [
    {
      "purpose": "parsing",
      "tokens": 450,
      "cost_usd": 0.0015,
      "latency_ms": 1200
    },
    {
      "purpose": "requirements_comparison",
      "tokens": 380,
      "cost_usd": 0.0013,
      "latency_ms": 1100
    },
    {
      "purpose": "executive_summary",
      "tokens": 420,
      "cost_usd": 0.0017,
      "latency_ms": 1050
    }
  ],
  "total_cost_usd": 0.0045,
  "credit_applied": true
}
```

This is exactly how your resume parsing tool should integrate!

---

## Code Examples

### Python Integration

```python
import requests
from typing import Dict, List, Any

class SaasLLMClient:
    def __init__(self, base_url: str, team_id: str, virtual_key: str):
        self.base_url = base_url
        self.team_id = team_id
        self.virtual_key = virtual_key
        self.headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json"
        }

    def create_job(self, job_type: str, user_id: str = None, metadata: Dict = None) -> str:
        """Create a new job and return job_id"""
        response = requests.post(
            f"{self.base_url}/api/jobs/create",
            headers=self.headers,
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
            headers=self.headers,
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
            headers=self.headers,
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
            f"{self.base_url}/api/credits/teams/{self.team_id}/balance",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SaasLLMClient(
    base_url="https://llm-saas.usegittie.com",
    team_id="team_engineering",
    virtual_key="sk-xxx..."  # Your team's virtual API key
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
  constructor(baseUrl, teamId, virtualKey) {
    this.baseUrl = baseUrl;
    this.teamId = teamId;
    this.virtualKey = virtualKey;
    this.headers = {
      'Authorization': `Bearer ${virtualKey}`,
      'Content-Type': 'application/json'
    };
  }

  async createJob(jobType, userId = null, metadata = {}) {
    const response = await fetch(`${this.baseUrl}/api/jobs/create`, {
      method: 'POST',
      headers: this.headers,
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
      headers: this.headers,
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
      headers: this.headers,
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
    const response = await fetch(`${this.baseUrl}/api/credits/teams/${this.teamId}/balance`, {
      headers: this.headers
    });
    if (!response.ok) throw new Error(`Failed to get credits: ${await response.text()}`);
    return await response.json();
  }
}

// Usage
const client = new SaasLLMClient(
  'https://llm-saas.usegittie.com',
  'team_engineering',
  'sk-xxx...'  // Your team's virtual API key
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

## Model Resolution API (Recommended for OpenAI SDK)

**The cleanest pattern for OpenAI SDK integration:** Let the API tell you which model to use!

### How It Works

1. **At session/job start**, ask the API: "What model should I use for ResumeAgent?"
2. **Cache the model name** for your session/job duration
3. **Use the model name** in OpenAI SDK calls
4. **Centralized control**: You manage model versions without client code changes

### Get Model for Agent Type

```bash
GET /api/model-groups/{group_name}/resolve?team_id=team_engineering
```

**Example Request:**
```bash
curl "https://llm-saas.usegittie.com/api/model-groups/ResumeAgent/resolve?team_id=team_engineering"
```

**Response:**
```json
{
  "group_name": "ResumeAgent",
  "primary_model": "gpt-4o",
  "fallback_models": ["gpt-4-turbo", "gpt-3.5-turbo"],
  "team_has_access": true
}
```

### Python Implementation

```python
from openai import OpenAI
import requests

class AgentModelClient:
    def __init__(self, saas_api_url, llm_proxy_url, team_id, virtual_key):
        self.saas_api_url = saas_api_url
        self.team_id = team_id
        self.virtual_key = virtual_key

        # Initialize OpenAI client with LiteLLM proxy
        self.openai = OpenAI(
            api_key=virtual_key,
            base_url=llm_proxy_url
        )

        # Cache for resolved models (per session)
        self.model_cache = {}

    def get_model_for_agent(self, agent_type: str) -> str:
        """
        Resolve agent type to actual model name.
        Caches result for session duration.
        """
        if agent_type not in self.model_cache:
            response = requests.get(
                f"{self.saas_api_url}/api/model-groups/{agent_type}/resolve",
                params={"team_id": self.team_id}
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("team_has_access"):
                raise PermissionError(f"Team doesn't have access to {agent_type}")

            self.model_cache[agent_type] = data["primary_model"]

        return self.model_cache[agent_type]

    def chat(self, agent_type: str, messages: list):
        """
        Make a chat completion using the agent's resolved model.
        """
        model = self.get_model_for_agent(agent_type)

        return self.openai.chat.completions.create(
            model=model,  # Actual model name from API
            messages=messages
        )

# Usage
client = AgentModelClient(
    saas_api_url="https://llm-saas.usegittie.com",
    llm_proxy_url="https://llm-proxy.usegittie.com",
    team_id="team_engineering",
    virtual_key="sk-xxx..."
)

# Client never needs to know actual model names!
response = client.chat(
    agent_type="ResumeAgent",  # Agent type, not model name
    messages=[
        {"role": "system", "content": "You are a resume analyzer."},
        {"role": "user", "content": "Analyze this resume..."}
    ]
)

print(response.choices[0].message.content)

# Model is cached for session - no additional API calls
response2 = client.chat("ResumeAgent", other_messages)
```

### Node.js Implementation

```javascript
import OpenAI from 'openai';

class AgentModelClient {
  constructor(saasApiUrl, llmProxyUrl, teamId, virtualKey) {
    this.saasApiUrl = saasApiUrl;
    this.teamId = teamId;
    this.virtualKey = virtualKey;

    // Initialize OpenAI client with LiteLLM proxy
    this.openai = new OpenAI({
      apiKey: virtualKey,
      baseURL: llmProxyUrl
    });

    // Cache for resolved models
    this.modelCache = {};
  }

  async getModelForAgent(agentType) {
    if (!this.modelCache[agentType]) {
      const response = await fetch(
        `${this.saasApiUrl}/api/model-groups/${agentType}/resolve?team_id=${this.teamId}`
      );

      if (!response.ok) throw new Error(`Failed to resolve ${agentType}`);

      const data = await response.json();

      if (!data.team_has_access) {
        throw new Error(`Team doesn't have access to ${agentType}`);
      }

      this.modelCache[agentType] = data.primary_model;
    }

    return this.modelCache[agentType];
  }

  async chat(agentType, messages) {
    const model = await this.getModelForAgent(agentType);

    return await this.openai.chat.completions.create({
      model,  // Actual model name from API
      messages
    });
  }
}

// Usage
const client = new AgentModelClient(
  'https://llm-saas.usegittie.com',
  'https://llm-proxy.usegittie.com',
  'team_engineering',
  'sk-xxx...'
);

// Clean agent-based API
const response = await client.chat('ResumeAgent', [
  { role: 'system', content: 'You are a resume analyzer.' },
  { role: 'user', content: 'Analyze this resume...' }
]);

console.log(response.choices[0].message.content);
```

### Benefits

✅ **Centralized Model Management**
- Change "ResumeAgent" from gpt-4 → gpt-4o without updating client code
- Clients only reference agent types, not model versions

✅ **Access Control**
- API enforces which teams can use which agent types
- Returns error if team doesn't have access

✅ **Caching-Friendly**
- Fetch once per session/job
- No repeated API calls
- Simple in-memory cache

✅ **Fallback Awareness**
- API returns fallback models if you want to implement your own retry logic
- Primary model is always priority 0

### Example: Multi-Agent Session

```python
# Session start - resolve all agents you'll use
client = AgentModelClient(...)

# Fetch and cache models for all agents
resume_model = client.get_model_for_agent("ResumeAgent")      # gpt-4o
chat_model = client.get_model_for_agent("ChatAgent")          # gpt-3.5-turbo
analysis_model = client.get_model_for_agent("AnalysisAgent")  # gpt-4-turbo

# Now use them throughout your session
# (no additional API calls to resolve models)

# Parse resume
parse_result = client.chat("ResumeAgent", parse_messages)

# Analyze parsed data
analysis = client.chat("AnalysisAgent", analysis_messages)

# Chat with user about results
response = client.chat("ChatAgent", chat_messages)
```

### When Models Change

**Scenario:** You update ResumeAgent from gpt-4 → gpt-4o in the API

```python
# Old sessions: continue using cached gpt-4 (until they restart)
# New sessions: automatically get gpt-4o
# Zero client code changes required! ✨
```

---

## Direct OpenAI-Compatible Integration (Pattern B)

For applications that need to use standard OpenAI SDK or want lower latency without job tracking, you can call LiteLLM directly.

### Getting Started

1. **Create team and get virtual key** (one-time setup):

```bash
curl -X POST https://llm-saas.usegittie.com/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_your_company",
    "team_id": "team_engineering",
    "team_alias": "Engineering Team",
    "model_groups": ["ChatAgent", "AnalysisAgent"],
    "credits_allocated": 1000
  }'
```

**Response includes:**
```json
{
  "team_id": "team_engineering",
  "model_groups": ["ChatAgent", "AnalysisAgent"],
  "allowed_models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
  "virtual_key": "sk-xxx...",
  "message": "Team created successfully with LiteLLM integration"
}
```

**Important:** Save the `virtual_key` and `allowed_models` list!

### LiteLLM Proxy URL

```
Production: https://llm-proxy.usegittie.com
```

### Python with OpenAI SDK

```python
from openai import OpenAI

# Initialize with virtual key
client = OpenAI(
    api_key="sk-xxx...",  # Your team's virtual key
    base_url="https://llm-proxy.usegittie.com"  # LiteLLM proxy URL
)

# Make calls with ACTUAL model names (not model groups!)
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # Use model name from allowed_models
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Node.js with OpenAI SDK

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-xxx...',  // Your team's virtual key
  baseURL: 'https://llm-proxy.usegittie.com'  // LiteLLM proxy URL
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'gpt-3.5-turbo',  // Use model name from allowed_models
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'Hello!' }
    ]
  });

  console.log(response.choices[0].message.content);
}
```

### Streaming Responses

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-xxx...",
    base_url="https://llm-proxy.usegittie.com"
)

stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### Key Differences from SaaS API

| Feature | SaaS API (Pattern A) | Direct LiteLLM (Pattern B) |
|---------|---------------------|---------------------------|
| Model Name | Model Group (e.g., "ResumeAgent") | Actual Model (e.g., "gpt-3.5-turbo") |
| Credit Tracking | Automatic (1 per job) | Manual (you track) |
| Fallbacks | Automatic (handled by SaaS API) | Manual (you implement) |
| Job Tracking | Yes (job_id) | No |
| Latency | +1 hop (SaaS API layer) | Direct to LiteLLM |
| Streaming | Not supported | Supported |
| OpenAI SDK | Custom client needed | Drop-in replacement |

### Which Models Can I Use?

When you create a team with model groups, the `allowed_models` field shows which **actual model names** you can use for direct calls:

```json
{
  "model_groups": ["ChatAgent", "AnalysisAgent"],
  "allowed_models": [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-turbo",
    "claude-3-sonnet"
  ]
}
```

If a model group contains:
- `ChatAgent`: gpt-3.5-turbo (priority 0), gpt-4 (priority 1)
- `AnalysisAgent`: gpt-4-turbo (priority 0), claude-3-sonnet (priority 1)

Your virtual key allows: **all 4 models** (deduplicated).

### Budget Limits

Your virtual key has a budget limit based on credits allocated:

```
Budget = Credits × $0.10
```

Example:
- 1,000 credits allocated = $100 budget in LiteLLM
- Once budget is exhausted, calls fail
- Add more credits via SaaS API to increase budget

### Error Handling

```python
from openai import OpenAI, OpenAIError

client = OpenAI(
    api_key="sk-xxx...",
    base_url="https://llm-proxy.usegittie.com"
)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )
except OpenAIError as e:
    if "budget" in str(e).lower():
        print("Budget exhausted - add more credits!")
    elif "model" in str(e).lower():
        print("Model not allowed for your team")
    else:
        print(f"LiteLLM error: {e}")
```

### Mixing Both Patterns

You can use both patterns simultaneously:

```python
from openai import OpenAI
from your_saas_client import SaasLLMClient

# For simple, streaming, or single-shot calls
openai_client = OpenAI(
    api_key="sk-xxx...",
    base_url="https://llm-proxy.usegittie.com"
)

# For complex workflows with credit tracking
saas_client = SaasLLMClient(
    base_url="https://llm-saas.usegittie.com",
    team_id="team_engineering"
)

# Simple chat - use OpenAI directly
response = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Quick question..."}]
)

# Complex workflow - use SaaS API
job_id = saas_client.create_job("document_analysis")
result = saas_client.llm_call(job_id, "ResumeAgent", messages)
saas_client.complete_job(job_id, "completed")  # Credit tracked!
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
curl "https://llm-saas.usegittie.com/api/teams/team_engineering/usage?period=2025-10"
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
curl "https://llm-saas.usegittie.com/api/credits/teams/team_engineering/transactions?limit=10"
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

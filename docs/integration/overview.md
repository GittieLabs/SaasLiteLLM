# Integration Overview

Learn how to integrate the SaaS LiteLLM API into your application. This guide covers integration patterns, authentication, and the job-based workflow.

!!! info "Built on LiteLLM"
    SaaS LiteLLM is built on top of [LiteLLM](https://docs.litellm.ai), which provides unified access to 100+ LLM providers (OpenAI, Anthropic, Google, Azure, etc.). The SaaS API layer adds job-based cost tracking and multi-tenancy on top of LiteLLM's routing capabilities.

## Integration Patterns

There are **two ways** to integrate with the SaaS LiteLLM API:

### Pattern A: Job-Based API (Recommended) 🌟

**Best for:** Multi-step workflows, cost tracking, simplified billing

```python
import requests

API = "http://localhost:8003/api"
headers = {"Authorization": "Bearer sk-your-virtual-key"}

# 1. Create job
job = requests.post(f"{API}/jobs/create", headers=headers, json={
    "team_id": "acme-corp",
    "job_type": "document_analysis"
}).json()

# 2. Make LLM calls
response = requests.post(f"{API}/jobs/{job['job_id']}/llm-call",
    headers=headers,
    json={
        "messages": [{"role": "user", "content": "Analyze this..."}]
    }
).json()

# 3. Complete job
result = requests.post(f"{API}/jobs/{job['job_id']}/complete",
    headers=headers,
    json={"status": "completed"}
).json()

print(f"Credits remaining: {result['costs']['credits_remaining']}")
```

**Key Features:**
- ✅ **Job-based tracking** - Group related LLM calls
- ✅ **Simple credit model** - 1 credit per completed job
- ✅ **Cost aggregation** - Track total costs per workflow
- ✅ **Model abstraction** - Use semantic names (e.g., "ChatAgent")
- ✅ **Automatic fallbacks** - Handled by the API
- ✅ **Usage analytics** - Track which workflows are expensive

[:octicons-arrow-right-24: Learn more about the job workflow](job-workflow.md)

### Pattern B: Streaming with SSE

**Best for:** Real-time responses, chat applications, progressive output

```python
import requests

API = "http://localhost:8003/api"
headers = {"Authorization": "Bearer sk-your-virtual-key"}

# Create job and make streaming call
response = requests.post(
    f"{API}/jobs/{job_id}/llm-call-stream",
    headers=headers,
    json={
        "messages": [{"role": "user", "content": "Tell me a story"}]
    },
    stream=True
)

# Process Server-Sent Events
for line in response.iter_lines():
    if line.startswith(b'data: '):
        chunk = json.loads(line[6:])
        if chunk.get("content"):
            print(chunk["content"], end="", flush=True)
```

**Key Features:**
- ✅ **Server-Sent Events (SSE)** - Standard streaming protocol
- ✅ **Zero buffering** - Immediate chunk forwarding
- ✅ **Full job tracking** - Same credit model as non-streaming
- ✅ **Type-safe** - Compatible with structured outputs

[:octicons-arrow-right-24: Learn more about streaming](streaming.md)

## Architecture Overview

```mermaid
graph LR
    A[Your Application] -->|HTTP/JSON| B[SaaS API :8003]
    B -->|Virtual Key| C[LiteLLM Proxy :8002]
    C --> D[OpenAI]
    C --> E[Anthropic]
    C --> F[Other Providers]

    B -.Job Tracking.-> G[PostgreSQL]
    B -.Credits.-> G

    style B fill:#4CAF50
    style C fill:#2196F3
    style G fill:#FF9800
```

### Component Breakdown

- **Your Application** - Makes API calls with virtual keys
- **SaaS API (Port 8003)** - Job-based wrapper, handles tracking and billing
- **LiteLLM Proxy (Port 8002)** - Routes to providers, handles caching and rate limiting
- **PostgreSQL** - Stores jobs, calls, teams, and usage data

## Authentication

All API endpoints require authentication using your team's **virtual API key**.

### Getting Your Virtual Key

When you create a team (via the admin dashboard or API), you receive a virtual key:

```bash
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme",
    "team_id": "acme-corp",
    "team_alias": "ACME Corp",
    "access_groups": ["gpt-models"],
    "credits_allocated": 1000
  }'
```

**Response:**
```json
{
  "team_id": "acme-corp",
  "virtual_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "credits_allocated": 1000,
  "credits_remaining": 1000
}
```

!!! warning "Keep your virtual key secure"
    - Store securely (environment variables, secrets manager)
    - Never commit to version control
    - Rotate keys periodically
    - Use different keys for different environments

### Using the Virtual Key

Include the virtual key in the `Authorization` header:

=== "Python"

    ```python
    headers = {
        "Authorization": "Bearer sk-your-virtual-key-here",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "http://localhost:8003/api/jobs/create",
        headers=headers,
        json={"team_id": "acme-corp", "job_type": "analysis"}
    )
    ```

=== "JavaScript"

    ```javascript
    const headers = {
      'Authorization': 'Bearer sk-your-virtual-key-here',
      'Content-Type': 'application/json'
    };

    const response = await fetch('http://localhost:8003/api/jobs/create', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        team_id: 'acme-corp',
        job_type: 'analysis'
      })
    });
    ```

=== "cURL"

    ```bash
    curl -X POST http://localhost:8003/api/jobs/create \
      -H "Authorization: Bearer sk-your-virtual-key-here" \
      -H "Content-Type: application/json" \
      -d '{"team_id":"acme-corp","job_type":"analysis"}'
    ```

[:octicons-arrow-right-24: Learn more about authentication](authentication.md)

## Job-Based Workflow

The job-based workflow groups multiple LLM calls into a single business operation:

### Why Jobs?

Traditional LLM APIs charge per API call. With jobs:

- **Simplified Billing** - 1 credit per completed job (not per call)
- **Cost Aggregation** - Track total cost across multiple calls
- **Business Context** - Track operations, not just API calls
- **Failure Handling** - Failed jobs don't consume credits

### Job Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending: Create Job
    Pending --> InProgress: First LLM Call
    InProgress --> InProgress: Additional Calls
    InProgress --> Completed: Complete (success)
    InProgress --> Failed: Complete (failure)
    Completed --> [*]: 1 credit deducted
    Failed --> [*]: No credit deducted
```

### Real-World Example: Document Analysis

```python
# 1 Job = Multiple LLM Calls = 1 Credit
job_id = create_job("document_analysis")

# Make multiple LLM calls
extract_text(job_id)      # Call 1
classify_content(job_id)  # Call 2
generate_summary(job_id)  # Call 3

# Complete job
complete_job(job_id, "completed")
# Result: 1 credit deducted (not 3!)
```

[:octicons-arrow-right-24: Learn more about the job workflow](job-workflow.md)

## Streaming vs Non-Streaming

### Non-Streaming (Buffered)

**Best for:** Batch processing, simple requests, structured outputs

```python
# Get complete response at once
response = requests.post(
    f"{API}/jobs/{job_id}/llm-call",
    headers=headers,
    json={"messages": messages}
).json()

content = response["response"]["content"]
```

**Characteristics:**
- ✅ Simpler to implement
- ✅ Complete response at once
- ✅ Easier error handling
- ❌ Higher latency (wait for full response)
- ❌ No progressive display

[:octicons-arrow-right-24: Learn more about non-streaming](non-streaming.md)

### Streaming (Server-Sent Events)

**Best for:** Chat applications, real-time responses, long outputs

```python
# Get response progressively
response = requests.post(
    f"{API}/jobs/{job_id}/llm-call-stream",
    headers=headers,
    json={"messages": messages},
    stream=True
)

for line in response.iter_lines():
    if line.startswith(b'data: '):
        chunk = json.loads(line[6:])
        print(chunk.get("content", ""), end="")
```

**Characteristics:**
- ✅ Lower perceived latency
- ✅ Progressive display
- ✅ Better user experience
- ✅ Same credit model as non-streaming
- ⚠️ More complex to implement

[:octicons-arrow-right-24: Learn more about streaming](streaming.md)

## Client Libraries

### Type-Safe Python Client

We provide a type-safe Python client with full type hints and Pydantic validation:

```python
from saas_litellm_client import SaasLiteLLMClient

async with SaasLiteLLMClient(
    base_url="http://localhost:8003",
    team_id="acme-corp",
    virtual_key="sk-your-key"
) as client:
    # Create job
    job = await client.create_job("document_analysis")

    # Make LLM call
    response = await client.llm_call(
        job_id=job.job_id,
        messages=[{"role": "user", "content": "Analyze..."}]
    )

    # Complete job
    result = await client.complete_job(job.job_id, "completed")
    print(f"Credits remaining: {result.credits_remaining}")
```

**Features:**
- ✅ Full type hints
- ✅ Pydantic validation
- ✅ Async/await support
- ✅ Automatic error handling
- ✅ Context manager support

[:octicons-arrow-right-24: Learn more about the typed client](typed-client.md)

### Structured Outputs

Use Pydantic models for type-safe responses:

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    email: str

# Get structured response
person = await client.structured_call(
    job_id=job_id,
    messages=[{"role": "user", "content": "Extract person info..."}],
    response_model=Person
)

print(f"Name: {person.name}, Age: {person.age}")
```

[:octicons-arrow-right-24: Learn more about structured outputs](structured-outputs.md)

## Quick Start

### Step 1: Set Up Organization and Team

```bash
# Create organization
curl -X POST http://localhost:8003/api/organizations/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme",
    "name": "ACME Corporation"
  }'

# Create model access group
curl -X POST http://localhost:8003/api/model-access-groups/create \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "gpt-models",
    "description": "GPT models"
  }'

# Create team
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme",
    "team_id": "acme-corp",
    "team_alias": "ACME Corp Team",
    "access_groups": ["gpt-models"],
    "credits_allocated": 1000
  }'
```

!!! tip "Use the Admin Dashboard"
    The easiest way to set up organizations and teams is through the [Admin Dashboard](../admin-dashboard/overview.md) at http://localhost:3002

### Step 2: Make Your First API Call

```python
import requests

API = "http://localhost:8003/api"
VIRTUAL_KEY = "sk-your-virtual-key-here"

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

# Create job
job = requests.post(f"{API}/jobs/create", headers=headers, json={
    "team_id": "acme-corp",
    "job_type": "test",
    "metadata": {"test": True}
}).json()

print(f"Created job: {job['job_id']}")

# Make LLM call
response = requests.post(
    f"{API}/jobs/{job['job_id']}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "Say hello!"}
        ]
    }
).json()

print(f"Response: {response['response']['content']}")

# Complete job
result = requests.post(
    f"{API}/jobs/{job['job_id']}/complete",
    headers=headers,
    json={"status": "completed"}
).json()

print(f"Credits remaining: {result['costs']['credits_remaining']}")
```

## Integration Guides

Ready to integrate? Check out these detailed guides:

<div class="grid cards" markdown>

-   **[Job Workflow](job-workflow.md)**

    ---

    Learn the job-based workflow: create, call, complete

-   **[Authentication](authentication.md)**

    ---

    Virtual keys, security best practices, error handling

-   **[Non-Streaming Calls](non-streaming.md)**

    ---

    Standard LLM calls with complete responses

-   **[Streaming Calls](streaming.md)**

    ---

    Server-Sent Events (SSE) for real-time responses

-   **[Typed Client](typed-client.md)**

    ---

    Type-safe Python client with async support

-   **[Structured Outputs](structured-outputs.md)**

    ---

    Pydantic models for type-safe responses

-   **[Error Handling](error-handling.md)**

    ---

    Common errors, retry strategies, best practices

-   **[Best Practices](best-practices.md)**

    ---

    Performance, security, cost optimization

</div>

## Code Examples

Want to see working code? Check out these examples:

- **[Basic Usage](../examples/basic-usage.md)** - Simple job creation and LLM call
- **[Streaming Examples](../examples/streaming-examples.md)** - Real-time streaming responses
- **[Structured Outputs](../examples/structured-outputs.md)** - Type-safe Pydantic models
- **[Full Chain Example](../examples/full-chain.md)** - UI → Client → SaaS API streaming chain

## API Reference

Need detailed API documentation?

- **[Interactive API Docs (Swagger)](http://localhost:8003/docs)** - Try the API in your browser
- **[ReDoc](http://localhost:8003/redoc)** - Beautiful API documentation
- **[API Reference](../api-reference/overview.md)** - Complete endpoint documentation

## Getting Help

If you encounter issues:

- Check the [Error Handling Guide](error-handling.md) for common errors
- Review the [Troubleshooting Guide](../testing/troubleshooting.md)
- See [Working Examples](../examples/basic-usage.md)

## Next Steps

1. **[Understand the Job Workflow](job-workflow.md)** - Core concept for cost tracking
2. **[Set Up Authentication](authentication.md)** - Get your virtual key and secure it
3. **[Try the Examples](../examples/basic-usage.md)** - Run working code
4. **[Explore Streaming](streaming.md)** - Add real-time responses to your app

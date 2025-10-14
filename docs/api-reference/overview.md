# API Reference Overview

Complete reference for the SaaS LiteLLM API endpoints.

## Overview

The SaaS LiteLLM API provides REST endpoints for managing jobs, making LLM calls, managing teams, and tracking usage.

**Base URL (Local):** `http://localhost:8003/api`
**Base URL (Production):** `https://your-domain.com/api`

**Authentication:** Bearer token (virtual key) in `Authorization` header

## Interactive API Documentation

For complete, interactive API documentation with "Try it out" functionality:

<div class="grid cards" markdown>

-   **:material-api: ReDoc**

    ---

    Beautiful, responsive API documentation

    [:octicons-arrow-right-24: http://localhost:8003/redoc](http://localhost:8003/redoc)

-   **:material-test-tube: Swagger UI**

    ---

    Interactive API testing interface

    [:octicons-arrow-right-24: http://localhost:8003/docs](http://localhost:8003/docs)

</div>

## API Categories

### Jobs API

Manage job lifecycle for cost tracking:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs/create` | POST | Create a new job |
| `/api/jobs/{job_id}` | GET | Get job details |
| `/api/jobs/{job_id}/complete` | POST | Complete a job |
| `/api/jobs/{job_id}/costs` | GET | Get job cost breakdown |

[:octicons-arrow-right-24: Jobs API Details](jobs.md)

### LLM Calls API

Make LLM calls within jobs:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs/{job_id}/llm-call` | POST | Non-streaming LLM call |
| `/api/jobs/{job_id}/llm-call-stream` | POST | Streaming LLM call (SSE) |

[:octicons-arrow-right-24: LLM Calls API Details](llm-calls.md)

### Teams API

Manage teams and access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/teams/create` | POST | Create a new team |
| `/api/teams/{team_id}` | GET | Get team details |
| `/api/teams/{team_id}` | PUT | Update team |
| `/api/teams/{team_id}/suspend` | POST | Suspend team |
| `/api/teams/{team_id}/resume` | POST | Resume team |
| `/api/teams/{team_id}/usage` | GET | Get team usage stats |

[:octicons-arrow-right-24: Teams API Details](teams.md)

### Organizations API

Manage organizations:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/organizations/create` | POST | Create organization |
| `/api/organizations/{org_id}` | GET | Get organization details |
| `/api/organizations/{org_id}/teams` | GET | List organization teams |

[:octicons-arrow-right-24: Organizations API Details](organizations.md)

### Credits API

Manage team credits:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/credits/balance` | GET | Get credit balance |
| `/api/credits/add` | POST | Add credits to team |
| `/api/credits/transactions` | GET | Get credit transaction history |

### Model Access Groups API

Control model access per team:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/model-access-groups/create` | POST | Create access group |
| `/api/model-access-groups/{group_name}` | GET | Get access group |
| `/api/model-access-groups/{group_name}` | PUT | Update access group |

### Model Aliases API

Configure model aliases:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/model-aliases/create` | POST | Create model alias |
| `/api/model-aliases/{alias_name}` | GET | Get model alias |

### Health API

Check system health:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |

## Authentication

All endpoints (except `/health`) require authentication with a virtual key:

```bash
curl -X POST http://localhost:8003/api/jobs/create \
  -H "Authorization: Bearer sk-your-virtual-key" \
  -H "Content-Type: application/json" \
  -d '{"team_id": "acme-corp", "job_type": "test"}'
```

[:octicons-arrow-right-24: Authentication Guide](../integration/authentication.md)

## Common Request Patterns

### Create Job → Make Call → Complete

```python
# 1. Create job
job = POST /api/jobs/create
  {
    "team_id": "acme-corp",
    "job_type": "analysis"
  }

# 2. Make LLM call
response = POST /api/jobs/{job_id}/llm-call
  {
    "messages": [{"role": "user", "content": "..."}]
  }

# 3. Complete job
result = POST /api/jobs/{job_id}/complete
  {
    "status": "completed"
  }
```

### Check Credits Before Call

```python
# Check balance
balance = GET /api/credits/balance?team_id=acme-corp

if balance["credits_remaining"] > 0:
    # Make call
    pass
else:
    # Add credits first
    POST /api/credits/add
      {
        "team_id": "acme-corp",
        "amount": 100
      }
```

## Response Formats

### Success Response (200 OK)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-10-14T12:00:00Z"
}
```

### Error Response (4xx/5xx)

```json
{
  "detail": "Insufficient credits"
}
```

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "messages"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Invalid or missing virtual key |
| 403 | Forbidden | Insufficient credits or access denied |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

[:octicons-arrow-right-24: Error Handling Guide](../integration/error-handling.md)

## Rate Limits

Rate limits are enforced per team:

- **Requests per minute (RPM):** Configurable per team
- **Tokens per minute (TPM):** Configurable per team

When rate limited, you'll receive a `429 Too Many Requests` response. Implement exponential backoff for retries.

## Pagination

Endpoints that return lists support pagination:

**Query Parameters:**
- `limit` (int, default: 100) - Number of items per page
- `offset` (int, default: 0) - Number of items to skip

**Example:**
```bash
GET /api/teams/acme-corp/usage?limit=50&offset=100
```

## Filtering and Sorting

### Time-based Filtering

```bash
GET /api/jobs?start_date=2024-10-01&end_date=2024-10-31
```

### Sorting

```bash
GET /api/jobs?sort_by=created_at&order=desc
```

## Versioning

The API uses URL-based versioning:

- **Current version:** v1 (default, no prefix required)
- **Future versions:** `/api/v2/...`

## OpenAPI Specification

Download the OpenAPI 3.0 specification:

```bash
curl http://localhost:8003/openapi.json > saas-api-spec.json
```

Use the spec to:
- Generate client libraries
- Import into API testing tools (Postman, Insomnia)
- Build custom tooling

## SDKs and Clients

### Python Client

Type-safe async Python client:

```python
from examples.typed_client import SaaSLLMClient

async with SaaSLLMClient(
    base_url="http://localhost:8003",
    team_id="acme-corp",
    virtual_key="sk-your-key"
) as client:
    job_id = await client.create_job("test")
    # ...
```

[:octicons-arrow-right-24: Typed Client Guide](../integration/typed-client.md)

### Other Languages

Currently, we provide an official Python client. For other languages:

1. Use the OpenAPI spec to generate clients
2. Use standard HTTP libraries
3. See example code in the integration guides

## Webhooks

Register webhooks to receive notifications:

```bash
POST /api/webhooks/register
{
  "team_id": "acme-corp",
  "webhook_url": "https://your-app.com/webhooks/job-complete",
  "events": ["job.completed", "job.failed"]
}
```

**Webhook Payload:**
```json
{
  "event": "job.completed",
  "job_id": "job_789abc",
  "team_id": "acme-corp",
  "timestamp": "2024-10-14T12:00:00Z",
  "data": {
    "total_calls": 5,
    "duration_seconds": 45
  }
}
```

## Idempotency

POST requests support idempotency keys to prevent duplicate operations:

```bash
POST /api/jobs/create
  -H "Idempotency-Key: unique-key-123"
  -d '{"team_id": "acme-corp", "job_type": "test"}'
```

If you retry with the same idempotency key within 24 hours, you'll receive the same response.

## CORS

CORS is enabled for web applications. Allowed origins can be configured in the server settings.

## Testing

### Test Endpoints in Browser

Use Swagger UI for interactive testing:

[:octicons-link-external-24: Open Swagger UI](http://localhost:8003/docs){ .md-button }

### Test with cURL

```bash
# Create job
curl -X POST http://localhost:8003/api/jobs/create \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"team_id": "acme-corp", "job_type": "test"}'

# Make LLM call
curl -X POST http://localhost:8003/api/jobs/{job_id}/llm-call \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

### Test with Python

```python
import requests

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = "sk-your-key"

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{API_URL}/jobs/create",
    headers=headers,
    json={"team_id": "acme-corp", "job_type": "test"}
)

print(response.json())
```

## Best Practices

1. **Always use HTTPS in production**
2. **Implement exponential backoff for retries**
3. **Set reasonable timeouts (30-60 seconds)**
4. **Handle all error codes appropriately**
5. **Monitor rate limits and credit usage**
6. **Use idempotency keys for critical operations**
7. **Validate request data before sending**
8. **Log requests for debugging**

[:octicons-arrow-right-24: Complete Best Practices Guide](../integration/best-practices.md)

## Detailed API Documentation

For detailed documentation on specific API categories:

<div class="grid cards" markdown>

-   **[Jobs API](jobs.md)**

    ---

    Create and manage jobs for cost tracking

-   **[LLM Calls API](llm-calls.md)**

    ---

    Make streaming and non-streaming LLM calls

-   **[Teams API](teams.md)**

    ---

    Manage teams and access controls

-   **[Organizations API](organizations.md)**

    ---

    Manage organizations and hierarchies

</div>

## Getting Help

If you encounter issues with the API:

1. **Check the interactive docs** - http://localhost:8003/docs
2. **Review error handling guide** - [Error Handling](../integration/error-handling.md)
3. **See examples** - [Basic Usage](../examples/basic-usage.md)
4. **Check troubleshooting** - [Troubleshooting Guide](../testing/troubleshooting.md)

## Next Steps

1. **[Try the Interactive Docs](http://localhost:8003/docs)** - Test endpoints in your browser
2. **[Read Integration Guide](../integration/overview.md)** - Learn integration patterns
3. **[See Examples](../examples/basic-usage.md)** - Working code examples
4. **[Review Jobs API](jobs.md)** - Detailed job endpoint documentation

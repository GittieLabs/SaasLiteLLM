# Teams API

The Teams API provides endpoints for managing teams, model access, and credit allocations in the SaaS LiteLLM platform. Teams are the primary organizational unit for access control and billing.

## Overview

Teams enable you to:

- **Organize users** - Group users by team for access control
- **Control model access** - Assign model groups to teams
- **Manage credits** - Allocate and track credit usage per team
- **Generate virtual keys** - Each team gets a virtual API key
- **Track usage** - Monitor team usage and costs

**Base URL:** `/api/teams`

**Authentication:** All endpoints require a Bearer token (virtual API key) in the `Authorization` header.

## Endpoints

### Create Team

Create a new team with model groups, credits, and LiteLLM integration.

**Endpoint:** `POST /api/teams/create`

**Authentication:** Required (admin/platform key)

**Request Body:**

```json
{
  "organization_id": "org_acme",
  "team_id": "acme-engineering",
  "team_alias": "ACME Engineering Team",
  "model_groups": ["GPT4Agent", "Claude3Agent"],
  "credits_allocated": 1000,
  "metadata": {
    "department": "Engineering",
    "cost_center": "CC-1001"
  }
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `organization_id` | string | Yes | Parent organization ID |
| `team_id` | string | Yes | Unique team identifier (e.g., "acme-engineering") |
| `team_alias` | string | No | Human-readable team name |
| `model_groups` | array | Yes | List of model group names the team can access |
| `credits_allocated` | integer | No | Initial credits to allocate (default: 0) |
| `metadata` | object | No | Custom metadata for the team |

**Response (200 OK):**

```json
{
  "team_id": "acme-engineering",
  "organization_id": "org_acme",
  "model_groups": ["GPT4Agent", "Claude3Agent"],
  "allowed_models": [
    "gpt-4-turbo",
    "gpt-4",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229"
  ],
  "credits_allocated": 1000,
  "credits_remaining": 1000,
  "virtual_key": "sk-1234567890abcdef",
  "message": "Team created successfully with LiteLLM integration"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `team_id` | string | Team identifier |
| `organization_id` | string | Parent organization ID |
| `model_groups` | array | Model groups assigned to team |
| `allowed_models` | array | Actual model names (resolved from model groups) |
| `credits_allocated` | integer | Total credits allocated |
| `credits_remaining` | integer | Credits remaining (initially same as allocated) |
| `virtual_key` | string | Virtual API key for this team |
| `message` | string | Success message |

**Example Request:**

=== "cURL"

    ```bash
    curl -X POST http://localhost:8003/api/teams/create \
      -H "Authorization: Bearer sk-platform-admin-key" \
      -H "Content-Type: application/json" \
      -d '{
        "organization_id": "org_acme",
        "team_id": "acme-engineering",
        "team_alias": "ACME Engineering Team",
        "model_groups": ["GPT4Agent", "Claude3Agent"],
        "credits_allocated": 1000,
        "metadata": {
          "department": "Engineering",
          "cost_center": "CC-1001"
        }
      }'
    ```

=== "Python"

    ```python
    import requests

    API_URL = "http://localhost:8003/api"
    ADMIN_KEY = "sk-platform-admin-key"

    headers = {
        "Authorization": f"Bearer {ADMIN_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_URL}/teams/create",
        headers=headers,
        json={
            "organization_id": "org_acme",
            "team_id": "acme-engineering",
            "team_alias": "ACME Engineering Team",
            "model_groups": ["GPT4Agent", "Claude3Agent"],
            "credits_allocated": 1000,
            "metadata": {
                "department": "Engineering",
                "cost_center": "CC-1001"
            }
        }
    )

    team = response.json()
    print(f"Team created: {team['team_id']}")
    print(f"Virtual key: {team['virtual_key']}")
    print(f"Allowed models: {', '.join(team['allowed_models'])}")
    print(f"Credits: {team['credits_remaining']}")
    ```

=== "JavaScript"

    ```javascript
    const API_URL = "http://localhost:8003/api";
    const ADMIN_KEY = "sk-platform-admin-key";

    const response = await fetch(`${API_URL}/teams/create`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ADMIN_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        organization_id: 'org_acme',
        team_id: 'acme-engineering',
        team_alias: 'ACME Engineering Team',
        model_groups: ['GPT4Agent', 'Claude3Agent'],
        credits_allocated: 1000,
        metadata: {
          department: 'Engineering',
          cost_center: 'CC-1001'
        }
      })
    });

    const team = await response.json();
    console.log(`Team created: ${team.team_id}`);
    console.log(`Virtual key: ${team.virtual_key}`);
    console.log(`Allowed models: ${team.allowed_models.join(', ')}`);
    console.log(`Credits: ${team.credits_remaining}`);
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Team already exists or invalid data |
| 404 | Not Found | Organization or model group not found |
| 422 | Validation Error | Invalid request data |
| 500 | Internal Server Error | LiteLLM integration failed or server error |

**Example Error Response:**

```json
{
  "detail": "Team 'acme-engineering' already exists"
}
```

---

### Get Team

Retrieve details about a specific team.

**Endpoint:** `GET /api/teams/{team_id}`

**Authentication:** Required (team's virtual key or admin key)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `team_id` | string | The team identifier |

**Response (200 OK):**

```json
{
  "team_id": "acme-engineering",
  "organization_id": "org_acme",
  "credits": {
    "team_id": "acme-engineering",
    "organization_id": "org_acme",
    "credits_allocated": 1000,
    "credits_used": 150,
    "credits_remaining": 850,
    "virtual_key": "sk-1234567890abcdef"
  },
  "model_groups": ["GPT4Agent", "Claude3Agent"]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `team_id` | string | Team identifier |
| `organization_id` | string | Parent organization ID |
| `credits` | object | Credit balance information |
| `credits.credits_allocated` | integer | Total credits allocated |
| `credits.credits_used` | integer | Credits consumed |
| `credits.credits_remaining` | integer | Credits remaining |
| `credits.virtual_key` | string | Team's virtual API key |
| `model_groups` | array | Model groups assigned to team |

**Example Request:**

=== "cURL"

    ```bash
    curl -X GET http://localhost:8003/api/teams/acme-engineering \
      -H "Authorization: Bearer sk-1234567890abcdef"
    ```

=== "Python"

    ```python
    response = requests.get(
        f"{API_URL}/teams/acme-engineering",
        headers={"Authorization": f"Bearer {team_virtual_key}"}
    )

    team = response.json()
    print(f"Team: {team['team_id']}")
    print(f"Organization: {team['organization_id']}")
    print(f"Credits remaining: {team['credits']['credits_remaining']}")
    print(f"Model groups: {', '.join(team['model_groups'])}")
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch(`${API_URL}/teams/acme-engineering`, {
      headers: {
        'Authorization': `Bearer ${teamVirtualKey}`
      }
    });

    const team = await response.json();
    console.log(`Team: ${team.team_id}`);
    console.log(`Organization: ${team.organization_id}`);
    console.log(`Credits remaining: ${team.credits.credits_remaining}`);
    console.log(`Model groups: ${team.model_groups.join(', ')}`);
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing virtual key |
| 404 | Not Found | Team not found |

---

### Update Team Model Groups

Assign or update model groups for a team (replaces existing assignments).

**Endpoint:** `PUT /api/teams/{team_id}/model-groups`

**Authentication:** Required (admin/platform key)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `team_id` | string | The team identifier |

**Request Body:**

```json
{
  "model_groups": ["GPT4Agent", "Claude3Agent", "GPT35Agent"]
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_groups` | array | Yes | List of model group names to assign (replaces all existing) |

**Response (200 OK):**

```json
{
  "team_id": "acme-engineering",
  "model_groups": ["GPT4Agent", "Claude3Agent", "GPT35Agent"],
  "message": "Model groups assigned successfully"
}
```

**Example Request:**

=== "cURL"

    ```bash
    curl -X PUT http://localhost:8003/api/teams/acme-engineering/model-groups \
      -H "Authorization: Bearer sk-platform-admin-key" \
      -H "Content-Type: application/json" \
      -d '{
        "model_groups": ["GPT4Agent", "Claude3Agent", "GPT35Agent"]
      }'
    ```

=== "Python"

    ```python
    response = requests.put(
        f"{API_URL}/teams/acme-engineering/model-groups",
        headers={
            "Authorization": f"Bearer {ADMIN_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model_groups": ["GPT4Agent", "Claude3Agent", "GPT35Agent"]
        }
    )

    result = response.json()
    print(f"Updated model groups for {result['team_id']}")
    print(f"New groups: {', '.join(result['model_groups'])}")
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch(`${API_URL}/teams/acme-engineering/model-groups`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${ADMIN_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model_groups: ['GPT4Agent', 'Claude3Agent', 'GPT35Agent']
      })
    });

    const result = await response.json();
    console.log(`Updated model groups for ${result.team_id}`);
    console.log(`New groups: ${result.model_groups.join(', ')}`);
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing admin key |
| 404 | Not Found | Team or model group not found |
| 422 | Validation Error | Invalid model group names |

---

### Get Team Usage

Get usage statistics for a team over a specified period.

**Endpoint:** `GET /api/teams/{team_id}/usage`

**Authentication:** Required (team's virtual key or admin key)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `team_id` | string | The team identifier |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | Yes | Period in format "YYYY-MM" (e.g., "2025-10") |

**Response (200 OK):**

```json
{
  "team_id": "acme-engineering",
  "period": "2025-10",
  "summary": {
    "total_jobs": 250,
    "successful_jobs": 235,
    "failed_jobs": 15,
    "total_cost_usd": 12.45,
    "total_tokens": 125000,
    "avg_cost_per_job": 0.0498
  },
  "job_types": {
    "resume_analysis": {
      "count": 150,
      "cost_usd": 7.5
    },
    "document_parsing": {
      "count": 80,
      "cost_usd": 4.0
    },
    "chat_session": {
      "count": 20,
      "cost_usd": 0.95
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `team_id` | string | Team identifier |
| `period` | string | Requested period |
| `summary.total_jobs` | integer | Total number of jobs |
| `summary.successful_jobs` | integer | Successfully completed jobs |
| `summary.failed_jobs` | integer | Failed jobs |
| `summary.total_cost_usd` | number | Total cost in USD (internal tracking) |
| `summary.total_tokens` | integer | Total tokens used |
| `summary.avg_cost_per_job` | number | Average cost per job |
| `job_types` | object | Breakdown by job type |

**Example Request:**

=== "cURL"

    ```bash
    curl -X GET "http://localhost:8003/api/teams/acme-engineering/usage?period=2025-10" \
      -H "Authorization: Bearer sk-1234567890abcdef"
    ```

=== "Python"

    ```python
    response = requests.get(
        f"{API_URL}/teams/acme-engineering/usage",
        headers={"Authorization": f"Bearer {team_virtual_key}"},
        params={"period": "2025-10"}
    )

    usage = response.json()
    print(f"Team: {usage['team_id']}")
    print(f"Period: {usage['period']}")
    print(f"Total jobs: {usage['summary']['total_jobs']}")
    print(f"Success rate: {usage['summary']['successful_jobs'] / usage['summary']['total_jobs'] * 100:.1f}%")
    print(f"Total cost: ${usage['summary']['total_cost_usd']:.2f}")
    print(f"Total tokens: {usage['summary']['total_tokens']:,}")
    print("\nJob type breakdown:")
    for job_type, stats in usage['job_types'].items():
        print(f"  {job_type}: {stats['count']} jobs (${stats['cost_usd']:.2f})")
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch(
      `${API_URL}/teams/acme-engineering/usage?period=2025-10`,
      {
        headers: {
          'Authorization': `Bearer ${teamVirtualKey}`
        }
      }
    );

    const usage = await response.json();
    console.log(`Team: ${usage.team_id}`);
    console.log(`Period: ${usage.period}`);
    console.log(`Total jobs: ${usage.summary.total_jobs}`);
    console.log(`Success rate: ${(usage.summary.successful_jobs / usage.summary.total_jobs * 100).toFixed(1)}%`);
    console.log(`Total cost: $${usage.summary.total_cost_usd.toFixed(2)}`);
    console.log(`Total tokens: ${usage.summary.total_tokens.toLocaleString()}`);
    console.log('\nJob type breakdown:');
    for (const [jobType, stats] of Object.entries(usage.job_types)) {
      console.log(`  ${jobType}: ${stats.count} jobs ($${stats.cost_usd.toFixed(2)})`);
    }
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing virtual key |
| 403 | Forbidden | Cannot access usage data for a different team |
| 404 | Not Found | Team not found |
| 422 | Validation Error | Invalid period format |

---

### List Team Jobs

List recent jobs for a team with optional filtering.

**Endpoint:** `GET /api/teams/{team_id}/jobs`

**Authentication:** Required (team's virtual key)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `team_id` | string | The team identifier |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 100 | Maximum number of jobs to return |
| `offset` | integer | No | 0 | Number of jobs to skip |
| `status` | string | No | None | Filter by status (pending, in_progress, completed, failed) |

**Response (200 OK):**

```json
{
  "team_id": "acme-engineering",
  "total": 25,
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "job_type": "resume_analysis",
      "status": "completed",
      "created_at": "2025-10-14T12:00:00.000Z",
      "completed_at": "2025-10-14T12:05:23.000Z",
      "credit_applied": true
    },
    {
      "job_id": "660e9511-f30c-52e5-b827-557766551111",
      "job_type": "document_parsing",
      "status": "in_progress",
      "created_at": "2025-10-14T13:00:00.000Z",
      "completed_at": null,
      "credit_applied": false
    }
  ]
}
```

**Example Request:**

=== "cURL"

    ```bash
    # Get all jobs
    curl -X GET "http://localhost:8003/api/teams/acme-engineering/jobs" \
      -H "Authorization: Bearer sk-1234567890abcdef"

    # Get only completed jobs
    curl -X GET "http://localhost:8003/api/teams/acme-engineering/jobs?status=completed" \
      -H "Authorization: Bearer sk-1234567890abcdef"

    # Pagination
    curl -X GET "http://localhost:8003/api/teams/acme-engineering/jobs?limit=50&offset=100" \
      -H "Authorization: Bearer sk-1234567890abcdef"
    ```

=== "Python"

    ```python
    # Get all jobs
    response = requests.get(
        f"{API_URL}/teams/acme-engineering/jobs",
        headers={"Authorization": f"Bearer {team_virtual_key}"}
    )

    jobs = response.json()
    print(f"Team: {jobs['team_id']}")
    print(f"Total jobs: {jobs['total']}")
    for job in jobs['jobs']:
        print(f"  {job['job_id']}: {job['job_type']} - {job['status']}")

    # Get only completed jobs
    response = requests.get(
        f"{API_URL}/teams/acme-engineering/jobs",
        headers={"Authorization": f"Bearer {team_virtual_key}"},
        params={"status": "completed", "limit": 50}
    )
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing virtual key |
| 403 | Forbidden | Cannot access jobs for a different team |
| 404 | Not Found | Team not found |

---

## Team Lifecycle

### Creating a Team

When you create a team:

1. Team record is created in the database
2. Team is registered with LiteLLM proxy
3. Virtual API key is generated
4. Model groups are assigned
5. Credits are allocated (if specified)
6. LiteLLM budget is configured based on credits

### Managing Team Access

Teams control access through:

- **Model Groups** - Which models the team can use
- **Credits** - How many jobs the team can run
- **Virtual Key** - API authentication for the team

### Team Credits

Credits are deducted when:
- A job completes successfully (status: "completed")
- All LLM calls in the job succeeded
- Credit hasn't already been applied

**1 Job = 1 Credit** regardless of:
- Number of LLM calls (1 or 100)
- Models used
- Actual USD cost
- Time duration

See [Credits API](../api-reference/credits.md) for credit management.

## Complete Example

```python
import requests

API_URL = "http://localhost:8003/api"
ADMIN_KEY = "sk-platform-admin-key"

headers = {
    "Authorization": f"Bearer {ADMIN_KEY}",
    "Content-Type": "application/json"
}

# 1. Create organization (if not exists)
org_response = requests.post(
    f"{API_URL}/organizations/create",
    headers=headers,
    json={
        "organization_id": "org_acme",
        "name": "ACME Corporation",
        "metadata": {"industry": "Technology"}
    }
)
print(f"Organization: {org_response.json()['name']}")

# 2. Create team
team_response = requests.post(
    f"{API_URL}/teams/create",
    headers=headers,
    json={
        "organization_id": "org_acme",
        "team_id": "acme-engineering",
        "team_alias": "ACME Engineering Team",
        "model_groups": ["GPT4Agent"],
        "credits_allocated": 1000,
        "metadata": {
            "department": "Engineering"
        }
    }
)

team = team_response.json()
print(f"\nTeam created: {team['team_id']}")
print(f"Virtual key: {team['virtual_key']}")
print(f"Allowed models: {', '.join(team['allowed_models'])}")
print(f"Credits: {team['credits_remaining']}")

# 3. Use team virtual key to create jobs
team_key = team['virtual_key']
team_headers = {
    "Authorization": f"Bearer {team_key}",
    "Content-Type": "application/json"
}

# Create a job
job_response = requests.post(
    f"{API_URL}/jobs/create",
    headers=team_headers,
    json={
        "team_id": "acme-engineering",
        "job_type": "test"
    }
)

print(f"\nJob created: {job_response.json()['job_id']}")

# 4. Get team details
team_details = requests.get(
    f"{API_URL}/teams/acme-engineering",
    headers=team_headers
).json()

print(f"\nTeam details:")
print(f"  Organization: {team_details['organization_id']}")
print(f"  Credits remaining: {team_details['credits']['credits_remaining']}")
print(f"  Model groups: {', '.join(team_details['model_groups'])}")
```

## Rate Limiting

Teams API endpoints have rate limits:

- **GET endpoints:** 100 requests per minute
- **POST/PUT endpoints:** 30 requests per minute

## Best Practices

1. **Use descriptive team IDs** - Use meaningful identifiers like "acme-engineering"
2. **Store virtual keys securely** - Treat virtual keys like passwords
3. **Monitor credit usage** - Check team usage regularly
4. **Assign appropriate model groups** - Give teams only the models they need
5. **Use team metadata** - Add context for billing and analytics
6. **Implement credit alerts** - Notify teams when credits are low

## See Also

- [Organizations API](organizations.md) - Manage parent organizations
- [Credits API](../api-reference/credits.md) - Manage team credits
- [Model Groups](../admin-dashboard/model-access-groups.md) - Configure model groups
- [Authentication Guide](../integration/authentication.md) - Using virtual keys
- [Jobs API](jobs.md) - Create and manage jobs

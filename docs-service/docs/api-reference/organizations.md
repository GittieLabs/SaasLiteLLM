# Organizations API

The Organizations API provides endpoints for managing organizations in the SaaS LiteLLM platform. Organizations are the top-level entity in the hierarchy and contain multiple teams.

## Overview

Organizations enable you to:

- **Group teams hierarchically** - Organize multiple teams under one organization
- **Track organization-wide usage** - View aggregated usage across all teams
- **Manage billing** - Bill at the organization level
- **Organize customers** - Each customer/company can be an organization

**Hierarchy:**

```
Organization (e.g., "ACME Corp")
├── Team 1 (e.g., "Engineering")
│   ├── Job 1
│   ├── Job 2
│   └── ...
├── Team 2 (e.g., "Sales")
│   ├── Job 1
│   └── ...
└── Team 3 (e.g., "Marketing")
    └── ...
```

**Base URL:** `/api/organizations`

**Authentication:** All endpoints require a Bearer token (virtual API key or admin key) in the `Authorization` header.

## Endpoints

### Create Organization

Create a new organization.

**Endpoint:** `POST /api/organizations/create`

**Authentication:** Required (admin/platform key)

**Request Body:**

```json
{
  "organization_id": "org_acme",
  "name": "ACME Corporation",
  "metadata": {
    "industry": "Technology",
    "size": "Enterprise",
    "country": "USA",
    "contact_email": "admin@acme.com"
  }
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `organization_id` | string | Yes | Unique organization identifier (e.g., "org_acme") |
| `name` | string | Yes | Organization display name |
| `metadata` | object | No | Custom metadata for the organization |

**Response (200 OK):**

```json
{
  "organization_id": "org_acme",
  "name": "ACME Corporation",
  "status": "active",
  "metadata": {
    "industry": "Technology",
    "size": "Enterprise",
    "country": "USA",
    "contact_email": "admin@acme.com"
  },
  "created_at": "2025-10-14T12:00:00.000Z",
  "updated_at": "2025-10-14T12:00:00.000Z"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `organization_id` | string | Unique organization identifier |
| `name` | string | Organization display name |
| `status` | string | Organization status (always "active" on creation) |
| `metadata` | object | Custom metadata |
| `created_at` | string (ISO 8601) | Creation timestamp |
| `updated_at` | string (ISO 8601) | Last update timestamp |

**Example Request:**

=== "cURL"

    ```bash
    curl -X POST http://localhost:8003/api/organizations/create \
      -H "Authorization: Bearer sk-platform-admin-key" \
      -H "Content-Type: application/json" \
      -d '{
        "organization_id": "org_acme",
        "name": "ACME Corporation",
        "metadata": {
          "industry": "Technology",
          "size": "Enterprise",
          "country": "USA",
          "contact_email": "admin@acme.com"
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
        f"{API_URL}/organizations/create",
        headers=headers,
        json={
            "organization_id": "org_acme",
            "name": "ACME Corporation",
            "metadata": {
                "industry": "Technology",
                "size": "Enterprise",
                "country": "USA",
                "contact_email": "admin@acme.com"
            }
        }
    )

    org = response.json()
    print(f"Organization created: {org['name']}")
    print(f"ID: {org['organization_id']}")
    print(f"Status: {org['status']}")
    print(f"Created: {org['created_at']}")
    ```

=== "JavaScript"

    ```javascript
    const API_URL = "http://localhost:8003/api";
    const ADMIN_KEY = "sk-platform-admin-key";

    const response = await fetch(`${API_URL}/organizations/create`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ADMIN_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        organization_id: 'org_acme',
        name: 'ACME Corporation',
        metadata: {
          industry: 'Technology',
          size: 'Enterprise',
          country: 'USA',
          contact_email: 'admin@acme.com'
        }
      })
    });

    const org = await response.json();
    console.log(`Organization created: ${org.name}`);
    console.log(`ID: ${org.organization_id}`);
    console.log(`Status: ${org.status}`);
    console.log(`Created: ${org.created_at}`);
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Organization with this ID already exists |
| 401 | Unauthorized | Invalid or missing admin key |
| 422 | Validation Error | Invalid request data |
| 500 | Internal Server Error | Server error |

**Example Error Response:**

```json
{
  "detail": "Organization with ID 'org_acme' already exists"
}
```

---

### Get Organization

Retrieve details about a specific organization.

**Endpoint:** `GET /api/organizations/{organization_id}`

**Authentication:** Required (admin key or team key within organization)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `organization_id` | string | The organization identifier |

**Response (200 OK):**

```json
{
  "organization_id": "org_acme",
  "name": "ACME Corporation",
  "status": "active",
  "metadata": {
    "industry": "Technology",
    "size": "Enterprise",
    "country": "USA",
    "contact_email": "admin@acme.com"
  },
  "created_at": "2025-10-14T12:00:00.000Z",
  "updated_at": "2025-10-14T12:00:00.000Z"
}
```

**Example Request:**

=== "cURL"

    ```bash
    curl -X GET http://localhost:8003/api/organizations/org_acme \
      -H "Authorization: Bearer sk-platform-admin-key"
    ```

=== "Python"

    ```python
    response = requests.get(
        f"{API_URL}/organizations/org_acme",
        headers={"Authorization": f"Bearer {ADMIN_KEY}"}
    )

    org = response.json()
    print(f"Organization: {org['name']}")
    print(f"ID: {org['organization_id']}")
    print(f"Status: {org['status']}")
    print(f"Industry: {org['metadata'].get('industry', 'N/A')}")
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch(`${API_URL}/organizations/org_acme`, {
      headers: {
        'Authorization': `Bearer ${ADMIN_KEY}`
      }
    });

    const org = await response.json();
    console.log(`Organization: ${org.name}`);
    console.log(`ID: ${org.organization_id}`);
    console.log(`Status: ${org.status}`);
    console.log(`Industry: ${org.metadata.industry || 'N/A'}`);
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing key |
| 404 | Not Found | Organization not found |

---

### List Organization Teams

List all teams belonging to an organization.

**Endpoint:** `GET /api/organizations/{organization_id}/teams`

**Authentication:** Required (admin key or team key within organization)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `organization_id` | string | The organization identifier |

**Response (200 OK):**

```json
{
  "organization_id": "org_acme",
  "team_count": 3,
  "teams": [
    "acme-engineering",
    "acme-sales",
    "acme-marketing"
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `organization_id` | string | Organization identifier |
| `team_count` | integer | Number of teams in the organization |
| `teams` | array | List of team IDs |

**Example Request:**

=== "cURL"

    ```bash
    curl -X GET http://localhost:8003/api/organizations/org_acme/teams \
      -H "Authorization: Bearer sk-platform-admin-key"
    ```

=== "Python"

    ```python
    response = requests.get(
        f"{API_URL}/organizations/org_acme/teams",
        headers={"Authorization": f"Bearer {ADMIN_KEY}"}
    )

    data = response.json()
    print(f"Organization: {data['organization_id']}")
    print(f"Total teams: {data['team_count']}")
    print("Teams:")
    for team_id in data['teams']:
        print(f"  - {team_id}")
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch(`${API_URL}/organizations/org_acme/teams`, {
      headers: {
        'Authorization': `Bearer ${ADMIN_KEY}`
      }
    });

    const data = await response.json();
    console.log(`Organization: ${data.organization_id}`);
    console.log(`Total teams: ${data.team_count}`);
    console.log('Teams:');
    data.teams.forEach(teamId => {
      console.log(`  - ${teamId}`);
    });
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing key |
| 404 | Not Found | Organization not found |

---

### Get Organization Usage

Get organization-wide usage statistics for a specified period.

**Endpoint:** `GET /api/organizations/{organization_id}/usage`

**Authentication:** Required (admin key or team key within organization)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `organization_id` | string | The organization identifier |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | Yes | Period in format "YYYY-MM" (e.g., "2025-10") |

**Response (200 OK):**

```json
{
  "organization_id": "org_acme",
  "period": "2025-10",
  "summary": {
    "total_jobs": 750,
    "completed_jobs": 710,
    "failed_jobs": 40,
    "credits_used": 710,
    "total_cost_usd": 35.25,
    "total_tokens": 375000
  },
  "teams": {
    "acme-engineering": {
      "jobs": 450,
      "credits_used": 425
    },
    "acme-sales": {
      "jobs": 200,
      "credits_used": 195
    },
    "acme-marketing": {
      "jobs": 100,
      "credits_used": 90
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `organization_id` | string | Organization identifier |
| `period` | string | Requested period |
| `summary.total_jobs` | integer | Total jobs across all teams |
| `summary.completed_jobs` | integer | Successfully completed jobs |
| `summary.failed_jobs` | integer | Failed jobs |
| `summary.credits_used` | integer | Total credits consumed |
| `summary.total_cost_usd` | number | Total cost in USD (internal tracking) |
| `summary.total_tokens` | integer | Total tokens used |
| `teams` | object | Per-team breakdown |
| `teams[team_id].jobs` | integer | Number of jobs for this team |
| `teams[team_id].credits_used` | integer | Credits used by this team |

**Example Request:**

=== "cURL"

    ```bash
    curl -X GET "http://localhost:8003/api/organizations/org_acme/usage?period=2025-10" \
      -H "Authorization: Bearer sk-platform-admin-key"
    ```

=== "Python"

    ```python
    response = requests.get(
        f"{API_URL}/organizations/org_acme/usage",
        headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        params={"period": "2025-10"}
    )

    usage = response.json()
    print(f"Organization: {usage['organization_id']}")
    print(f"Period: {usage['period']}")
    print(f"\nSummary:")
    print(f"  Total jobs: {usage['summary']['total_jobs']}")
    print(f"  Completed: {usage['summary']['completed_jobs']}")
    print(f"  Failed: {usage['summary']['failed_jobs']}")
    print(f"  Success rate: {usage['summary']['completed_jobs'] / usage['summary']['total_jobs'] * 100:.1f}%")
    print(f"  Credits used: {usage['summary']['credits_used']}")
    print(f"  Total cost: ${usage['summary']['total_cost_usd']:.2f}")
    print(f"  Total tokens: {usage['summary']['total_tokens']:,}")

    print(f"\nTeam breakdown:")
    for team_id, stats in usage['teams'].items():
        print(f"  {team_id}:")
        print(f"    Jobs: {stats['jobs']}")
        print(f"    Credits used: {stats['credits_used']}")
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch(
      `${API_URL}/organizations/org_acme/usage?period=2025-10`,
      {
        headers: {
          'Authorization': `Bearer ${ADMIN_KEY}`
        }
      }
    );

    const usage = await response.json();
    console.log(`Organization: ${usage.organization_id}`);
    console.log(`Period: ${usage.period}`);
    console.log('\nSummary:');
    console.log(`  Total jobs: ${usage.summary.total_jobs}`);
    console.log(`  Completed: ${usage.summary.completed_jobs}`);
    console.log(`  Failed: ${usage.summary.failed_jobs}`);
    console.log(`  Success rate: ${(usage.summary.completed_jobs / usage.summary.total_jobs * 100).toFixed(1)}%`);
    console.log(`  Credits used: ${usage.summary.credits_used}`);
    console.log(`  Total cost: $${usage.summary.total_cost_usd.toFixed(2)}`);
    console.log(`  Total tokens: ${usage.summary.total_tokens.toLocaleString()}`);

    console.log('\nTeam breakdown:');
    for (const [teamId, stats] of Object.entries(usage.teams)) {
      console.log(`  ${teamId}:`);
      console.log(`    Jobs: ${stats.jobs}`);
      console.log(`    Credits used: ${stats.credits_used}`);
    }
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing key |
| 404 | Not Found | Organization not found |
| 422 | Validation Error | Invalid period format |

---

## Organization Hierarchy

Organizations follow a hierarchical structure:

```
┌─────────────────────────────────────────┐
│ Organization: org_acme                  │
│ Name: ACME Corporation                  │
├─────────────────────────────────────────┤
│ Teams:                                  │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │ Team: acme-engineering          │    │
│ │ Model Groups: GPT4Agent         │    │
│ │ Credits: 1000                   │    │
│ │ Virtual Key: sk-eng-123...      │    │
│ │                                 │    │
│ │ Jobs: 450                       │    │
│ │   ├─ resume_analysis: 300       │    │
│ │   ├─ document_parsing: 100      │    │
│ │   └─ chat_session: 50           │    │
│ └─────────────────────────────────┘    │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │ Team: acme-sales                │    │
│ │ Model Groups: GPT35Agent        │    │
│ │ Credits: 500                    │    │
│ │ Virtual Key: sk-sales-456...    │    │
│ │                                 │    │
│ │ Jobs: 200                       │    │
│ │   ├─ lead_qualification: 150    │    │
│ │   └─ email_generation: 50       │    │
│ └─────────────────────────────────┘    │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │ Team: acme-marketing            │    │
│ │ Model Groups: Claude3Agent      │    │
│ │ Credits: 300                    │    │
│ │ Virtual Key: sk-mkt-789...      │    │
│ │                                 │    │
│ │ Jobs: 100                       │    │
│ │   └─ content_generation: 100    │    │
│ └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Complete Workflow Example

```python
import requests

API_URL = "http://localhost:8003/api"
ADMIN_KEY = "sk-platform-admin-key"

headers = {
    "Authorization": f"Bearer {ADMIN_KEY}",
    "Content-Type": "application/json"
}

# 1. Create organization
print("Creating organization...")
org_response = requests.post(
    f"{API_URL}/organizations/create",
    headers=headers,
    json={
        "organization_id": "org_acme",
        "name": "ACME Corporation",
        "metadata": {
            "industry": "Technology",
            "size": "Enterprise",
            "country": "USA"
        }
    }
)

org = org_response.json()
print(f"✓ Created: {org['name']} ({org['organization_id']})")

# 2. Create teams within the organization
teams_to_create = [
    {
        "team_id": "acme-engineering",
        "team_alias": "Engineering Team",
        "model_groups": ["GPT4Agent"],
        "credits": 1000
    },
    {
        "team_id": "acme-sales",
        "team_alias": "Sales Team",
        "model_groups": ["GPT35Agent"],
        "credits": 500
    },
    {
        "team_id": "acme-marketing",
        "team_alias": "Marketing Team",
        "model_groups": ["Claude3Agent"],
        "credits": 300
    }
]

print("\nCreating teams...")
for team_config in teams_to_create:
    team_response = requests.post(
        f"{API_URL}/teams/create",
        headers=headers,
        json={
            "organization_id": "org_acme",
            "team_id": team_config["team_id"],
            "team_alias": team_config["team_alias"],
            "model_groups": team_config["model_groups"],
            "credits_allocated": team_config["credits"]
        }
    )

    team = team_response.json()
    print(f"✓ Created: {team['team_id']} (Credits: {team['credits_allocated']})")

# 3. List organization teams
print("\nListing organization teams...")
teams_response = requests.get(
    f"{API_URL}/organizations/org_acme/teams",
    headers=headers
)

teams_data = teams_response.json()
print(f"✓ Organization has {teams_data['team_count']} teams:")
for team_id in teams_data['teams']:
    print(f"  - {team_id}")

# 4. Get organization details
print("\nGetting organization details...")
org_details = requests.get(
    f"{API_URL}/organizations/org_acme",
    headers=headers
).json()

print(f"✓ Organization: {org_details['name']}")
print(f"  Status: {org_details['status']}")
print(f"  Industry: {org_details['metadata'].get('industry', 'N/A')}")
print(f"  Created: {org_details['created_at']}")

# 5. Get organization usage (if data exists)
print("\nGetting organization usage for current period...")
try:
    usage_response = requests.get(
        f"{API_URL}/organizations/org_acme/usage",
        headers=headers,
        params={"period": "2025-10"}
    )

    if usage_response.status_code == 200:
        usage = usage_response.json()
        print(f"✓ Period: {usage['period']}")
        print(f"  Total jobs: {usage['summary']['total_jobs']}")
        print(f"  Credits used: {usage['summary']['credits_used']}")
        print(f"  Total cost: ${usage['summary']['total_cost_usd']:.2f}")
    else:
        print("  No usage data yet for this period")
except:
    print("  No usage data yet")

print("\n✅ Organization setup complete!")
```

**Output:**

```
Creating organization...
✓ Created: ACME Corporation (org_acme)

Creating teams...
✓ Created: acme-engineering (Credits: 1000)
✓ Created: acme-sales (Credits: 500)
✓ Created: acme-marketing (Credits: 300)

Listing organization teams...
✓ Organization has 3 teams:
  - acme-engineering
  - acme-sales
  - acme-marketing

Getting organization details...
✓ Organization: ACME Corporation
  Status: active
  Industry: Technology
  Created: 2025-10-14T12:00:00.000Z

Getting organization usage for current period...
✓ Period: 2025-10
  Total jobs: 750
  Credits used: 710
  Total cost: $35.25

✅ Organization setup complete!
```

## Use Cases

### Multi-Tenant SaaS Platform

Each customer is an organization:

```python
# Customer A
create_organization("org_customer_a", "Customer A Inc.")
create_team("org_customer_a", "customer-a-prod", ["GPT4Agent"])
create_team("org_customer_a", "customer-a-dev", ["GPT35Agent"])

# Customer B
create_organization("org_customer_b", "Customer B LLC")
create_team("org_customer_b", "customer-b-prod", ["Claude3Agent"])
create_team("org_customer_b", "customer-b-dev", ["GPT35Agent"])
```

### Departmental Organization

Single company, multiple departments:

```python
create_organization("org_acme", "ACME Corporation")
create_team("org_acme", "engineering", ["GPT4Agent", "Claude3Agent"])
create_team("org_acme", "sales", ["GPT35Agent"])
create_team("org_acme", "marketing", ["Claude3Agent"])
create_team("org_acme", "support", ["GPT35Agent"])
```

### Environment Separation

Separate production and development:

```python
create_organization("org_acme", "ACME Corporation")
create_team("org_acme", "production", ["GPT4Agent"])
create_team("org_acme", "staging", ["GPT4Agent"])
create_team("org_acme", "development", ["GPT35Agent"])
```

## Rate Limiting

Organizations API endpoints have rate limits:

- **GET endpoints:** 100 requests per minute
- **POST/PUT endpoints:** 30 requests per minute

## Best Practices

1. **Use descriptive organization IDs** - Use prefixes like "org_" for clarity
2. **Add comprehensive metadata** - Include industry, size, contact info for billing
3. **Monitor organization-wide usage** - Track usage across all teams
4. **Set up team hierarchy early** - Create organization before creating teams
5. **Use meaningful names** - Human-readable names help with reporting
6. **Track periods consistently** - Use YYYY-MM format for usage queries
7. **Implement usage alerts** - Monitor organization usage to prevent overages

## See Also

- [Teams API](teams.md) - Manage teams within organizations
- [Jobs API](jobs.md) - Create and manage jobs
- [Credits API](../api-reference/credits.md) - Manage team credits
- [Authentication Guide](../integration/authentication.md) - API authentication details
- [Getting Started](../getting-started/quickstart.md) - Initial setup guide

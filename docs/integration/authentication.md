# Team Authentication

Learn how to authenticate API requests using virtual keys, best practices for key management, and how to handle authentication errors.

!!! info "Admin vs Team Authentication"
    This guide covers **team authentication** using virtual keys for making LLM requests.

    For **admin authentication** (managing organizations, teams, models), see [Admin Authentication](../admin-dashboard/authentication.md).

## Overview

All team API endpoints in SaaS LiteLLM require authentication using **virtual keys**. Virtual keys are team-specific API keys that:

- Authenticate your team with the SaaS API
- Track usage and costs per team
- Enforce credit limits and access controls
- Never expose the underlying LiteLLM infrastructure

## Authentication Types

SaaS LiteLLM uses **two separate authentication systems**:

| Type | Key Format | Header | Used For | Documentation |
|------|------------|--------|----------|---------------|
| **Admin** | `MASTER_KEY` | `X-Admin-Key` | Managing organizations, teams, models | [Admin Auth](../admin-dashboard/authentication.md) |
| **Team** | Virtual Key (per-team) | `Authorization: Bearer` | Making LLM requests | This guide |

**Important**: These are completely separate systems with different keys and purposes!

## Virtual Keys

### What is a Virtual Key?

A virtual key is a Bearer token in the format:

```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Each team has a unique virtual key that:

- **Identifies the team** - Associates requests with a specific team
- **Enforces budgets** - Ensures teams don't exceed credit limits
- **Controls access** - Limits which models the team can use via model access groups
- **Tracks usage** - Records all LLM calls and costs per team

!!! info "Virtual Keys are Team-Specific"
    Each virtual key is tied to exactly one team. One team cannot use another team's virtual key.

### Getting Your Virtual Key

When you create a team (via the admin dashboard or API), you receive a virtual key in the response.

#### Via API

```bash
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

**Response:**
```json
{
  "team_id": "acme-corp",
  "organization_id": "org_acme",
  "virtual_key": "sk-1234567890abcdef1234567890abcdef",
  "credits_allocated": 1000,
  "credits_remaining": 1000,
  "status": "active"
}
```

#### Via Admin Dashboard

1. Navigate to http://localhost:3002 (or your production URL)
2. Go to **Teams** section
3. Click **Create Team**
4. Fill in team details and click **Create**
5. Copy the virtual key from the response

!!! tip "Save Your Virtual Key Immediately"
    The virtual key is only shown once during team creation. Store it securely immediately.

### Viewing Existing Keys

If you need to retrieve a team's virtual key:

```bash
curl http://localhost:8003/api/teams/acme-corp \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "team_id": "acme-corp",
  "organization_id": "org_acme",
  "virtual_key": "sk-1234567890abcdef1234567890abcdef",
  "credits_remaining": 850,
  "status": "active"
}
```

## Using Virtual Keys

### HTTP Header Authentication

Include the virtual key in the `Authorization` header with the `Bearer` scheme:

=== "Python"

    ```python
    import requests

    API_URL = "http://localhost:8003/api"
    VIRTUAL_KEY = "sk-1234567890abcdef1234567890abcdef"

    headers = {
        "Authorization": f"Bearer {VIRTUAL_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={
            "team_id": "acme-corp",
            "job_type": "document_analysis"
        }
    )

    print(response.json())
    ```

=== "JavaScript"

    ```javascript
    const API_URL = "http://localhost:8003/api";
    const VIRTUAL_KEY = "sk-1234567890abcdef1234567890abcdef";

    const headers = {
      "Authorization": `Bearer ${VIRTUAL_KEY}`,
      "Content-Type": "application/json"
    };

    const response = await fetch(`${API_URL}/jobs/create`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        team_id: "acme-corp",
        job_type: "document_analysis"
      })
    });

    const data = await response.json();
    console.log(data);
    ```

=== "cURL"

    ```bash
    curl -X POST http://localhost:8003/api/jobs/create \
      -H "Authorization: Bearer sk-1234567890abcdef1234567890abcdef" \
      -H "Content-Type: application/json" \
      -d '{
        "team_id": "acme-corp",
        "job_type": "document_analysis"
      }'
    ```

=== "Go"

    ```go
    package main

    import (
        "bytes"
        "encoding/json"
        "net/http"
    )

    func main() {
        apiURL := "http://localhost:8003/api"
        virtualKey := "sk-1234567890abcdef1234567890abcdef"

        data := map[string]string{
            "team_id":  "acme-corp",
            "job_type": "document_analysis",
        }

        jsonData, _ := json.Marshal(data)
        req, _ := http.NewRequest("POST", apiURL+"/jobs/create", bytes.NewBuffer(jsonData))
        req.Header.Set("Authorization", "Bearer "+virtualKey)
        req.Header.Set("Content-Type", "application/json")

        client := &http.Client{}
        resp, _ := client.Do(req)
        defer resp.Body.Close()
    }
    ```

### Type-Safe Python Client

If you're using Python, we provide a type-safe client that handles authentication automatically:

```python
from saas_litellm_client import SaasLiteLLMClient

async with SaasLiteLLMClient(
    base_url="http://localhost:8003",
    team_id="acme-corp",
    virtual_key="sk-1234567890abcdef1234567890abcdef"
) as client:
    # Authentication is handled automatically
    job = await client.create_job("document_analysis")
    print(f"Created job: {job.job_id}")
```

[:octicons-arrow-right-24: Learn more about the typed client](typed-client.md)

## Authentication Errors

### 401 Unauthorized

**Error Response:**
```json
{
  "detail": "Invalid or missing API key"
}
```

**Causes:**
- Missing `Authorization` header
- Invalid virtual key format
- Virtual key doesn't exist
- Virtual key has been revoked

**Solution:**
```python
# ❌ Wrong - Missing Authorization header
response = requests.post(
    "http://localhost:8003/api/jobs/create",
    json={"team_id": "acme-corp", "job_type": "test"}
)

# ✅ Correct - Include Authorization header
headers = {"Authorization": "Bearer sk-your-virtual-key"}
response = requests.post(
    "http://localhost:8003/api/jobs/create",
    headers=headers,
    json={"team_id": "acme-corp", "job_type": "test"}
)
```

### 403 Forbidden

**Error Response:**
```json
{
  "detail": "Team suspended or insufficient credits"
}
```

**Causes:**
- Team has been suspended by an administrator
- Team has run out of credits
- Team is in "pause" mode

**Solution:**
1. Check team status: `GET /api/teams/{team_id}`
2. Contact administrator to add credits or reactivate team
3. Check credit balance: `GET /api/credits/balance?team_id={team_id}`

### 403 Model Access Denied

**Error Response:**
```json
{
  "detail": "Team does not have access to the requested model"
}
```

**Causes:**
- Team's model access group doesn't include the requested model
- Model alias not configured for the team's access group

**Solution:**
1. Check team's access groups: `GET /api/teams/{team_id}`
2. Contact administrator to update access groups
3. Use a model alias the team has access to

## Security Best Practices

### 1. Environment Variables

**Never hardcode virtual keys in your source code.** Use environment variables:

=== "Python"

    ```python
    import os

    VIRTUAL_KEY = os.environ.get("SAAS_LITELLM_VIRTUAL_KEY")

    if not VIRTUAL_KEY:
        raise ValueError("SAAS_LITELLM_VIRTUAL_KEY environment variable not set")

    headers = {"Authorization": f"Bearer {VIRTUAL_KEY}"}
    ```

=== "JavaScript"

    ```javascript
    const VIRTUAL_KEY = process.env.SAAS_LITELLM_VIRTUAL_KEY;

    if (!VIRTUAL_KEY) {
      throw new Error("SAAS_LITELLM_VIRTUAL_KEY environment variable not set");
    }

    const headers = {
      "Authorization": `Bearer ${VIRTUAL_KEY}`
    };
    ```

=== ".env File"

    ```bash
    # .env
    SAAS_LITELLM_VIRTUAL_KEY=sk-1234567890abcdef1234567890abcdef
    ```

### 2. Secrets Management

Use a secrets management service for production:

- **AWS Secrets Manager** - For AWS deployments
- **Google Secret Manager** - For Google Cloud
- **HashiCorp Vault** - For on-premise or multi-cloud
- **Railway Variables** - For Railway deployments
- **Vercel Environment Variables** - For Vercel deployments

**Example with AWS Secrets Manager:**
```python
import boto3
import json

def get_virtual_key():
    client = boto3.client('secretsmanager', region_name='us-west-2')
    response = client.get_secret_value(SecretId='saas-litellm-virtual-key')
    secret = json.loads(response['SecretString'])
    return secret['virtual_key']

VIRTUAL_KEY = get_virtual_key()
```

### 3. Key Rotation

Rotate virtual keys periodically:

1. **Create a new team** (or update the existing team to generate a new key)
2. **Update your application** to use the new key
3. **Verify the new key works**
4. **Deactivate the old team** (optional)

**Recommended rotation schedule:**
- Development: Every 90 days
- Production: Every 30-60 days
- After any security incident: Immediately

### 4. Separate Keys Per Environment

Use different teams (and thus different virtual keys) for each environment:

```bash
# Development environment
SAAS_LITELLM_VIRTUAL_KEY_DEV=sk-dev-key-here

# Staging environment
SAAS_LITELLM_VIRTUAL_KEY_STAGING=sk-staging-key-here

# Production environment
SAAS_LITELLM_VIRTUAL_KEY_PROD=sk-prod-key-here
```

### 5. Least Privilege Access

- **Separate teams for different applications** - Don't share keys across apps
- **Limit model access** - Only grant access to models the team needs
- **Set appropriate credit limits** - Prevent runaway costs
- **Monitor usage** - Track which teams are using the most resources

### 6. Never Expose Keys

**❌ DON'T:**
- Commit keys to version control
- Include keys in client-side code (JavaScript in browsers)
- Log keys in application logs
- Share keys via email or chat
- Store keys in plaintext files

**✅ DO:**
- Use environment variables or secrets management
- Keep keys on the server-side only
- Use `.gitignore` for `.env` files
- Rotate keys regularly
- Audit key usage

### 7. HTTPS Only

**Always use HTTPS in production:**

```python
# ❌ Development only
API_URL = "http://localhost:8003/api"

# ✅ Production
API_URL = "https://api.your-saas.com/api"
```

HTTP transmits the virtual key in plaintext, which is vulnerable to interception.

## Testing Authentication

### Health Check (No Auth Required)

Test that the API is reachable:

```bash
curl http://localhost:8003/health
```

Expected response:
```json
{"status": "healthy"}
```

### Authenticated Request

Test that your virtual key works:

```bash
curl -X POST http://localhost:8003/api/jobs/create \
  -H "Authorization: Bearer sk-your-virtual-key" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "acme-corp",
    "job_type": "test"
  }'
```

Expected response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-10-14T12:00:00Z"
}
```

### Check Team Info

Verify your team exists and is active:

```bash
curl http://localhost:8003/api/teams/acme-corp
```

Expected response:
```json
{
  "team_id": "acme-corp",
  "organization_id": "org_acme",
  "status": "active",
  "credits_remaining": 850,
  "credits_allocated": 1000
}
```

## Error Handling

### Retry Logic

Implement retry logic for transient authentication errors:

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST", "GET"]
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# Use the session
session = create_session_with_retries()
headers = {"Authorization": f"Bearer {VIRTUAL_KEY}"}

response = session.post(
    "http://localhost:8003/api/jobs/create",
    headers=headers,
    json={"team_id": "acme-corp", "job_type": "test"}
)
```

### Handling 401/403 Errors

```python
import requests

def make_authenticated_request(endpoint, data):
    headers = {"Authorization": f"Bearer {VIRTUAL_KEY}"}

    try:
        response = requests.post(
            f"{API_URL}/{endpoint}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication failed. Check your virtual key.")
            # Maybe try to refresh the key or notify admin
        elif e.response.status_code == 403:
            print("Access denied. Check team status and credits.")
            # Maybe check credit balance or team status
        else:
            print(f"HTTP error: {e}")
        raise

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

# Usage
result = make_authenticated_request("jobs/create", {
    "team_id": "acme-corp",
    "job_type": "test"
})
```

## Advanced Topics

### Custom Authentication Middleware

If you're building a wrapper service, you might want custom authentication:

```python
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

async def verify_virtual_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """Verify the virtual key and return team_id"""
    virtual_key = credentials.credentials

    # Verify with SaaS API
    response = requests.get(
        f"http://localhost:8003/api/teams/verify",
        headers={"Authorization": f"Bearer {virtual_key}"}
    )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid virtual key")

    return response.json()["team_id"]

@app.post("/my-endpoint")
async def my_endpoint(team_id: str = Security(verify_virtual_key)):
    return {"message": f"Authenticated as team: {team_id}"}
```

### Caching Team Info

Cache team information to reduce authentication overhead:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_team_info(virtual_key: str, cache_time: int):
    """
    Cache team info for 5 minutes.
    cache_time is passed to invalidate cache every 5 minutes.
    """
    response = requests.get(
        f"http://localhost:8003/api/teams/verify",
        headers={"Authorization": f"Bearer {virtual_key}"}
    )
    return response.json()

# Usage - cache is invalidated every 5 minutes
cache_key = int(time.time() / 300)  # 300 seconds = 5 minutes
team_info = get_team_info(VIRTUAL_KEY, cache_key)
```

## Next Steps

Now that you understand authentication:

1. **[Learn the Job Workflow](job-workflow.md)** - Create jobs and make LLM calls
2. **[Try Non-Streaming Calls](non-streaming.md)** - Standard LLM requests
3. **[Try Streaming Calls](streaming.md)** - Real-time responses
4. **[See Examples](../examples/basic-usage.md)** - Working code examples

## Additional Resources

- **[Error Handling Guide](error-handling.md)** - Comprehensive error handling
- **[Best Practices](best-practices.md)** - Security and performance tips
- **[Admin Dashboard Guide](../admin-dashboard/teams.md)** - Create and manage teams

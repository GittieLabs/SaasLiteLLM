# Provider Credentials API

Manage encrypted LLM provider API keys via REST API.

## Overview

The Provider Credentials API provides CRUD operations for managing encrypted provider API keys at the organization level. All credentials are stored encrypted and can be activated/deactivated without deletion.

!!! info "Authentication Required"
    All provider credentials endpoints require admin authentication. Include your admin JWT token in the Authorization header.

## Endpoints

### List All Credentials

Get all provider credentials in the system.

```http
GET /api/provider-credentials
Authorization: Bearer <admin-token>
```

**Response:**
```json
[
  {
    "credential_id": "cred-uuid-here",
    "organization_id": "org-123",
    "provider": "openai",
    "credential_name": "Production OpenAI Key",
    "api_base": null,
    "is_active": true,
    "created_at": "2025-10-31T12:00:00Z",
    "updated_at": "2025-10-31T12:00:00Z"
  }
]
```

### List Credentials for Organization

Get all provider credentials for a specific organization.

```http
GET /api/provider-credentials/organization/{organization_id}
Authorization: Bearer <admin-token>
```

**Parameters:**
- `organization_id` (path) - Organization ID

**Response:**
```json
[
  {
    "credential_id": "cred-uuid-1",
    "organization_id": "org-123",
    "provider": "openai",
    "credential_name": "Production OpenAI Key",
    "api_base": null,
    "is_active": true,
    "created_at": "2025-10-31T12:00:00Z",
    "updated_at": "2025-10-31T12:00:00Z"
  },
  {
    "credential_id": "cred-uuid-2",
    "organization_id": "org-123",
    "provider": "anthropic",
    "credential_name": "Claude API Key",
    "api_base": null,
    "is_active": true,
    "created_at": "2025-10-31T13:00:00Z",
    "updated_at": "2025-10-31T13:00:00Z"
  }
]
```

### List Credentials by Provider

Get active credentials for a specific provider and organization.

```http
GET /api/provider-credentials/organization/{organization_id}/provider/{provider}
Authorization: Bearer <admin-token>
```

**Parameters:**
- `organization_id` (path) - Organization ID
- `provider` (path) - Provider name: `openai`, `anthropic`, `gemini`, `fireworks`

**Response:**
```json
[
  {
    "credential_id": "cred-uuid-1",
    "organization_id": "org-123",
    "provider": "openai",
    "credential_name": "Production OpenAI Key",
    "api_base": null,
    "is_active": true,
    "created_at": "2025-10-31T12:00:00Z",
    "updated_at": "2025-10-31T12:00:00Z"
  }
]
```

### Create Credential

Create a new provider credential.

```http
POST /api/provider-credentials/create
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "organization_id": "org-123",
  "provider": "openai",
  "credential_name": "Production OpenAI Key",
  "api_key": "sk-proj-...",
  "api_base": null
}
```

**Request Body:**
- `organization_id` (string, required) - Organization ID
- `provider` (string, required) - One of: `openai`, `anthropic`, `gemini`, `fireworks`
- `credential_name` (string, required) - Descriptive name for the credential
- `api_key` (string, required) - Provider API key (will be encrypted)
- `api_base` (string, optional) - Custom API base URL (for proxy setups)

**Response (201 Created):**
```json
{
  "credential_id": "cred-uuid-new",
  "organization_id": "org-123",
  "provider": "openai",
  "credential_name": "Production OpenAI Key",
  "api_base": null,
  "is_active": true,
  "created_at": "2025-10-31T14:00:00Z",
  "updated_at": "2025-10-31T14:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid provider or organization not found
- `422 Unprocessable Entity` - Validation error (missing required fields)

### Get Credential by ID

Get a specific provider credential.

```http
GET /api/provider-credentials/{credential_id}
Authorization: Bearer <admin-token>
```

**Parameters:**
- `credential_id` (path) - Credential UUID

**Response:**
```json
{
  "credential_id": "cred-uuid-1",
  "organization_id": "org-123",
  "provider": "openai",
  "credential_name": "Production OpenAI Key",
  "api_base": null,
  "is_active": true,
  "created_at": "2025-10-31T12:00:00Z",
  "updated_at": "2025-10-31T12:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Credential does not exist

### Update Credential

Update an existing provider credential.

```http
PUT /api/provider-credentials/{credential_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "credential_name": "Updated Credential Name",
  "api_key": "sk-proj-new-key...",
  "api_base": "https://custom-endpoint.com/v1"
}
```

**Parameters:**
- `credential_id` (path) - Credential UUID

**Request Body (all fields optional):**
- `credential_name` (string) - New descriptive name
- `api_key` (string) - New API key (will be encrypted)
- `api_base` (string) - New custom API base URL

**Response:**
```json
{
  "credential_id": "cred-uuid-1",
  "organization_id": "org-123",
  "provider": "openai",
  "credential_name": "Updated Credential Name",
  "api_base": "https://custom-endpoint.com/v1",
  "is_active": true,
  "created_at": "2025-10-31T12:00:00Z",
  "updated_at": "2025-10-31T15:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Credential does not exist

!!! warning "API Key Update"
    When updating the `api_key` field, provide the full new key. The encrypted key is never returned in responses for security reasons.

### Activate Credential

Activate a deactivated credential.

```http
PUT /api/provider-credentials/{credential_id}/activate
Authorization: Bearer <admin-token>
```

**Parameters:**
- `credential_id` (path) - Credential UUID

**Response:**
```json
{
  "credential_id": "cred-uuid-1",
  "organization_id": "org-123",
  "provider": "openai",
  "credential_name": "Production OpenAI Key",
  "api_base": null,
  "is_active": true,
  "created_at": "2025-10-31T12:00:00Z",
  "updated_at": "2025-10-31T16:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Credential does not exist

### Deactivate Credential

Deactivate an active credential (temporarily disable without deletion).

```http
PUT /api/provider-credentials/{credential_id}/deactivate
Authorization: Bearer <admin-token>
```

**Parameters:**
- `credential_id` (path) - Credential UUID

**Response:**
```json
{
  "credential_id": "cred-uuid-1",
  "organization_id": "org-123",
  "provider": "openai",
  "credential_name": "Production OpenAI Key",
  "api_base": null,
  "is_active": false,
  "created_at": "2025-10-31T12:00:00Z",
  "updated_at": "2025-10-31T17:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Credential does not exist

### Delete Credential

Permanently delete a provider credential.

```http
DELETE /api/provider-credentials/{credential_id}
Authorization: Bearer <admin-token>
```

**Parameters:**
- `credential_id` (path) - Credential UUID

**Response:**
```json
{
  "message": "Provider credential deleted successfully"
}
```

**Error Responses:**
- `404 Not Found` - Credential does not exist

!!! danger "Permanent Deletion"
    Deletion is permanent and cannot be undone. If teams are using this credential, their API calls will fail. Consider deactivating instead.

## Security

### Encryption

- **At Rest** - All API keys encrypted using Fernet symmetric encryption
- **In Transit** - HTTPS for all API communications
- **Never Exposed** - Encrypted keys never returned in API responses
- **Audit Trail** - Creation and update timestamps tracked

### Access Control

- **Admin Only** - All endpoints require admin authentication
- **Organization Isolation** - Credentials scoped to organizations
- **JWT Authentication** - Secure token-based authentication

## Usage Examples

### Python

```python
import requests

API_URL = "https://your-saas-api.com"
ADMIN_TOKEN = "your-admin-jwt-token"

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

# Create credential
response = requests.post(
    f"{API_URL}/api/provider-credentials/create",
    headers=headers,
    json={
        "organization_id": "org-123",
        "provider": "openai",
        "credential_name": "Production Key",
        "api_key": "sk-proj-...",
        "api_base": None
    }
)
credential = response.json()
print(f"Created credential: {credential['credential_id']}")

# List organization's credentials
response = requests.get(
    f"{API_URL}/api/provider-credentials/organization/org-123",
    headers=headers
)
credentials = response.json()
print(f"Found {len(credentials)} credentials")

# Deactivate credential
requests.put(
    f"{API_URL}/api/provider-credentials/{credential['credential_id']}/deactivate",
    headers=headers
)
print("Credential deactivated")
```

### JavaScript/TypeScript

```typescript
const API_URL = "https://your-saas-api.com";
const ADMIN_TOKEN = "your-admin-jwt-token";

const headers = {
  "Authorization": `Bearer ${ADMIN_TOKEN}`,
  "Content-Type": "application/json"
};

// Create credential
const response = await fetch(
  `${API_URL}/api/provider-credentials/create`,
  {
    method: "POST",
    headers,
    body: JSON.stringify({
      organization_id: "org-123",
      provider: "anthropic",
      credential_name: "Claude API Key",
      api_key: "sk-ant-...",
      api_base: null
    })
  }
);
const credential = await response.json();
console.log(`Created credential: ${credential.credential_id}`);

// List by provider
const listResponse = await fetch(
  `${API_URL}/api/provider-credentials/organization/org-123/provider/anthropic`,
  { headers }
);
const credentials = await listResponse.json();
console.log(`Found ${credentials.length} Anthropic credentials`);
```

### cURL

```bash
# Create credential
curl -X POST https://your-saas-api.com/api/provider-credentials/create \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org-123",
    "provider": "openai",
    "credential_name": "Production Key",
    "api_key": "sk-proj-...",
    "api_base": null
  }'

# List organization credentials
curl https://your-saas-api.com/api/provider-credentials/organization/org-123 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Activate credential
curl -X PUT https://your-saas-api.com/api/provider-credentials/cred-uuid-1/activate \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Delete credential
curl -X DELETE https://your-saas-api.com/api/provider-credentials/cred-uuid-1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Related Pages

- **[Provider Credentials Admin UI](../admin-dashboard/provider-credentials.md)** - Manage via dashboard
- **[Model Aliases API](models.md)** - Configure model routing
- **[Architecture](../getting-started/architecture.md)** - Understand provider integration
- **[Authentication](../integration/authentication.md)** - API authentication guide

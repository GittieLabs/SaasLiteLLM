# Model Aliases API

Manage model aliases that map user-friendly names to actual LLM provider models.

## Overview

The Model Aliases API provides CRUD operations for creating and managing model aliases. Model aliases allow you to abstract actual provider model names (like `gpt-4o`) behind user-friendly names (like `smart-chat`), enabling you to change underlying models without affecting client code.

!!! info "Direct Provider Integration"
    As of v1.0.0, model aliases no longer require LiteLLM proxy configuration. They map directly to provider models using the direct provider integration system.

## Key Concepts

### What is a Model Alias?

A **model alias** is a custom name that maps to an actual provider model:

- **Alias**: `smart-chat` (what clients use)
- **Provider**: `openai` (which provider)
- **Actual Model**: `gpt-4o` (the real model)
- **Pricing**: Custom pricing (can differ from actual provider cost)

### Benefits

- **Abstraction**: Clients don't need to know actual model names
- **Flexibility**: Change underlying models without client code changes
- **Pricing Control**: Set custom pricing with markup
- **Access Control**: Limit which teams can use which models

## Endpoints

### List All Model Aliases

Get all model aliases in the system.

```http
GET /api/models
Authorization: Bearer <admin-token>
```

**Optional Query Parameters:**
- `provider` - Filter by provider (openai, anthropic, gemini, fireworks)
- `status` - Filter by status (active, inactive)

**Response:**
```json
[
  {
    "id": 1,
    "model_alias": "smart-chat",
    "display_name": "Smart Chat Model",
    "provider": "openai",
    "actual_model": "gpt-4o",
    "description": "Fast, intelligent chat model",
    "pricing_input": 2.5,
    "pricing_output": 10.0,
    "status": "active",
    "access_groups": ["default", "premium"],
    "created_at": "2025-10-31T12:00:00Z",
    "updated_at": "2025-10-31T12:00:00Z"
  }
]
```

### Get Model Alias by Name

Get a specific model alias.

```http
GET /api/models/{alias}
Authorization: Bearer <admin-token>
```

**Parameters:**
- `alias` (path) - Model alias name

**Response:**
```json
{
  "id": 1,
  "model_alias": "smart-chat",
  "display_name": "Smart Chat Model",
  "provider": "openai",
  "actual_model": "gpt-4o",
  "description": "Fast, intelligent chat model",
  "pricing_input": 2.5,
  "pricing_output": 10.0,
  "status": "active",
  "access_groups": ["default", "premium"],
  "created_at": "2025-10-31T12:00:00Z",
  "updated_at": "2025-10-31T12:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Model alias does not exist

### Create Model Alias

Create a new model alias.

```http
POST /api/models/create
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "model_alias": "budget-chat",
  "display_name": "Budget Chat Model",
  "provider": "openai",
  "actual_model": "gpt-4o-mini",
  "description": "Cost-effective chat model",
  "pricing_input": 0.15,
  "pricing_output": 0.60,
  "access_groups": ["default"]
}
```

**Request Body:**
- `model_alias` (string, required) - Unique alias name (lowercase, hyphens allowed)
- `display_name` (string, required) - Human-readable name
- `provider` (string, required) - Provider: `openai`, `anthropic`, `gemini`, `fireworks`
- `actual_model` (string, required) - Actual provider model ID
- `description` (string, optional) - Description of the model
- `pricing_input` (number, required) - Input price in $/million tokens
- `pricing_output` (number, required) - Output price in $/million tokens
- `access_groups` (array, optional) - List of access group names (default: [])

**Response (200 OK):**
```json
{
  "id": 2,
  "model_alias": "budget-chat",
  "display_name": "Budget Chat Model",
  "provider": "openai",
  "actual_model": "gpt-4o-mini",
  "description": "Cost-effective chat model",
  "pricing_input": 0.15,
  "pricing_output": 0.60,
  "status": "active",
  "access_groups": ["default"],
  "created_at": "2025-10-31T14:00:00Z",
  "updated_at": "2025-10-31T14:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Model alias already exists or invalid provider
- `422 Unprocessable Entity` - Validation error (missing required fields)

### Update Model Alias

Update an existing model alias.

```http
PUT /api/models/{alias}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "display_name": "Updated Display Name",
  "description": "Updated description",
  "pricing_input": 0.20,
  "pricing_output": 0.80
}
```

**Parameters:**
- `alias` (path) - Model alias name

**Request Body (all fields optional):**
- `display_name` (string) - New display name
- `description` (string) - New description
- `actual_model` (string) - Change underlying model
- `pricing_input` (number) - New input pricing
- `pricing_output` (number) - New output pricing
- `access_groups` (array) - Update access groups
- `status` (string) - Change status (active, inactive)

**Response:**
```json
{
  "id": 2,
  "model_alias": "budget-chat",
  "display_name": "Updated Display Name",
  "provider": "openai",
  "actual_model": "gpt-4o-mini",
  "description": "Updated description",
  "pricing_input": 0.20,
  "pricing_output": 0.80,
  "status": "active",
  "access_groups": ["default"],
  "created_at": "2025-10-31T14:00:00Z",
  "updated_at": "2025-10-31T16:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Model alias does not exist

### Delete Model Alias

Permanently delete a model alias.

```http
DELETE /api/models/{alias}
Authorization: Bearer <admin-token>
```

**Parameters:**
- `alias` (path) - Model alias name

**Response:**
```json
{
  "message": "Model alias 'budget-chat' deleted successfully"
}
```

**Error Responses:**
- `404 Not Found` - Model alias does not exist

!!! danger "Permanent Deletion"
    Deletion is permanent. If teams are using this model alias, their API calls will fail. Consider setting status to "inactive" instead.

## Auto-Pricing from Catalog

!!! info "New in v1.0.0"
    The admin dashboard now includes a provider model catalog with auto-populated pricing from `llm_pricing_current.json`.

When creating model aliases via the admin dashboard, pricing is automatically populated based on the selected provider model:

**Example:**
1. Select provider: `openai`
2. Choose model: `gpt-4o` from dropdown
3. Pricing auto-fills:
   - Input: $2.50 / M tokens
   - Output: $10.00 / M tokens
4. Optionally adjust pricing with markup
5. Create alias

## Provider Model Catalog

The system maintains a catalog of 40+ models with current pricing:

### OpenAI Models
- GPT-5, GPT-5 Mini, GPT-5 Nano
- GPT-4.1, GPT-4.1 Mini, GPT-4.1 Nano
- GPT-4o, GPT-4o Mini
- o3, o4-mini (reasoning models)

### Anthropic Models
- Claude Opus 4.1, Claude Opus 4
- Claude Sonnet 4.5, Claude Sonnet 4, Claude Sonnet 3.7
- Claude Haiku 4.5, Claude Haiku 3.5, Claude Haiku 3

### Google Gemini Models
- Gemini 2.5 Pro, Flash, Flash Lite
- Gemini 2.0 Pro, Flash, Flash Lite
- Gemini 1.5 Pro, Flash

### Fireworks AI Models
- Llama 3.3 70B, Llama 3.1 405B/70B/8B
- DeepSeek R1 (reasoning)
- Qwen 2.5 72B
- Mixtral 8x22B, 8x7B
- Phi-3 Vision, FireLLaVA (vision models)

## Access Control

Model aliases can be restricted to specific access groups:

### Assigning Access Groups

```json
{
  "model_alias": "premium-model",
  "access_groups": ["premium", "enterprise"]
}
```

Only teams in the "premium" or "enterprise" access groups can use this model.

### Default Access

If `access_groups` is empty or omitted, all teams can use the model alias.

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

# Create model alias
response = requests.post(
    f"{API_URL}/api/models/create",
    headers=headers,
    json={
        "model_alias": "fast-analysis",
        "display_name": "Fast Analysis Model",
        "provider": "gemini",
        "actual_model": "gemini-2.5-flash",
        "description": "Fast and cost-effective analysis",
        "pricing_input": 0.075,
        "pricing_output": 0.30,
        "access_groups": []
    }
)
alias = response.json()
print(f"Created alias: {alias['model_alias']}")

# List all aliases
response = requests.get(
    f"{API_URL}/api/models",
    headers=headers
)
aliases = response.json()
print(f"Found {len(aliases)} model aliases")

# Update pricing
requests.put(
    f"{API_URL}/api/models/fast-analysis",
    headers=headers,
    json={
        "pricing_input": 0.10,
        "pricing_output": 0.40
    }
)
print("Pricing updated with markup")
```

### JavaScript/TypeScript

```typescript
const API_URL = "https://your-saas-api.com";
const ADMIN_TOKEN = "your-admin-jwt-token";

const headers = {
  "Authorization": `Bearer ${ADMIN_TOKEN}`,
  "Content-Type": "application/json"
};

// Create model alias
const response = await fetch(
  `${API_URL}/api/models/create`,
  {
    method: "POST",
    headers,
    body: JSON.stringify({
      model_alias: "reasoning-model",
      display_name: "Advanced Reasoning",
      provider: "openai",
      actual_model: "o3",
      description: "For complex reasoning tasks",
      pricing_input: 1.0,
      pricing_output: 4.0,
      access_groups: ["premium"]
    })
  }
);
const alias = await response.json();
console.log(`Created alias: ${alias.model_alias}`);

// Get specific alias
const getResponse = await fetch(
  `${API_URL}/api/models/reasoning-model`,
  { headers }
);
const model = await getResponse.json();
console.log(`Model: ${model.actual_model} at $${model.pricing_input}/$${model.pricing_output}`);
```

### cURL

```bash
# Create model alias
curl -X POST https://your-saas-api.com/api/models/create \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_alias": "doc-analyzer",
    "display_name": "Document Analyzer",
    "provider": "anthropic",
    "actual_model": "claude-sonnet-4-5",
    "description": "For document analysis",
    "pricing_input": 3.0,
    "pricing_output": 15.0,
    "access_groups": ["default"]
  }'

# List all model aliases
curl https://your-saas-api.com/api/models \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by provider
curl "https://your-saas-api.com/api/models?provider=openai" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Update model alias
curl -X PUT https://your-saas-api.com/api/models/doc-analyzer \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pricing_input": 4.0,
    "pricing_output": 20.0
  }'

# Delete model alias
curl -X DELETE https://your-saas-api.com/api/models/doc-analyzer \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Best Practices

### Naming Conventions

✅ **DO:**
- Use descriptive, purpose-based names: `document-analyzer`, `chat-assistant`
- Use lowercase with hyphens: `smart-chat`, not `SmartChat`
- Keep aliases short but meaningful
- Include model tier if applicable: `chat-premium`, `chat-budget`

❌ **DON'T:**
- Use provider model names: `gpt-4o` (defeats the purpose of aliases)
- Use unclear abbreviations: `sc1`, `mdl-a`
- Mix naming conventions
- Change alias names frequently (breaks client code)

### Pricing Strategy

✅ **DO:**
- Start with provider pricing and add markup
- Group similar-capability models at same price point
- Document pricing rationale
- Review pricing quarterly
- Consider volume discounts for high-usage teams

❌ **DON'T:**
- Price below cost (unless intentional loss leader)
- Price inconsistently across similar models
- Change pricing without notice
- Forget to account for context window differences

### Model Selection

✅ **DO:**
- Test models before creating aliases
- Consider latency requirements
- Match model capabilities to use case
- Provide budget and premium tiers
- Document model strengths/weaknesses

❌ **DON'T:**
- Create aliases for every provider model
- Use outdated models
- Ignore context window limits
- Overlook cost differences

## Related Pages

- **[Model Aliases Admin UI](../admin-dashboard/model-aliases.md)** - Manage via dashboard
- **[Model Pricing](../admin-dashboard/pricing.md)** - View provider pricing
- **[Provider Credentials](provider-credentials.md)** - Configure provider access
- **[Model Access Groups](../admin-dashboard/model-access-groups.md)** - Control team access
- **[Architecture](../getting-started/architecture.md)** - Understand model resolution

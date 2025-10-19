# Model Access Groups

Learn how to control which LLM models your clients can access using model access groups.

## What are Model Access Groups?

**Model Access Groups** are collections of model aliases that define which LLMs a team can use. They provide granular access control and enable tiered pricing strategies.

!!! info "Built on LiteLLM"
    SaaS LiteLLM uses [LiteLLM](https://docs.litellm.ai) for routing to 100+ LLM providers. Model access groups control which of these providers and models your teams can access.

**Key Benefits:**
- ✅ Control costs by limiting expensive models
- ✅ Create pricing tiers (Basic, Pro, Enterprise)
- ✅ Grant access to specific providers (OpenAI, Anthropic, etc.)
- ✅ Simplify team management
- ✅ Implement progressive access upgrades

## How Model Access Groups Work

```
Team → Access Groups → Model Aliases → Actual LLM Models
```

**Example:**
```
Team: "acme-prod"
  └── Access Groups: ["gpt-models", "claude-models"]
       ├── gpt-models
       │    ├── gpt-4 → openai/gpt-4
       │    └── gpt-3.5-turbo → openai/gpt-3.5-turbo
       │
       └── claude-models
            ├── claude-3-opus → anthropic/claude-3-opus-20240229
            └── claude-3-sonnet → anthropic/claude-3-sonnet-20240229
```

The team can now use models: `gpt-4`, `gpt-3.5-turbo`, `claude-3-opus`, `claude-3-sonnet`

[:octicons-arrow-right-24: Learn more about model aliases](model-aliases.md)

## Creating Model Access Groups

![Model Access Groups](../images/model-access-groups.png)
*Model Access Groups interface - control which models teams can access*

### Via Admin Dashboard

1. **Navigate to Model Access**
   - Click "Model Access" in sidebar
   - Click "Create Access Group"

2. **Fill in Details**
   - **Group Name**: `gpt-models` (lowercase, hyphens)
   - **Description**: "OpenAI GPT models"
   - **Model Aliases**: Select models to include

3. **Save**
   - Click "Create"
   - Group is ready to assign to teams

### Via API

```bash
curl -X POST http://localhost:8003/api/model-access-groups/create \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "gpt-models",
    "description": "OpenAI GPT models",
    "model_aliases": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
  }'
```

**Response:**
```json
{
  "group_name": "gpt-models",
  "description": "OpenAI GPT models",
  "model_aliases": [
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-4-turbo"
  ],
  "created_at": "2024-10-14T12:00:00Z"
}
```

## Common Access Group Setups

### Setup 1: By Provider

Group models by AI provider:

**OpenAI Models:**
```json
{
  "group_name": "openai-models",
  "description": "All OpenAI models",
  "model_aliases": [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-3.5-turbo"
  ]
}
```

**Anthropic Models:**
```json
{
  "group_name": "anthropic-models",
  "description": "All Anthropic Claude models",
  "model_aliases": [
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku"
  ]
}
```

**Google Models:**
```json
{
  "group_name": "google-models",
  "description": "Google Gemini models",
  "model_aliases": [
    "gemini-pro",
    "gemini-1.5-pro"
  ]
}
```

### Setup 2: By Pricing Tier

Group models by cost/capabilities for tiered pricing:

**Basic Tier (Fast & Cheap):**
```json
{
  "group_name": "basic-models",
  "description": "Fast, cost-effective models",
  "model_aliases": [
    "gpt-3.5-turbo",
    "claude-3-haiku"
  ]
}
```

**Professional Tier (Balanced):**
```json
{
  "group_name": "pro-models",
  "description": "Balanced performance and cost",
  "model_aliases": [
    "gpt-4-turbo",
    "claude-3-sonnet",
    "gemini-pro"
  ]
}
```

**Enterprise Tier (Most Capable):**
```json
{
  "group_name": "enterprise-models",
  "description": "Most capable models",
  "model_aliases": [
    "gpt-4",
    "claude-3-opus",
    "gemini-1.5-pro"
  ]
}
```

### Setup 3: By Use Case

Group models by intended application:

**Chat/Conversational:**
```json
{
  "group_name": "chat-models",
  "description": "Optimized for conversation",
  "model_aliases": [
    "gpt-3.5-turbo",
    "claude-3-sonnet"
  ]
}
```

**Analysis/Complex Tasks:**
```json
{
  "group_name": "analysis-models",
  "description": "Complex reasoning and analysis",
  "model_aliases": [
    "gpt-4",
    "claude-3-opus"
  ]
}
```

**Fast Tasks:**
```json
{
  "group_name": "fast-models",
  "description": "Quick responses for simple tasks",
  "model_aliases": [
    "gpt-3.5-turbo",
    "claude-3-haiku"
  ]
}
```

## Assigning Access Groups to Teams

### During Team Creation

```bash
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme",
    "team_id": "acme-prod",
    "team_alias": "Production",
    "access_groups": ["gpt-models", "claude-models"],
    "credits_allocated": 1000
  }'
```

### Update Existing Team

```bash
curl -X PUT http://localhost:8003/api/teams/acme-prod \
  -H "Content-Type: application/json" \
  -d '{
    "access_groups": ["gpt-models", "claude-models", "gemini-models"]
  }'
```

**Via Dashboard:**
1. Navigate to team
2. Click "Edit Access Groups"
3. Select/deselect groups
4. Click "Save"

## Viewing Access Groups

### List All Access Groups

**Via Dashboard:**
- Navigate to "Model Access"
- See all access groups with model counts

**Via API:**
```bash
curl http://localhost:8003/api/model-access-groups
```

**Response:**
```json
{
  "access_groups": [
    {
      "group_name": "gpt-models",
      "description": "OpenAI GPT models",
      "model_count": 3,
      "team_count": 15
    },
    {
      "group_name": "claude-models",
      "description": "Anthropic Claude models",
      "model_count": 3,
      "team_count": 8
    }
  ]
}
```

### View Access Group Details

```bash
curl http://localhost:8003/api/model-access-groups/gpt-models
```

**Response:**
```json
{
  "group_name": "gpt-models",
  "description": "OpenAI GPT models",
  "model_aliases": [
    {
      "alias": "gpt-4",
      "litellm_model": "openai/gpt-4",
      "description": "Most capable GPT-4 model"
    },
    {
      "alias": "gpt-3.5-turbo",
      "litellm_model": "openai/gpt-3.5-turbo",
      "description": "Fast and efficient"
    }
  ],
  "teams_with_access": [
    "acme-prod",
    "techco-dev",
    "client-staging"
  ]
}
```

## Managing Access Groups

### Add Models to Group

```bash
curl -X POST http://localhost:8003/api/model-access-groups/gpt-models/add-models \
  -H "Content-Type: application/json" \
  -d '{
    "model_aliases": ["gpt-4-vision"]
  }'
```

### Remove Models from Group

```bash
curl -X POST http://localhost:8003/api/model-access-groups/gpt-models/remove-models \
  -H "Content-Type: application/json" \
  -d '{
    "model_aliases": ["gpt-3.5-turbo"]
  }'
```

### Delete Access Group

!!! danger "Warning"
    Deleting an access group will remove it from all teams. Teams will lose access to models in this group unless they have the models through other access groups.

```bash
curl -X DELETE http://localhost:8003/api/model-access-groups/old-models
```

## Pricing Strategies Using Access Groups

### Strategy 1: Tiered Plans

Offer different plans with different model access:

**Starter Plan - $99/month**
```json
{
  "access_groups": ["basic-models"],
  "credits_allocated": 1000
}
```
- Access: GPT-3.5-turbo, Claude 3 Haiku
- Best for: Simple tasks, high volume

**Professional Plan - $299/month**
```json
{
  "access_groups": ["basic-models", "pro-models"],
  "credits_allocated": 5000
}
```
- Access: All basic + GPT-4-turbo, Claude 3 Sonnet
- Best for: Complex tasks, balanced performance

**Enterprise Plan - $999/month**
```json
{
  "access_groups": ["basic-models", "pro-models", "enterprise-models"],
  "credits_allocated": 20000
}
```
- Access: All models including GPT-4, Claude 3 Opus
- Best for: Maximum capabilities

### Strategy 2: Provider-Based Pricing

Charge based on provider access:

**OpenAI Only - $149/month**
```json
{
  "access_groups": ["openai-models"],
  "credits_allocated": 2000
}
```

**Multi-Provider - $299/month**
```json
{
  "access_groups": ["openai-models", "anthropic-models", "google-models"],
  "credits_allocated": 5000
}
```

### Strategy 3: Use Case Bundles

Bundle models by intended use:

**Chat Bundle - $199/month**
```json
{
  "access_groups": ["chat-models"],
  "credits_allocated": 3000
}
```

**Analysis Bundle - $399/month**
```json
{
  "access_groups": ["analysis-models", "chat-models"],
  "credits_allocated": 5000
}
```

## Team Model Access Workflow

### When Team Makes API Call

1. **Team sends request:**
   ```bash
   POST /api/jobs/{job_id}/llm-call
   {
     "model": "gpt-4",
     "messages": [...]
   }
   ```

2. **SaaS API checks:**
   - Does team have "gpt-4" in any access group? ✅
   - Is team active? ✅
   - Does team have credits? ✅

3. **SaaS API resolves:**
   - `gpt-4` → `openai/gpt-4` (via model alias)

4. **Routes to LiteLLM:**
   - LiteLLM routes to actual OpenAI API
   - Response returns through chain

5. **If access denied:**
   ```json
   {
     "error": "Model access denied",
     "message": "Team does not have access to model 'gpt-4'",
     "available_models": ["gpt-3.5-turbo", "claude-3-haiku"]
   }
   ```

## Common Workflows

### Workflow 1: Upgrade Team to Higher Tier

Client wants access to more powerful models:

```bash
# 1. Check current access
curl http://localhost:8003/api/teams/acme-prod

# 2. Update access groups
curl -X PUT http://localhost:8003/api/teams/acme-prod \
  -d '{
    "access_groups": ["basic-models", "pro-models", "enterprise-models"]
  }'

# 3. Add more credits for higher usage
curl -X POST http://localhost:8003/api/credits/add \
  -d '{
    "team_id": "acme-prod",
    "amount": 10000
  }'
```

### Workflow 2: Create Custom Access for Enterprise Client

Enterprise client wants specific models:

```bash
# 1. Create custom access group
curl -X POST http://localhost:8003/api/model-access-groups/create \
  -d '{
    "group_name": "acme-custom",
    "description": "Custom models for ACME Corp",
    "model_aliases": [
      "gpt-4",
      "claude-3-opus",
      "gemini-1.5-pro"
    ]
  }'

# 2. Assign to team
curl -X PUT http://localhost:8003/api/teams/acme-prod \
  -d '{
    "access_groups": ["acme-custom"]
  }'
```

### Workflow 3: Temporarily Grant Access for Testing

Client wants to test a new model:

```bash
# 1. Add access group temporarily
curl -X PUT http://localhost:8003/api/teams/acme-dev \
  -d '{
    "access_groups": ["current-models", "experimental-models"]
  }'

# 2. Monitor usage

# 3. Remove after testing
curl -X PUT http://localhost:8003/api/teams/acme-dev \
  -d '{
    "access_groups": ["current-models"]
  }'
```

## Best Practices

### Naming Conventions

**Access Group Names:**
- Use lowercase with hyphens
- Be descriptive: `gpt-models`, `premium-models`, `chat-optimized`
- Use consistent prefixes for organization: `tier-basic`, `tier-pro`, `tier-enterprise`

### Organization

1. **Start with Provider Groups**
   - Create one group per provider (OpenAI, Anthropic, Google)
   - Easy to understand and manage

2. **Add Tier Groups as You Grow**
   - Basic, Professional, Enterprise
   - Maps to pricing plans

3. **Create Use Case Groups for Specific Clients**
   - Custom bundles for enterprise clients
   - Special access for partners

### Access Control

1. **Principle of Least Privilege**
   - Start teams with minimal access
   - Upgrade as needed
   - Don't grant all models by default

2. **Separate Dev and Prod**
   - Dev teams: cheaper models for testing
   - Prod teams: full access to needed models

3. **Monitor and Adjust**
   - Track which models teams actually use
   - Remove unused access groups
   - Identify upgrade opportunities

### Cost Management

1. **Group by Cost**
   - Create "expensive-models" group
   - Restrict to paying customers only
   - Monitor usage of costly models

2. **Gradual Rollout**
   - New models → small test group first
   - Monitor costs and performance
   - Expand access gradually

3. **Sunset Old Models**
   - Remove deprecated models from groups
   - Notify teams before removal
   - Provide migration path

## Troubleshooting

### Team Can't Access Model

**Problem:** Client reports "Model access denied" for `gpt-4`

**Solutions:**
1. Check team's access groups:
   ```bash
   curl http://localhost:8003/api/teams/acme-prod
   ```

2. Check if any access group contains the model:
   ```bash
   curl http://localhost:8003/api/model-access-groups/gpt-models
   ```

3. Add missing access group:
   ```bash
   curl -X PUT http://localhost:8003/api/teams/acme-prod \
     -d '{"access_groups": ["existing-groups", "gpt-models"]}'
   ```

### Model Alias Not Found

**Problem:** Access group won't accept model alias

**Solutions:**
1. Verify model alias exists:
   ```bash
   curl http://localhost:8003/api/model-aliases
   ```

2. Create model alias if missing:
   ```bash
   curl -X POST http://localhost:8003/api/model-aliases/create \
     -d '{
       "alias": "gpt-4",
       "litellm_model": "openai/gpt-4",
       "description": "GPT-4"
     }'
   ```

3. Add to access group:
   ```bash
   curl -X POST http://localhost:8003/api/model-access-groups/gpt-models/add-models \
     -d '{"model_aliases": ["gpt-4"]}'
   ```

### Access Group Changes Not Taking Effect

**Problem:** Updated access groups but team still can't access model

**Solutions:**
1. Verify update succeeded:
   ```bash
   curl http://localhost:8003/api/teams/acme-prod
   ```

2. Check model is in the access group:
   ```bash
   curl http://localhost:8003/api/model-access-groups/gpt-models
   ```

3. Restart SaaS API server if needed (rare):
   ```bash
   docker compose restart saas-api
   ```

## Example: Complete Client Onboarding with Access Control

```bash
# 1. Create organization
curl -X POST http://localhost:8003/api/organizations/create \
  -d '{
    "organization_id": "org_newclient",
    "name": "New Client Inc"
  }'

# 2. Create access groups (if not exists)
curl -X POST http://localhost:8003/api/model-access-groups/create \
  -d '{
    "group_name": "starter-models",
    "description": "Starter tier models",
    "model_aliases": ["gpt-3.5-turbo", "claude-3-haiku"]
  }'

# 3. Create team with access
curl -X POST http://localhost:8003/api/teams/create \
  -d '{
    "organization_id": "org_newclient",
    "team_id": "newclient-prod",
    "team_alias": "Production",
    "access_groups": ["starter-models"],
    "credits_allocated": 1000
  }'

# 4. Share virtual key with client
# (From response above)

# 5. Later: Upgrade to pro tier
curl -X PUT http://localhost:8003/api/teams/newclient-prod \
  -d '{
    "access_groups": ["starter-models", "pro-models"]
  }'

# 6. Add more credits
curl -X POST http://localhost:8003/api/credits/add \
  -d '{
    "team_id": "newclient-prod",
    "amount": 5000
  }'
```

## Next Steps

Now that you understand model access groups:

1. **[Configure Model Aliases](model-aliases.md)** - Set up the actual models
2. **[Create Teams](teams.md)** - Assign access groups to teams
3. **[Monitor Usage](monitoring.md)** - Track which models are used most
4. **[Best Practices](best-practices.md)** - Advanced access control patterns

## Quick Reference

### Create Access Group
```bash
POST /api/model-access-groups/create
{
  "group_name": "gpt-models",
  "description": "OpenAI GPT models",
  "model_aliases": ["gpt-4", "gpt-3.5-turbo"]
}
```

### Assign to Team
```bash
PUT /api/teams/{team_id}
{
  "access_groups": ["gpt-models", "claude-models"]
}
```

### Add Models to Group
```bash
POST /api/model-access-groups/{group_name}/add-models
{
  "model_aliases": ["new-model"]
}
```

### View Group Details
```bash
GET /api/model-access-groups/{group_name}
```

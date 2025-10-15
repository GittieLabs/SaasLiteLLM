# Complete Integration Flow

This guide explains how all components of SaasLiteLLM work together, from admin setup to end-user requests.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ADMIN SETUP PHASE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Admin → LiteLLM UI (Port 8002)                              │
│     - Add provider credentials (OpenAI, Anthropic, etc.)        │
│     - Configure models (gpt-4, claude-3-sonnet, etc.)           │
│     - Test models in playground                                  │
│                                                                  │
│  2. Admin → SaaS Admin Panel (Port 3000)                        │
│     - Create organizations                                       │
│     - Create model groups (referencing LiteLLM models)          │
│     - Create teams with budgets                                  │
│     - Assign model groups to teams                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     END USER REQUEST PHASE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client Application                                              │
│         │                                                         │
│         │ (1) Uses team's virtual_key                           │
│         ▼                                                         │
│  SaaS API (Port 8003)                                           │
│         │                                                         │
│         │ (2) Validates key, checks credits, tracks job         │
│         ▼                                                         │
│  LiteLLM Proxy (Port 8002)                                      │
│         │                                                         │
│         │ (3) Routes to provider, tracks costs                  │
│         ▼                                                         │
│  LLM Provider (OpenAI, Anthropic, etc.)                         │
│         │                                                         │
│         │ (4) Returns completion                                 │
│         ▼                                                         │
│  Response flows back to client                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication Keys

Understanding the different keys is crucial:

### 1. MASTER_KEY (SaaS API Admin Key)

**Purpose**: Admin access to SaaS API management endpoints

**Used for**:
- Creating organizations
- Creating teams
- Creating model groups
- Adding credits
- Viewing usage reports

**Used by**: System administrators via admin panel or API calls

**Configured in**: `saas-api/.env` → `MASTER_KEY`

**Example**:
```bash
curl -X POST http://localhost:8003/api/organizations/create \
  -H "X-Admin-Key: sk-admin-your-master-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "litellm_organization_id": "acme"}'
```

**Security**:
- ⚠️ **Never** expose to end users
- Store securely (environment variables, secrets manager)
- Rotate quarterly
- Different from LITELLM_MASTER_KEY

### 2. LITELLM_MASTER_KEY (LiteLLM Admin Key)

**Purpose**: Admin access to LiteLLM proxy management

**Used for**:
- Accessing LiteLLM UI
- SaaS API creating virtual keys for teams
- Managing models and credentials in LiteLLM
- Direct LiteLLM API access (admin only)

**Used by**:
- Admins accessing LiteLLM UI
- SaaS API (programmatically)

**Configured in**: Both `saas-api/.env` and `litellm/.env` → `LITELLM_MASTER_KEY`

**Example**:
```bash
# Access LiteLLM UI
http://localhost:8002/ui
# Login with: LITELLM_MASTER_KEY value

# Direct API call
curl -X POST http://localhost:8002/chat/completions \
  -H "Authorization: Bearer sk-litellm-your-master-key" \
  -d '{"model": "gpt-3.5-turbo", "messages": [...]}'
```

**Security**:
- ⚠️ **Never** expose to end users
- Must be the same in both SaaS API and LiteLLM .env files
- Used by SaaS API to create team virtual keys
- Rotate quarterly

### 3. Virtual Keys (Team Keys)

**Purpose**: Team-specific access to LiteLLM with budget/model controls

**Used for**:
- End users making LLM requests
- Enforcing budget limits per team
- Restricting model access per team
- Tracking usage per team

**Created by**: SaaS API automatically when creating a team

**Used by**: End-user applications (your SaaS customers)

**Example**:
```bash
# Your customer's application uses their team's virtual key
curl -X POST http://localhost:8002/chat/completions \
  -H "Authorization: Bearer sk-litellm-virtual-key-team-abc-123" \
  -d '{"model": "gpt-3.5-turbo", "messages": [...]}'
```

**Security**:
- ✅ **Safe** to give to end users
- Budget-limited (can't overspend)
- Model-limited (only assigned models)
- Rate-limited (RPM/TPM limits)
- Tracked per team

## Setup Flow (Admin Perspective)

### Phase 1: Infrastructure Setup

1. **Deploy services** (Docker Compose, Railway, etc.)
   - PostgreSQL database
   - Redis cache
   - LiteLLM proxy
   - SaaS API
   - Admin panel

2. **Configure environment variables**:
   ```bash
   # Generate strong keys
   MASTER_KEY=$(openssl rand -hex 32)
   LITELLM_MASTER_KEY=$(openssl rand -hex 32)

   # Set in .env files
   # saas-api/.env
   MASTER_KEY=sk-admin-...
   LITELLM_MASTER_KEY=sk-litellm-...

   # litellm/.env
   LITELLM_MASTER_KEY=sk-litellm-...  # Same as SaaS API
   ```

3. **Verify services are running**:
   ```bash
   docker ps
   # Should see: postgres, redis, litellm-proxy, saas-api, admin-panel
   ```

### Phase 2: LiteLLM Configuration (CRITICAL)

**This must be done BEFORE creating teams in SaaS API**

1. **Access LiteLLM UI**: http://localhost:8002/ui
   - Login with `LITELLM_MASTER_KEY`

2. **Add Provider Credentials**:
   - Navigate to **Keys** tab
   - Click **+ Add Key**
   - For each provider you want to use:
     ```
     OpenAI:
       - Key Alias: openai-prod
       - Provider: openai
       - API Key: sk-... (from OpenAI dashboard)

     Anthropic:
       - Key Alias: anthropic-prod
       - Provider: anthropic
       - API Key: sk-ant-... (from Anthropic console)
     ```

3. **Add Models**:
   - Navigate to **Models** tab
   - Click **+ Add Model**
   - For each model you want to offer:
     ```
     Example 1:
       - Model Name: gpt-3.5-turbo
       - LiteLLM Model Name: openai/gpt-3.5-turbo
       - Credential: openai-prod
       - Cost per 1K input tokens: 0.0005
       - Cost per 1K output tokens: 0.0015

     Example 2:
       - Model Name: claude-3-sonnet
       - LiteLLM Model Name: anthropic/claude-3-sonnet-20240229
       - Credential: anthropic-prod
       - Cost per 1K input tokens: 0.003
       - Cost per 1K output tokens: 0.015
     ```

4. **Test Models**:
   - Navigate to **Playground** tab
   - Select each model
   - Send test message: "Hello, are you working?"
   - Verify responses

✅ **Checkpoint**: All models should respond successfully in playground

### Phase 3: SaaS API Configuration

1. **Access Admin Panel**: http://localhost:3000
   - Login with `MASTER_KEY` (from SaaS API .env)

2. **Create Organization**:
   ```
   - Name: Acme Corporation
   - LiteLLM Org ID: acme-corp
   - Description: Main organization
   ```

3. **Create Model Groups**:
   ```
   Group 1 - Basic Tier:
     - Name: basic-models
     - Models: gpt-3.5-turbo
     - Description: Fast, cost-effective models

   Group 2 - Premium Tier:
     - Name: premium-models
     - Models: gpt-4-turbo, claude-3-sonnet, claude-3-opus
     - Description: Most capable models
   ```

   ⚠️ **Important**: Model names must match EXACTLY what you configured in LiteLLM

4. **Create Team**:
   ```
   - Name: Acme Dev Team
   - Organization: Acme Corporation
   - Model Group: basic-models
   - Max Budget: 100.0 (USD/credits)
   - Budget Duration: 30d
   - Rate Limits:
     - RPM: 100
     - TPM: 50000
   ```

5. **Get Team Virtual Key**:
   - After creating team, view team details
   - Copy the `virtual_key` value
   - This is what your customer will use

✅ **Checkpoint**: Team created successfully with virtual_key

## Request Flow (End User Perspective)

### Step 1: Client Gets Team Credentials

Your SaaS application provides the team's virtual key to their application:

```javascript
// Your application provides these to the customer
const teamVirtualKey = "sk-litellm-virtual-key-abc123";
const apiEndpoint = "http://localhost:8002"; // LiteLLM proxy URL
```

### Step 2: Client Makes LLM Request

The customer's application makes requests directly to LiteLLM:

```javascript
const response = await fetch('http://localhost:8002/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${teamVirtualKey}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-3.5-turbo',
    messages: [
      { role: 'user', content: 'Hello, world!' }
    ]
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

### Step 3: LiteLLM Processes Request

Behind the scenes, LiteLLM:

1. **Validates virtual key**: Checks if key exists and is valid
2. **Checks team budget**: Ensures team has enough credits
3. **Checks model access**: Verifies team can use requested model
4. **Checks rate limits**: Ensures RPM/TPM not exceeded
5. **Routes to provider**: Forwards request to OpenAI/Anthropic/etc.
6. **Tracks costs**: Records token usage and costs
7. **Deducts budget**: Updates team's remaining budget
8. **Returns response**: Sends completion back to client

### Step 4: SaaS API Tracks Usage

The SaaS API can query usage data:

```bash
# Admin checks team usage
curl http://localhost:8003/api/teams/{team_id}/usage \
  -H "X-Admin-Key: $MASTER_KEY"

# Response includes:
{
  "team_id": "team_abc123",
  "total_spend": 15.50,
  "remaining_budget": 84.50,
  "request_count": 1234,
  "models_used": {
    "gpt-3.5-turbo": { "requests": 1000, "cost": 10.00 },
    "gpt-4": { "requests": 234, "cost": 5.50 }
  }
}
```

## Budget Management

### How Credits Work

1. **Admin adds credits** to team:
   ```bash
   curl -X POST http://localhost:8003/api/credits/teams/{team_id}/add \
     -H "X-Admin-Key: $MASTER_KEY" \
     -d '{"amount": 100.0, "reason": "Monthly allocation"}'
   ```

2. **LiteLLM tracks spending**:
   - Every request deducts from team budget
   - Cost = (input_tokens * input_cost) + (output_tokens * output_cost)
   - Stored in LiteLLM's database

3. **When budget exhausted**:
   - Team's virtual key stops working
   - Requests return 429 error (quota exceeded)
   - Admin must add more credits

### Budget Modes

Teams can have different budget enforcement modes:

**Hard Limit** (default):
- Requests blocked when budget reached
- Team cannot exceed budget under any circumstance

**Soft Limit**:
- Warning sent when 80% budget used
- Requests still allowed after budget reached
- Useful for enterprise customers with invoicing

## Model Access Control

### How Model Groups Work

1. **Admin creates model group** in SaaS API:
   ```
   Model Group: "premium-models"
   Models: ["gpt-4-turbo", "claude-3-opus"]
   ```

2. **Admin assigns to team**:
   - Team's virtual key is configured in LiteLLM
   - Only specified models are accessible

3. **User requests model**:
   ```javascript
   // ✅ Allowed (model in group)
   { model: "gpt-4-turbo", messages: [...] }

   // ❌ Denied (model not in group)
   { model: "gpt-3.5-turbo", messages: [...] }
   // Returns 403 Forbidden
   ```

### Changing Model Access

To change a team's model access:

1. Update the model group assignment in SaaS API admin panel
2. Or create a new model group and reassign the team
3. Changes take effect immediately
4. No need to regenerate virtual keys

## Monitoring and Observability

### LiteLLM UI Dashboard

Access: http://localhost:8002/ui

**Available views**:
- Usage by team
- Cost breakdown by model
- Request counts and latencies
- Error rates
- Budget remaining per team

### SaaS API Endpoints

**Organization usage**:
```bash
GET /api/organizations/{org_id}/usage
Headers: X-Admin-Key: $MASTER_KEY
```

**Team usage**:
```bash
GET /api/teams/{team_id}/usage
Headers: X-Admin-Key: $MASTER_KEY
```

**All teams usage**:
```bash
GET /api/teams
Headers: X-Admin-Key: $MASTER_KEY
```

### Logs

**LiteLLM logs**:
```bash
docker logs litellm-proxy
# Shows: requests, costs, errors, rate limits
```

**SaaS API logs**:
```bash
docker logs saas-api
# Shows: admin actions, team creation, credit additions
```

## Production Deployment

### Environment Configuration

**Railway** (recommended):

1. **Deploy LiteLLM**:
   - Expose public URL for admin access
   - Use private networking for SaaS API connection
   - Set `LITELLM_MASTER_KEY` in Railway secrets

2. **Deploy SaaS API**:
   - Private networking to LiteLLM
   - Set `MASTER_KEY` and `LITELLM_MASTER_KEY`
   - Set `LITELLM_PROXY_URL` to LiteLLM's internal URL

3. **Deploy Admin Panel**:
   - Public URL for admin access
   - Set `NEXT_PUBLIC_API_URL` to SaaS API URL

### Security Checklist

- [ ] Changed default `MASTER_KEY` to strong random value
- [ ] Changed default `LITELLM_MASTER_KEY` to strong random value
- [ ] LiteLLM UI accessible only via HTTPS
- [ ] Admin panel accessible only via HTTPS
- [ ] Rate limiting enabled in LiteLLM
- [ ] Budget limits set on all teams
- [ ] Monitoring/alerting configured
- [ ] Database backups enabled
- [ ] Provider API keys stored securely
- [ ] No keys committed to git

## Troubleshooting Common Issues

### Issue: "Model not found"

**Cause**: Model name mismatch between SaaS API and LiteLLM

**Solution**:
1. Check model name in SaaS API model group
2. Check model name in LiteLLM UI Models tab
3. Ensure they match exactly (case-sensitive)

### Issue: "Invalid API key"

**Cause**: Team virtual key not working

**Solution**:
1. Verify team exists and has budget
2. Check LiteLLM UI Keys tab for the virtual key
3. Ensure model group is assigned to team
4. Try recreating the team

### Issue: "Quota exceeded"

**Cause**: Team has exhausted budget

**Solution**:
1. Check team's remaining budget in admin panel
2. Add more credits via admin panel
3. Or adjust budget limits for the team

### Issue: SaaS API can't connect to LiteLLM

**Cause**: Network configuration problem

**Solution**:
1. Verify `LITELLM_PROXY_URL` in SaaS API .env
2. Check both services on same Docker network
3. Test connectivity: `curl http://litellm-proxy:8002/health`
4. Verify `LITELLM_MASTER_KEY` matches in both services

## Next Steps

- [LiteLLM Setup Guide](litellm-setup.md) - Detailed LiteLLM configuration
- [API Reference](api-reference/overview.md) - Complete API documentation
- [Deployment Guide](deployment/railway.md) - Production deployment
- [Security Documentation](../SECURITY.md) - Security best practices

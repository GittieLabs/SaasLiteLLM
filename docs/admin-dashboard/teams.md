# Teams

Learn how to create and manage teams - the primary way your clients access the SaaS LiteLLM API.

## What are Teams?

**Teams** are the core access unit in SaaS LiteLLM. Each team gets:

- ✅ Unique **virtual API key** for authentication
- ✅ **Credit allocation** for usage
- ✅ **Model access permissions** via access groups
- ✅ Independent **rate limits** (TPM/RPM)
- ✅ Usage tracking and **cost monitoring**

**Key Point:** Your clients use teams to make API calls. One organization can have multiple teams (e.g., dev, staging, production).

## Creating a Team for a Client

### Quick Start

1. **Navigate to Teams** → Click "Create Team"
2. **Fill in details:**
   - Team ID: `client-prod`
   - Organization: Select client's organization
   - Access Groups: `["gpt-models"]`
   - Credits: `1000`
3. **Click "Create"**
4. **Copy the virtual key** and share with client securely

That's it! Your client can now make API calls.

### Via API

```bash
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_acme",
    "team_id": "acme-prod",
    "team_alias": "ACME Production",
    "access_groups": ["gpt-models"],
    "credits_allocated": 1000
  }'
```

**Response:**
```json
{
  "team_id": "acme-prod",
  "organization_id": "org_acme",
  "team_alias": "ACME Production",
  "virtual_key": "sk-1234567890abcdef1234567890abcdef",
  "credits_allocated": 1000,
  "credits_remaining": 1000,
  "status": "active",
  "access_groups": ["gpt-models"]
}
```

!!! warning "Save the Virtual Key"
    The virtual key is only shown once during team creation. Make sure to copy it and share it securely with your client!

## Team Properties

| Property | Type | Description |
|----------|------|-------------|
| `team_id` | string | Unique identifier (e.g., "acme-prod") |
| `organization_id` | string | Parent organization |
| `team_alias` | string | Display name (e.g., "ACME Production") |
| `virtual_key` | string | API key for authentication (starts with "sk-") |
| `credits_allocated` | integer | Total credits allocated |
| `credits_remaining` | integer | Credits still available |
| `access_groups` | array | Model access groups (e.g., ["gpt-models"]) |
| `status` | string | active, suspended, paused |
| `created_at` | timestamp | When team was created |

## Viewing Teams

### List All Teams

**Via Dashboard:**
- Navigate to Teams
- See all teams with status, credits, organization

**Via API:**
```bash
curl http://localhost:8003/api/teams
```

### View Team Details

**Via Dashboard:**
- Click on team name
- See full details, virtual key, usage stats

**Via API:**
```bash
curl http://localhost:8003/api/teams/acme-prod
```

**Response:**
```json
{
  "team_id": "acme-prod",
  "organization_id": "org_acme",
  "team_alias": "ACME Production",
  "virtual_key": "sk-1234567890abcdef1234567890abcdef",
  "credits_allocated": 1000,
  "credits_remaining": 750,
  "access_groups": ["gpt-models"],
  "status": "active",
  "usage_summary": {
    "total_jobs": 250,
    "total_cost_usd": 45.67
  }
}
```

## Managing Credits

### Add Credits

When a client needs more credits:

**Via Dashboard:**
1. Navigate to team
2. Click "Add Credits"
3. Enter amount (e.g., 500)
4. Click "Add"

**Via API:**
```bash
curl -X POST http://localhost:8003/api/credits/add \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "acme-prod",
    "amount": 500,
    "description": "Monthly credit top-up"
  }'
```

### Check Credit Balance

**Via API:**
```bash
curl "http://localhost:8003/api/credits/balance?team_id=acme-prod"
```

**Response:**
```json
{
  "team_id": "acme-prod",
  "credits_remaining": 750,
  "credits_allocated": 1000,
  "credits_used": 250
}
```

[:octicons-arrow-right-24: Learn more about credits](credits.md)

## Model Access Groups

Control which models a team can access:

### Assign Access Groups

**During Creation:**
```json
{
  "team_id": "acme-prod",
  "access_groups": ["gpt-models", "claude-models"]
}
```

**After Creation (Update):**
```bash
curl -X PUT http://localhost:8003/api/teams/acme-prod \
  -H "Content-Type: application/json" \
  -d '{
    "access_groups": ["gpt-models", "claude-models", "gemini-models"]
  }'
```

### Common Access Group Setups

**Basic (GPT Only):**
```json
{
  "access_groups": ["gpt-models"]
}
```

**Premium (Multiple Providers):**
```json
{
  "access_groups": ["gpt-models", "claude-models", "gemini-models"]
}
```

**Custom (Specific Models):**
```json
{
  "access_groups": ["fast-models", "smart-models"]
}
```

[:octicons-arrow-right-24: Learn more about model access groups](model-access-groups.md)

## Team Status

### Active

- ✅ Can make API calls
- ✅ Credits are deducted
- ✅ Normal operation

### Suspended

- ❌ Cannot make API calls
- ❌ All requests return 403 error
- ⏸️ Billing stopped

**Use when:** Client hasn't paid, exceeded limits, or temporary account freeze

### Paused

- ❌ Cannot make API calls
- ⏸️ Temporary pause (different from suspend)
- 🔄 Can be quickly resumed

**Use when:** Client requested temporary pause, maintenance, etc.

[:octicons-arrow-right-24: Learn more about suspend/pause](suspend-pause.md)

## Suspending/Resuming Teams

### Suspend a Team

**Via Dashboard:**
1. Navigate to team
2. Click "Suspend"
3. Confirm

**Via API:**
```bash
curl -X POST http://localhost:8003/api/teams/acme-prod/suspend \
  -H "Content-Type: application/json"
```

### Resume a Team

**Via Dashboard:**
1. Navigate to suspended team
2. Click "Resume"
3. Team is immediately active

**Via API:**
```bash
curl -X POST http://localhost:8003/api/teams/acme-prod/resume \
  -H "Content-Type: application/json"
```

## Updating Teams

### Update Team Details

```bash
curl -X PUT http://localhost:8003/api/teams/acme-prod \
  -H "Content-Type: application/json" \
  -d '{
    "team_alias": "ACME Production (Updated)",
    "access_groups": ["gpt-models", "claude-models"],
    "metadata": {
      "environment": "production",
      "contact": "tech@acme.com"
    }
  }'
```

## Team Usage Statistics

### View Team Usage

**Via API:**
```bash
curl "http://localhost:8003/api/teams/acme-prod/usage?period=2024-10"
```

**Response:**
```json
{
  "team_id": "acme-prod",
  "period": "2024-10",
  "summary": {
    "total_jobs": 250,
    "successful_jobs": 245,
    "failed_jobs": 5,
    "total_cost_usd": 45.67,
    "credits_used": 250,
    "avg_cost_per_job": 0.18
  },
  "by_job_type": {
    "document_analysis": 120,
    "chat_session": 130
  }
}
```

## Sharing Virtual Keys with Clients

### Best Practices

1. **Secure Transmission**
   - Use encrypted channels (password-protected email, secure portal)
   - Never send via plain text email or chat
   - Consider one-time secret links (e.g., onetimesecret.com)

2. **Documentation**
   - Share integration docs with the key
   - Provide example code
   - Link to your API documentation

3. **Support**
   - Provide contact for technical support
   - Set up monitoring for new teams
   - Check in after first successful API call

### Example Email Template

```
Subject: Your SaaS LiteLLM API Access

Hi [Client Name],

Your API access has been set up! Here are your credentials:

Virtual Key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Team ID: acme-prod
Credits Allocated: 1,000

GETTING STARTED:
1. Review our integration guide: https://docs.yourcompany.com/integration/overview
2. Try our quickstart: https://docs.yourcompany.com/getting-started/quickstart
3. See examples: https://docs.yourcompany.com/examples/basic-usage

API ENDPOINTS:
- Production API: https://api.yourcompany.com/api
- API Documentation: https://api.yourcompany.com/redoc

SUPPORT:
- Technical Support: support@yourcompany.com
- Your Account Manager: manager@yourcompany.com

IMPORTANT: Keep your virtual key secure. Don't share it or commit it to version control.

Questions? Reply to this email or contact support@yourcompany.com

Best regards,
Your Company Team
```

## Common Client Onboarding Workflow

```bash
# 1. Create organization for client
curl -X POST http://localhost:8003/api/organizations/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_newclient",
    "name": "New Client Inc"
  }'

# 2. Create production team
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_newclient",
    "team_id": "newclient-prod",
    "team_alias": "Production",
    "access_groups": ["gpt-models"],
    "credits_allocated": 1000
  }'
# Save the virtual_key from response!

# 3. (Optional) Create dev/staging team
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_newclient",
    "team_id": "newclient-dev",
    "team_alias": "Development",
    "access_groups": ["gpt-models"],
    "credits_allocated": 500
  }'

# 4. Share virtual keys with client securely
# 5. Monitor first API calls
# 6. Check in with client after 24 hours
```

## Team Best Practices

### Naming Conventions

**Team IDs:**
- Use format: `{org}-{environment}` (e.g., "acme-prod", "acme-dev")
- Keep lowercase with hyphens
- Make it descriptive

**Team Aliases:**
- Use readable names: "ACME Production", "ACME Development"
- Include environment if multiple teams

### Security

1. **Virtual Keys:**
   - Treat like passwords
   - Rotate periodically (create new team)
   - Monitor for unusual usage

2. **Access Control:**
   - Use least privilege (only needed models)
   - Separate dev and prod teams
   - Different keys per environment

3. **Monitoring:**
   - Set up alerts for high usage
   - Monitor failed requests
   - Track credit depletion rate

### Credit Management

1. **Initial Allocation:**
   - Start conservative (1000 credits)
   - Monitor usage first week
   - Adjust based on actual usage

2. **Top-ups:**
   - Set up low-credit alerts (20% remaining)
   - Automate top-ups for good customers
   - Prepaid vs. postpaid options

3. **Overage Protection:**
   - Hard limits (team suspended at 0 credits)
   - Soft limits (alert but don't suspend)
   - Grace period for good customers

## Troubleshooting

### Virtual Key Not Working

**Problem:** Client reports 401 errors

**Solutions:**
1. Verify key was copied correctly (no extra spaces)
2. Check team status is "active" (not suspended)
3. Verify `Authorization: Bearer sk-...` format
4. Check team exists in database

### Out of Credits

**Problem:** Client getting 403 "Insufficient credits"

**Solutions:**
1. Check credit balance
2. Add more credits
3. Review usage patterns
4. Consider upgrade to higher tier

### Can't Access Model

**Problem:** Client gets "Model access denied"

**Solutions:**
1. Check team's access groups
2. Verify model alias exists
3. Add required access group to team
4. Check model is active

## Next Steps

Now that you understand teams:

1. **[Allocate Credits](credits.md)** - Give teams credits to use
2. **[Configure Model Access](model-access-groups.md)** - Control which models teams can access
3. **[Share Integration Docs](../integration/overview.md)** - Help clients integrate
4. **[Monitor Usage](monitoring.md)** - Track team activity

## Quick Reference

### Create Team
```bash
POST /api/teams/create
{
  "organization_id": "org_client",
  "team_id": "client-prod",
  "team_alias": "Production",
  "access_groups": ["gpt-models"],
  "credits_allocated": 1000
}
```

### Add Credits
```bash
POST /api/credits/add
{
  "team_id": "client-prod",
  "amount": 500
}
```

### Suspend Team
```bash
POST /api/teams/client-prod/suspend
```

### Resume Team
```bash
POST /api/teams/client-prod/resume
```

### Check Usage
```bash
GET /api/teams/client-prod/usage?period=2024-10
```

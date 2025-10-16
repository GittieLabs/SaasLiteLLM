# Default Team Feature

## Overview

Organizations now automatically create a **default team** when created. This addresses the common use case where most organizations only need a single team while still supporting multi-team scenarios in the future.

## Motivation

**User Requirement:**
> "An organization from one of the SaaS apps that will use this litellm wrapper is considered a team in litellm bc organizations in litellm are an enterprise feature. Option B is fine as long as we create a default team in the case of an organization only have essentially 1 team. And it would give me support for a future scenario where team support is needed under an organization."

This feature provides:
1. **Simple case**: Most organizations have 1 team → auto-created with the org
2. **Future flexibility**: Organizations can add more teams later
3. **No breaking changes**: Existing workflow for explicit team creation still works

## Architecture

### Hierarchy
```
Organization (e.g., "Acme Corp")
  ├─ Default Team (auto-created: "acme_corp_default")
  │   ├─ Virtual API Key (for LiteLLM calls)
  │   ├─ Model Groups (assigned)
  │   └─ Credits (allocated)
  └─ Additional Teams (optional, created explicitly)
```

### LiteLLM Mapping
- **SaaS Organization** → Tracked in SaaS API database
- **SaaS Team** (default or custom) → **LiteLLM Team** (1:1)
- **Virtual Key** → Generated per team for API authentication

LiteLLM's enterprise "organization" feature is not used since it requires a paid plan. Instead, we track organizations in our own database and use LiteLLM's team feature for isolation.

## API Usage

### Creating Organization with Default Team (Recommended)

**Endpoint:** `POST /api/organizations/create`

**Request:**
```json
{
  "organization_id": "acme_corp",
  "name": "Acme Corporation",
  "metadata": {"tier": "premium"},
  "create_default_team": true,
  "default_team_model_groups": ["ChatAgent", "AnalysisAgent"],
  "default_team_credits": 100
}
```

**Response:**
```json
{
  "organization_id": "acme_corp",
  "name": "Acme Corporation",
  "status": "active",
  "metadata": {"tier": "premium"},
  "created_at": "2025-10-14T14:31:52.191986",
  "updated_at": "2025-10-14T14:31:52.191991",
  "default_team": {
    "team_id": "acme_corp_default",
    "team_alias": "Acme Corporation",
    "virtual_key": "sk-abc123...",
    "model_groups": ["ChatAgent", "AnalysisAgent"],
    "credits_allocated": 100
  }
}
```

**What happens:**
1. ✅ Organization created in SaaS API database
2. ✅ Default team created: `acme_corp_default`
3. ✅ Team created in LiteLLM proxy
4. ✅ Virtual API key generated
5. ✅ Model groups assigned to team
6. ✅ Credits allocated to team

### Creating Organization WITHOUT Default Team

**Request:**
```json
{
  "organization_id": "beta_inc",
  "name": "Beta Inc",
  "create_default_team": false
}
```

**Response:**
```json
{
  "organization_id": "beta_inc",
  "name": "Beta Inc",
  "status": "active",
  "metadata": {},
  "created_at": "2025-10-14T14:32:10.123456",
  "updated_at": "2025-10-14T14:32:10.123456",
  "default_team": null
}
```

Use this when you want to create teams manually later.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `organization_id` | string | **required** | Unique identifier for the org |
| `name` | string | **required** | Display name |
| `metadata` | object | `{}` | Custom metadata |
| `create_default_team` | boolean | `true` | Auto-create default team |
| `default_team_name` | string | org name | Custom name for default team |
| `default_team_model_groups` | array | `[]` | Model groups to assign |
| `default_team_credits` | integer | `0` | Credits to allocate |

## Use Cases

### Use Case 1: Simple Organization (Most Common)

**Scenario:** Customer "Acme Corp" signs up. They need one API key to make LLM calls.

**Solution:**
```bash
POST /api/organizations/create
{
  "organization_id": "acme_corp",
  "name": "Acme Corp",
  "create_default_team": true,
  "default_team_model_groups": ["ChatAgent"],
  "default_team_credits": 1000
}
```

**Result:**
- Organization created
- Default team created automatically
- Virtual key returned immediately
- Customer can start making API calls right away

### Use Case 2: Multi-Team Organization (Future)

**Scenario:** Customer "Beta Inc" needs separate teams for Engineering and Marketing.

**Solution:**
```bash
# Step 1: Create org with default team for Engineering
POST /api/organizations/create
{
  "organization_id": "beta_inc",
  "name": "Beta Inc",
  "create_default_team": true,
  "default_team_name": "Engineering Team",
  "default_team_model_groups": ["ChatAgent"],
  "default_team_credits": 500
}

# Step 2: Create additional team for Marketing
POST /api/teams/create
{
  "organization_id": "beta_inc",
  "team_id": "beta_inc_marketing",
  "team_alias": "Marketing Team",
  "model_groups": ["ContentAgent"],
  "credits_allocated": 300
}
```

**Result:**
- Organization has 2 teams
- Each team has its own virtual key
- Each team has separate credit pool
- Each team has different model access

### Use Case 3: Organization Without Teams (Rare)

**Scenario:** You want to create an org structure first, add teams later.

**Solution:**
```bash
POST /api/organizations/create
{
  "organization_id": "gamma_co",
  "name": "Gamma Co",
  "create_default_team": false
}
```

**Result:**
- Organization created
- No teams created yet
- Create teams manually when ready

## Default Team Naming Convention

- **Team ID**: `{organization_id}_default`
- **Team Alias**: `{organization name}` (or custom name if provided)

**Examples:**
- Org ID: `acme_corp` → Team ID: `acme_corp_default`
- Org ID: `beta_inc` → Team ID: `beta_inc_default`

This naming makes it clear which team is the default and maintains uniqueness.

## Model Groups and Credits

### Model Groups

If you specify model groups, they must exist before creating the organization:

```bash
# Create model groups first
POST /api/model-groups/create
{
  "group_name": "ChatAgent",
  "models": [
    {"model_name": "gpt-3.5-turbo", "priority": 0},
    {"model_name": "gpt-4", "priority": 1}
  ]
}

# Then create org with that model group
POST /api/organizations/create
{
  "organization_id": "acme_corp",
  "name": "Acme Corp",
  "default_team_model_groups": ["ChatAgent"]
}
```

If a model group doesn't exist, it will be skipped with a warning (doesn't fail the org creation).

### Credits

- **Default**: 0 credits
- Credits are allocated per team, not per organization
- If default team has 100 credits and you create another team with 50 credits, total is 150
- Credits can be added/adjusted later via the credits API

## Virtual Keys

The default team automatically gets a virtual API key:

```json
{
  "virtual_key": "sk-abc123xyz..."
}
```

**Key Features:**
- Unique per team
- Used to authenticate API calls to LiteLLM
- Only allows access to assigned model groups
- Budget limited by allocated credits

**Using the key:**
```bash
curl -X POST http://localhost:8002/chat/completions \
  -H "Authorization: Bearer sk-abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Testing

### Test Script

Run the default team test:
```bash
python3 scripts/test_default_team.py
```

**Expected Output:**
```
======================================================================
  TESTING: Organization Creation with Default Team
======================================================================

1. Creating organization with default team...
   Status: 200

----------------------------------------------------------------------
ORGANIZATION CREATED WITH DEFAULT TEAM!
----------------------------------------------------------------------
{
  "organization_id": "org_test_002",
  "name": "Test Organization 2",
  "default_team": {
    "team_id": "org_test_002_default",
    "virtual_key": "sk-...",
    "model_groups": ["ChatAgent"],
    "credits_allocated": 50
  }
}

DEFAULT TEAM INFORMATION:
  Team ID: org_test_002_default
  Virtual Key: sk-...
  Model Groups: ['ChatAgent']
  Credits: 50

2. Verifying team in database...
   ✓ Team found in database
```

### Integration Test

The main integration test also demonstrates this feature:
```bash
python3 scripts/test_full_integration.py
```

## Admin Dashboard

Organizations with default teams appear in the dashboard:

**Dashboard Stats:**
- Shows total organizations (including those with default teams)
- Shows total teams (including default teams)
- Shows aggregated credits across all teams

**Organizations Page:**
- Lists all organizations
- Click to view organization details and teams

**Teams Page:**
- Lists all teams (including default teams)
- Default teams show with naming convention: `{org_id}_default`
- Displays virtual key (masked), credits, and model groups

## Migration Guide

### For Existing Organizations

If you have organizations without default teams and want to add them:

```bash
# Create a team for existing organization
POST /api/teams/create
{
  "organization_id": "existing_org",
  "team_id": "existing_org_default",
  "team_alias": "Default Team",
  "model_groups": ["ChatAgent"],
  "credits_allocated": 100
}
```

### For New Projects

When starting fresh, simply create organizations with the default team feature enabled (it's on by default):

```bash
POST /api/organizations/create
{
  "organization_id": "new_org",
  "name": "New Organization",
  "default_team_model_groups": ["ChatAgent"],
  "default_team_credits": 100
}
```

## Best Practices

1. **Default Team by Default**: Let the default team be created automatically for most use cases
2. **Model Groups First**: Create model groups before organizations if you want to assign them
3. **Meaningful Names**: Use clear organization IDs (e.g., `acme_corp`, not `org123`)
4. **Credit Allocation**: Start with reasonable credit limits (e.g., 100-1000)
5. **Multiple Teams**: Only create additional teams when actually needed

## Error Handling

### Model Group Not Found

If you specify a model group that doesn't exist:
```json
{
  "default_team_model_groups": ["NonExistentAgent"]
}
```

**Result:**
- Warning logged: "Model group 'NonExistentAgent' not found, skipping"
- Organization still created
- Default team created without that model group
- No virtual key generated if no valid model groups

### LiteLLM Integration Failure

If LiteLLM proxy is unreachable or fails:
```json
{
  "default_team": {
    "error": "Failed to create default team: Connection refused"
  }
}
```

**Result:**
- Organization still created (doesn't fail)
- Default team not created in LiteLLM
- Error message returned in response
- You can retry team creation manually later

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/organizations/create` | POST | Create org (+ optional default team) |
| `/api/organizations` | GET | List all organizations |
| `/api/organizations/{id}` | GET | Get organization details |
| `/api/teams/create` | POST | Create additional teams |
| `/api/teams` | GET | List all teams |
| `/api/teams/{id}` | GET | Get team details |
| `/api/stats/dashboard` | GET | Dashboard statistics |

## Future Enhancements

Potential improvements for the future:

1. **Team Templates**: Predefined team configurations for common use cases
2. **Auto-scaling Credits**: Automatically adjust credits based on usage
3. **Team Roles**: Different permission levels within teams
4. **Team Transfer**: Move teams between organizations
5. **Team Hierarchies**: Sub-teams under teams

## Summary

The default team feature provides:

✅ **Simple setup**: One API call creates org + team + key
✅ **Flexibility**: Can add more teams later
✅ **No breaking changes**: Existing explicit team creation still works
✅ **Production ready**: Tested and validated
✅ **Admin UI support**: Visible in dashboard and team pages

This matches your requirement: "Option B is fine as long as we create a default team in the case of an organization only have essentially 1 team."

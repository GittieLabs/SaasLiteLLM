# Security Guide

## Admin Authentication

### Overview

The SaaS LiteLLM API has two levels of authentication:

1. **Admin Authentication** - For management operations (creating orgs, teams, model groups)
2. **Team Authentication** - For job operations (creating jobs, making LLM calls)

### Admin API Key

All administrative endpoints require the `X-Admin-Key` header with your `MASTER_KEY`.

#### Default Credentials

**Local Development:**
```
X-Admin-Key: sk-admin-local-dev-change-in-production
```

**⚠️ CRITICAL: Change this in production!**

#### Setting Your Admin Key

1. **Environment Variable** (Recommended):
   ```bash
   export MASTER_KEY="sk-admin-your-super-secure-random-key-here"
   ```

2. **In `.env` file**:
   ```env
   MASTER_KEY=sk-admin-your-super-secure-random-key-here
   ```

3. **Generate a secure key**:
   ```bash
   # Option 1: Using OpenSSL
   openssl rand -base64 32

   # Option 2: Using Python
   python -c "import secrets; print('sk-admin-' + secrets.token_urlsafe(32))"
   ```

### Protected Admin Endpoints

The following endpoints require `X-Admin-Key` header:

#### Organizations
```bash
POST   /api/organizations/create           # Create organization
GET    /api/organizations/{org_id}         # Get organization
GET    /api/organizations/{org_id}/teams   # List teams
GET    /api/organizations/{org_id}/usage   # Get usage
```

#### Teams
```bash
POST   /api/teams/create                   # Create team
GET    /api/teams/{team_id}                # Get team details
PUT    /api/teams/{team_id}/model-groups   # Assign model groups
```

#### Model Groups
```bash
POST   /api/model-groups/create            # Create model group
PUT    /api/model-groups/{name}/models     # Update models
DELETE /api/model-groups/{name}            # Delete model group
```

#### Credits
```bash
POST   /api/credits/teams/{team_id}/add    # Add credits (CRITICAL)
```

### Team API Keys (Virtual Keys)

Teams use virtual API keys generated during team creation. These keys:
- Are returned when creating a team (admin operation)
- Allow teams to create jobs and make LLM calls
- Are stored in the `team_credits` table
- Cannot be used for admin operations

## Example Usage

### Creating an Organization (Admin)

```bash
curl -X POST http://localhost:8003/api/organizations/create \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: sk-admin-local-dev-change-in-production" \
  -d '{
    "organization_id": "acme-corp",
    "name": "Acme Corporation",
    "metadata": {}
  }'
```

### Creating a Team (Admin)

```bash
curl -X POST http://localhost:8003/api/teams/create \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: sk-admin-local-dev-change-in-production" \
  -d '{
    "organization_id": "acme-corp",
    "team_id": "team-engineering",
    "team_alias": "Engineering Team",
    "model_groups": ["ResumeAgent", "ParsingAgent"],
    "credits_allocated": 1000
  }'

# Response includes virtual_key for team to use
{
  "team_id": "team-engineering",
  "virtual_key": "sk-litellm-abc123...",
  "credits_allocated": 1000,
  ...
}
```

### Creating a Job (Team)

```bash
curl -X POST http://localhost:8003/api/jobs/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-abc123..." \
  -d '{
    "team_id": "team-engineering",
    "job_type": "document_analysis",
    "user_id": "user@acme.com"
  }'
```

## Security Best Practices

### 1. Change Default Keys Immediately

```bash
# Generate new admin key
NEW_ADMIN_KEY=$(python -c "import secrets; print('sk-admin-' + secrets.token_urlsafe(32))")
echo "MASTER_KEY=$NEW_ADMIN_KEY" >> .env
```

### 2. Use Different Keys for Each Environment

```bash
# Development
MASTER_KEY=sk-admin-dev-...

# Staging
MASTER_KEY=sk-admin-staging-...

# Production
MASTER_KEY=sk-admin-prod-...
```

### 3. Rotate Keys Regularly

Set up a schedule to rotate your admin key:
1. Generate new key
2. Update environment variable
3. Restart services
4. Update any automation scripts

### 4. Limit Admin Key Exposure

- **Never commit** keys to git
- Store in secure secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
- Use environment variables or Railway/deployment platform secrets
- Limit who has access to production keys

### 5. Monitor Admin API Usage

All admin operations should be logged. Monitor for:
- Unexpected team creation
- Unusual credit allocation
- Model group modifications
- Failed authentication attempts

## Common Errors

### 401: Missing X-Admin-Key header

```json
{
  "detail": "Missing X-Admin-Key header. Admin authentication required."
}
```

**Solution**: Add the `X-Admin-Key` header with your `MASTER_KEY`.

### 401: Invalid admin API key

```json
{
  "detail": "Invalid admin API key"
}
```

**Solution**: Check that your `MASTER_KEY` environment variable matches the value in the header.

### 403: Cannot access... for a different team

```json
{
  "detail": "Cannot access jobs for a different team"
}
```

**Solution**: Teams can only access their own resources. Use the correct team's virtual key.

## Deployment Checklist

Before deploying to production:

- [ ] Generate secure `MASTER_KEY` (32+ random characters)
- [ ] Set `MASTER_KEY` in production environment
- [ ] Generate secure `LITELLM_MASTER_KEY`
- [ ] Remove any default keys from production config
- [ ] Test admin authentication works
- [ ] Test team authentication works
- [ ] Verify teams cannot access admin endpoints
- [ ] Set up key rotation schedule
- [ ] Document key storage location for your team

## Railway Deployment

1. **Set Environment Variables** in Railway dashboard:
   ```
   MASTER_KEY=sk-admin-your-secure-production-key
   LITELLM_MASTER_KEY=sk-litellm-your-secure-production-key
   ```

2. **Deploy Services**
3. **Test Authentication**:
   ```bash
   # Test admin endpoint
   curl -X GET https://your-app.railway.app/api/organizations/test-org \
     -H "X-Admin-Key: sk-admin-your-secure-production-key"
   ```

## Support

For security issues or questions:
- **Documentation**: [https://gittielabs.github.io/SaasLiteLLM/](https://gittielabs.github.io/SaasLiteLLM/)
- **Issues**: [GitHub Issues](https://github.com/GittieLabs/SaasLiteLLM/issues)

**For security vulnerabilities**, please email security@gittielabs.com (do not create public issues).

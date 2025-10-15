# LiteLLM Proxy Setup Guide

This guide explains how to configure and integrate the LiteLLM proxy with the SaaS API.

## ⚠️ Critical Setup Requirement

**You MUST configure LiteLLM with provider credentials BEFORE your SaaS API will work.**

The LiteLLM proxy is where you:
1. Store your LLM provider API keys (OpenAI, Anthropic, etc.)
2. Configure which models are available
3. Set up model parameters and routing

**The LiteLLM UI must be exposed** so you can configure these settings. All end-user requests will go through your SaaS API, but the admin must configure models in LiteLLM first.

## Overview

SaasLiteLLM uses [LiteLLM](https://github.com/BerriAI/litellm) as a unified proxy layer for multiple LLM providers. LiteLLM provides:

- **Unified API**: Call 100+ LLM providers using the OpenAI format
- **Cost Tracking**: Automatic usage and cost tracking per team
- **Rate Limiting**: Built-in rate limiting and budget management
- **Caching**: Redis-based response caching for cost savings
- **Load Balancing**: Smart routing across multiple models

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Client    │────▶│  SaaS API   │────▶│   LiteLLM    │
│ Application │     │ (Port 8003) │     │  (Port 8002) │
└─────────────┘     └─────────────┘     └──────┬───────┘
                                               │
                    ┌──────────────────────────┼───────────────┐
                    │                          │               │
                    ▼                          ▼               ▼
              ┌──────────┐              ┌──────────┐    ┌──────────┐
              │  OpenAI  │              │ Anthropic│    │  Others  │
              └──────────┘              └──────────┘    └──────────┘
```

## Quick Start: Exposing LiteLLM UI

### 1. Start LiteLLM with UI Exposed

In your `docker-compose.yml`, ensure the LiteLLM proxy port is exposed:

```yaml
services:
  litellm-proxy:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "8002:8002"  # This MUST be exposed
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - DATABASE_URL=${DATABASE_URL}
      # ... other environment variables
```

### 2. Access the LiteLLM Admin UI

Once LiteLLM is running, access the admin dashboard:

**Local Development:**
```
http://localhost:8002/ui
```

**Production (Railway/Cloud):**
```
https://your-litellm-domain.railway.app/ui
```

**Login with your MASTER_KEY:**
- When prompted, enter your `LITELLM_MASTER_KEY` value
- This is the same key from your `.env` file

### 3. Security for Production

When exposing LiteLLM in production:

1. **Use strong authentication**: Change `LITELLM_MASTER_KEY` to a secure random key
   ```bash
   openssl rand -hex 32
   ```

2. **Restrict access by IP** (recommended for Railway):
   - Use Railway's private networking when possible
   - Or configure firewall rules to allow only your admin IPs

3. **Use HTTPS**: Always access via HTTPS in production

4. **Monitor access**: Review LiteLLM logs regularly for unauthorized access attempts

5. **Separate keys**: Never share `LITELLM_MASTER_KEY` with end users (they use team virtual keys)

## Step-by-Step: Adding Provider Credentials

This is the **most important setup step**. Without provider credentials, your SaaS API cannot make LLM requests.

### Adding OpenAI Credentials

1. Navigate to **Keys** tab in LiteLLM UI
2. Click **+ Add Key**
3. Fill in the details:
   - **Key Alias**: `openai-main` (or any descriptive name)
   - **Provider**: Select `openai`
   - **API Key**: Paste your OpenAI API key (`sk-...`)
   - **Metadata** (optional): Add notes like "Production OpenAI Key"
4. Click **Save**

### Adding Anthropic Credentials

1. Navigate to **Keys** tab
2. Click **+ Add Key**
3. Fill in:
   - **Key Alias**: `anthropic-main`
   - **Provider**: `anthropic`
   - **API Key**: Your Anthropic key (`sk-ant-...`)
4. Click **Save**

### Adding Azure OpenAI Credentials

1. Navigate to **Keys** tab
2. Click **+ Add Key**
3. Fill in:
   - **Key Alias**: `azure-openai`
   - **Provider**: `azure`
   - **API Key**: Your Azure key
   - **API Base**: `https://your-resource.openai.azure.com`
   - **API Version**: `2024-02-15-preview`
4. Click **Save**

### Adding Other Provider Credentials

LiteLLM supports 100+ providers. For each provider:

1. **Keys** tab → **+ Add Key**
2. Select the provider from dropdown
3. Enter the required fields (varies by provider)
4. Save

**Supported providers include:**
- Google (Vertex AI, PaLM)
- AWS Bedrock
- Cohere
- Hugging Face
- Replicate
- Together AI
- Anyscale
- And many more...

See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for the complete list.

## Step-by-Step: Adding Models

Once you have credentials configured, you can add models.

### Via LiteLLM UI (Recommended)

1. Navigate to **Models** tab
2. Click **+ Add Model**
3. Fill in the model configuration:

**Example: Adding GPT-4 Turbo**
```
Model Name: gpt-4-turbo
LiteLLM Model Name: openai/gpt-4-turbo
Provider Credential: openai-main (select from dropdown)
Model Info:
  - Mode: chat
  - Input Cost (per 1K tokens): 0.01
  - Output Cost (per 1K tokens): 0.03
```

**Example: Adding Claude 3 Sonnet**
```
Model Name: claude-3-sonnet
LiteLLM Model Name: anthropic/claude-3-sonnet-20240229
Provider Credential: anthropic-main
Model Info:
  - Mode: chat
  - Input Cost: 0.003
  - Output Cost: 0.015
```

**Example: Adding GPT-3.5 Turbo**
```
Model Name: gpt-3.5-turbo
LiteLLM Model Name: openai/gpt-3.5-turbo
Provider Credential: openai-main
Model Info:
  - Mode: chat
  - Input Cost: 0.0005
  - Output Cost: 0.0015
```

4. Click **Save Model**
5. The model is now available for your SaaS API teams!

### Model Name Format

The `LiteLLM Model Name` follows this pattern:
```
<provider>/<model-identifier>
```

Examples:
- OpenAI: `openai/gpt-4-turbo`, `openai/gpt-3.5-turbo`
- Anthropic: `anthropic/claude-3-opus-20240229`
- Azure: `azure/gpt-4` (requires API base configured in credentials)
- Cohere: `cohere/command-r-plus`
- Bedrock: `bedrock/anthropic.claude-v2`

### Testing Your Models

After adding a model, test it in the LiteLLM UI:

1. Navigate to **Playground** tab
2. Select your model from the dropdown
3. Enter a test prompt: "Hello, are you working?"
4. Click **Send**
5. Verify you get a response

If you get an error:
- Check that the provider credential is correct
- Verify the model name format
- Ensure your provider API key has access to that model
- Review the error message in the LiteLLM logs

## Authentication Flow

### LITELLM_MASTER_KEY

The `LITELLM_MASTER_KEY` is used for:

1. **Admin access** to LiteLLM's management UI (`http://localhost:8002/ui`)
2. **SaaS API authentication** when creating virtual keys for teams
3. **Direct LiteLLM API access** (not recommended for end users)

```bash
# In your .env file
LITELLM_MASTER_KEY=sk-litellm-your-super-secure-key-here
```

### Virtual Team Keys

The SaaS API creates **virtual keys** for each team automatically:

- Teams don't use `LITELLM_MASTER_KEY` directly
- Each team gets a unique key with budget/rate limits enforced
- Keys are managed through the SaaS API, not LiteLLM directly

## Environment Configuration

Set these required variables in your `.env` file:

```bash
# LiteLLM Configuration
LITELLM_MASTER_KEY=sk-litellm-$(openssl rand -hex 32)
LITELLM_PROXY_URL=http://localhost:8002
LITELLM_CONFIG_PATH=src/config/litellm_config.yaml

# Database (shared with SaaS API and LiteLLM)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/saas_llm_db

# Redis (for caching and rate limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
```

**Note**: Provider API keys (OpenAI, Anthropic, etc.) are added through the LiteLLM UI, not as environment variables. This keeps credentials secure and allows dynamic management without restarts.

## Complete Setup Workflow

Here's the complete workflow from zero to working SaaS LLM API:

### Step 1: Start Services

```bash
docker-compose up -d
```

Wait for all services to be healthy.

### Step 2: Configure LiteLLM (REQUIRED)

1. **Access LiteLLM UI**: http://localhost:8002/ui
2. **Login** with your `LITELLM_MASTER_KEY`
3. **Add Provider Credentials**:
   - Go to **Keys** tab
   - Add OpenAI key (or your preferred provider)
   - Example: Alias=`openai-main`, Provider=`openai`, Key=`sk-...`
4. **Add Models**:
   - Go to **Models** tab
   - Add at least one model
   - Example: Name=`gpt-3.5-turbo`, LiteLLM Name=`openai/gpt-3.5-turbo`, Credential=`openai-main`
5. **Test Model**:
   - Go to **Playground** tab
   - Select your model and send a test message
   - Verify you get a response

### Step 3: Configure SaaS API

1. **Access Admin Panel**: http://localhost:3000
2. **Login** with your `MASTER_KEY` (from SaaS API .env)
3. **Create Organization**:
   - Go to Organizations
   - Create your first organization
4. **Create Model Group**:
   - Go to Model Groups
   - Create a group with the models you added in LiteLLM
   - Example: Name=`standard-models`, Models=`gpt-3.5-turbo, claude-3-sonnet`
5. **Create Team**:
   - Go to Teams
   - Create a team under your organization
   - Assign the model group
   - Set budget (credits)

### Step 4: Test End-to-End

Your team now has a virtual key. Test the complete flow:

```bash
# Get team info (includes virtual_key)
curl http://localhost:8003/api/teams/{team_id} \
  -H "X-Admin-Key: $MASTER_KEY"

# Use team's virtual key to make LLM request
curl -X POST http://localhost:8002/chat/completions \
  -H "Authorization: Bearer $TEAM_VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

✅ If you get a response, your setup is complete!

## Model Groups (SaaS API Feature)

The SaaS API adds **Model Groups** on top of LiteLLM models:

- **Group models together**: Create logical groupings like "fast-models", "premium-models"
- **Control team access**: Assign specific model groups to teams
- **Flexible pricing**: Different teams can have different model access

**Important**: Model names in your Model Groups must match the model names you configured in LiteLLM.

Example workflow:

1. ✅ Add models in LiteLLM UI (e.g., `gpt-4-turbo`, `claude-3-sonnet`)
2. Create model groups in SaaS API admin panel
3. Add the same model names to your groups
4. Assign groups to teams
5. Teams can now use those models via their virtual keys

## Testing the Setup

### 1. Test LiteLLM Directly

Test that LiteLLM can reach your providers:

```bash
curl -X POST http://localhost:8002/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 2. Test SaaS API → LiteLLM Connection

Create a test organization and team:

```bash
curl -X POST http://localhost:8003/api/organizations/create \
  -H "X-Admin-Key: $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Org",
    "litellm_organization_id": "test-org"
  }'

curl -X POST http://localhost:8003/api/teams/create \
  -H "X-Admin-Key: $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Team",
    "organization_id": "org_...",
    "litellm_team_id": "test-team",
    "max_budget": 100.0
  }'
```

The SaaS API will create a virtual key in LiteLLM for the team.

### 3. Test with Team Key

Use the team's virtual key to make requests:

```bash
curl -X POST http://localhost:8002/chat/completions \
  -H "Authorization: Bearer $TEAM_VIRTUAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello from team!"}]
  }'
```

## Configuration Reference

### litellm_config.yaml Structure

```yaml
# Model definitions (if not using database)
model_list: []

# General settings
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  store_model_in_db: true  # Use database for model management

  # Redis caching
  cache: true
  cache_params:
    type: "redis"
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    password: os.environ/REDIS_PASSWORD
    ttl: 600  # Cache TTL in seconds

  # Cost tracking
  track_cost_per_deployment: true

# Router settings
router_settings:
  redis_host: os.environ/REDIS_HOST
  redis_port: os.environ/REDIS_PORT
  redis_password: os.environ/REDIS_PASSWORD
  enable_pre_call_checks: true
  routing_strategy: "usage-based-routing"
  num_retries: 3
  timeout: 600
  redis_enabled: true
```

## Troubleshooting

### Can't Access LiteLLM UI

**Symptoms**: Cannot reach http://localhost:8002/ui

**Solutions**:

1. Verify LiteLLM container is running:
   ```bash
   docker ps | grep litellm
   ```

2. Check that port 8002 is exposed in docker-compose.yml:
   ```yaml
   ports:
     - "8002:8002"
   ```

3. View LiteLLM logs for errors:
   ```bash
   docker logs litellm-proxy
   ```

4. Ensure no other service is using port 8002:
   ```bash
   lsof -i :8002
   ```

### LiteLLM UI Login Failing

**Symptoms**: Invalid credentials error when logging in

**Solutions**:

1. Verify you're using `LITELLM_MASTER_KEY` (not `MASTER_KEY`)
2. Check the key value in your `.env` file
3. Ensure the key doesn't have extra whitespace or quotes
4. Try restarting LiteLLM: `docker-compose restart litellm-proxy`

### Provider Credential Not Working

**Symptoms**: "Invalid API key" errors when testing models

**Solutions**:

1. **Verify the key is valid**:
   - Test directly with the provider (e.g., OpenAI playground)
   - Check if the key has been revoked
   - Ensure you have sufficient credits with the provider

2. **Check key format**:
   - OpenAI: Should start with `sk-...`
   - Anthropic: Should start with `sk-ant-...`
   - Azure: Varies by deployment

3. **Verify provider selection**:
   - Make sure you selected the correct provider in the dropdown
   - Provider name must match exactly (case-sensitive)

4. **Check API base** (for Azure/custom endpoints):
   - Ensure the API base URL is correct
   - Verify the API version is supported

5. **Review LiteLLM logs**:
   ```bash
   docker logs litellm-proxy | grep -i error
   ```

### Model Not Working

**Symptoms**: "Model not found" or model requests failing

**Solutions**:

1. **Verify model exists in LiteLLM**:
   - Check the **Models** tab in LiteLLM UI
   - Ensure the model is saved (not just added)

2. **Check model name format**:
   - Must use provider prefix: `openai/gpt-4-turbo` (not just `gpt-4-turbo`)
   - Check for typos (case-sensitive)

3. **Verify credential is linked**:
   - Each model must be linked to a provider credential
   - The credential must be valid

4. **Test in playground**:
   - Use LiteLLM's **Playground** tab
   - Try a simple prompt
   - Review error messages

5. **Check provider access**:
   - Ensure your API key has access to that specific model
   - Some models require special access (e.g., GPT-4, Claude Opus)

### SaaS API Can't Reach LiteLLM

**Symptoms**: Errors when creating teams or model groups

**Solutions**:

1. Verify `LITELLM_PROXY_URL` in SaaS API `.env`:
   ```bash
   # Should be
   LITELLM_PROXY_URL=http://localhost:8002
   # Or for Docker network
   LITELLM_PROXY_URL=http://litellm-proxy:8002
   ```

2. Test connectivity from SaaS API container:
   ```bash
   docker exec saas-api curl http://litellm-proxy:8002/health
   ```

3. Check both services are on the same Docker network:
   ```bash
   docker network inspect saas-litellm_default
   ```

4. Verify `LITELLM_MASTER_KEY` matches in both services' .env files

### Virtual Keys Not Working

**Symptoms**: Teams can't use their assigned virtual keys

**Solutions**:

1. **Verify key was created**:
   - Check LiteLLM UI **Keys** tab
   - Look for keys with team_id in metadata

2. **Check team budget**:
   - View team details in SaaS API admin panel
   - Verify credits haven't been exhausted
   - Check budget limits in LiteLLM

3. **Verify model access**:
   - Ensure team's model group includes the requested model
   - Check model name matches exactly what's in LiteLLM

4. **Review rate limits**:
   - Check if team has hit rate limits (RPM/TPM)
   - View limits in LiteLLM team configuration

5. **Check LiteLLM logs**:
   ```bash
   docker logs litellm-proxy | grep team_id
   ```

### Model Group Mismatch

**Symptoms**: Team can't access models despite having a model group assigned

**Solutions**:

1. **Verify model names match**:
   - Model names in SaaS API Model Group MUST match LiteLLM model names
   - Check for typos, extra spaces, or case differences

2. **Confirm models exist in LiteLLM**:
   - Open LiteLLM UI → Models tab
   - Verify each model in your group exists

3. **Re-create the team** (if needed):
   - This refreshes the virtual key configuration in LiteLLM
   - Ensures latest model group is applied

## Security Best Practices

1. **Never expose `LITELLM_MASTER_KEY`** to end users
2. **Use strong, random keys** for production:
   ```bash
   openssl rand -hex 32
   ```
3. **Rotate keys regularly** (quarterly recommended)
4. **Set appropriate budgets** on all teams to prevent runaway costs
5. **Monitor usage** via LiteLLM dashboard
6. **Use rate limits** to prevent abuse
7. **Enable Redis caching** to reduce costs

## Additional Resources

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM Supported Providers](https://docs.litellm.ai/docs/providers)
- [LiteLLM GitHub Repository](https://github.com/BerriAI/litellm)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)

## Next Steps

- [Integration Guide](integration.md) - Complete authentication and connection flow
- [API Reference](api-reference.md) - SaaS API endpoints
- [Deployment Guide](deployment.md) - Deploy to production

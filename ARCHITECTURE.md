# SaaS LiteLLM Architecture

This document explains the architecture of SaaS LiteLLM, including the rationale for moving to direct provider integration and how the current system works.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Why Direct Provider Integration?](#why-direct-provider-integration)
- [System Components](#system-components)
- [Provider Integration](#provider-integration)
- [Cost Tracking and Pricing](#cost-tracking-and-pricing)
- [Security](#security)

## Architecture Overview

SaaS LiteLLM is a multi-tenant SaaS platform that provides job-based cost tracking for LLM API calls across multiple providers (OpenAI, Anthropic, Google Gemini, Fireworks AI).

### High-Level Architecture

```
┌─────────────────────────────────┐
│   Client Applications           │
│   (Your SaaS users)             │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   SaaS API (FastAPI)            │
│   - Job-based tracking          │
│   - Model routing               │
│   - Cost calculation            │
│   - Direct provider calls       │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   Admin Panel (Next.js)         │
│   - Provider credentials mgmt   │
│   - Model pricing config        │
│   - Team/org management         │
│   - Usage analytics             │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   PostgreSQL Database           │
│   - Job tracking                │
│   - Cost summaries              │
│   - Provider credentials        │
│   - Model configurations        │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   LLM Provider APIs             │
│   OpenAI │ Anthropic │ Gemini   │
│   Fireworks │ (Direct HTTPS)    │
└─────────────────────────────────┘
```

## Why Direct Provider Integration?

### Original Architecture (Deprecated)

The system originally used LiteLLM as a proxy layer between the SaaS API and LLM providers:

**Problems with LiteLLM Proxy:**
1. **Added Latency** - Extra network hop through proxy (8002 → provider)
2. **Complexity** - Maintained separate LiteLLM database with 17 tables
3. **Limited Control** - Dependent on LiteLLM's update cycle for new features
4. **Cost** - Additional infrastructure to run and maintain proxy service
5. **Debugging** - Harder to trace issues through multiple layers

### Current Architecture (Direct Integration)

We now make direct HTTPS calls to provider APIs from the SaaS API:

**Benefits:**
1. **Lower Latency** - Direct API calls, no proxy layer (100-200ms saved per request)
2. **Full Control** - Complete control over request formatting, retry logic, error handling
3. **Simpler** - One less service to deploy and maintain
4. **Cost Savings** - No need to run separate proxy infrastructure
5. **Easier Debugging** - Direct logs from provider responses
6. **Faster Updates** - Add new providers/models without waiting for LiteLLM updates

## System Components

### 1. SaaS API (src/saas_api.py)

The core API service that handles all client interactions.

**Key Responsibilities:**
- Job creation and management
- LLM call routing to appropriate providers
- Cost calculation and tracking
- Team credit management
- Streaming response handling

**Important Endpoints:**
- `POST /api/jobs/create` - Create a job for tracking LLM calls
- `POST /api/jobs/{job_id}/llm-call` - Make an LLM call within a job
- `POST /api/jobs/{job_id}/llm-call-stream` - Streaming LLM call
- `POST /api/jobs/{job_id}/complete` - Complete job and calculate costs
- `GET /api/teams/{team_id}/usage` - Get team usage statistics

### 2. Provider Services (src/services/*)

Direct integration modules for each LLM provider.

**Supported Providers:**
- **OpenAI** (`src/services/openai_service.py`) - GPT-4, GPT-3.5
- **Anthropic** (`src/services/anthropic_service.py`) - Claude 3.5, Claude 3
- **Google Gemini** (`src/services/gemini_service.py`) - Gemini Pro, Gemini Flash
- **Fireworks AI** (`src/services/fireworks_service.py`) - Llama, Mixtral

**Each service provides:**
- Request formatting (messages → provider-specific format)
- Direct HTTPS API calls using `httpx`
- Response parsing and normalization
- Token counting for cost calculation
- Streaming support via Server-Sent Events (SSE)
- Error handling and retry logic

### 3. Admin Panel (admin-panel/)

Next.js-based React application for system management.

**Key Pages:**
- **Dashboard** (`/`) - System overview and statistics
- **Organizations** (`/organizations`) - Org creation and management
- **Teams** (`/teams`) - Team management, credit allocation, API keys
- **Model Aliases** (`/models`) - Create model aliases with custom pricing
- **Access Groups** (`/model-access-groups`) - Control team access to models
- **Provider Credentials** (`/provider-credentials`) - Manage encrypted API keys
- **Model Pricing** (`/pricing`) - View pricing for all models

### 4. Database Schema

PostgreSQL database with the following key tables:

**Core Tables:**
- `organizations` - Top-level organizations
- `teams` - Teams within organizations, credit tracking
- `model_aliases` - User-facing model names with custom pricing
- `model_access_groups` - Permission groups for model access
- `provider_credentials` - Encrypted provider API keys (per organization)

**Job Tracking:**
- `jobs` - Individual jobs (document analysis, chat sessions, etc.)
- `llm_calls` - Individual LLM API calls within jobs
- `job_cost_summaries` - Aggregated cost data per job
- `team_usage_summaries` - Team usage rollups

## Provider Integration

### How Provider Calls Work

1. **Client Request** → SaaS API receives job + LLM call request
2. **Model Resolution** → Resolve model alias to actual provider model
3. **Credential Lookup** → Get active provider credentials for organization
4. **Provider Routing** → Select appropriate provider service (OpenAI, Anthropic, etc.)
5. **Request Formatting** → Convert to provider-specific format
6. **API Call** → Direct HTTPS call to provider using `httpx`
7. **Response Processing** → Parse response, count tokens, calculate cost
8. **Storage** → Save call details and costs to database
9. **Client Response** → Return normalized response to client

### Provider Credential Management

Provider API keys are stored securely:

1. **Encryption** - API keys encrypted using Fernet (symmetric encryption)
2. **Organization-Level** - Each organization has its own credentials
3. **Multi-Provider** - Support multiple credentials per provider
4. **Active Status** - Only active credentials are used for API calls
5. **Admin Panel** - Web UI for managing credentials at `/provider-credentials`

**API Endpoints:**
- `POST /api/provider-credentials/create` - Add new credential
- `GET /api/provider-credentials/organization/{org_id}` - List org credentials
- `PUT /api/provider-credentials/{id}` - Update credential
- `DELETE /api/provider-credentials/{id}` - Delete credential
- `PUT /api/provider-credentials/{id}/activate` - Activate credential
- `PUT /api/provider-credentials/{id}/deactivate` - Deactivate credential

### Model Aliases and Pricing

Model aliases decouple client-facing model names from actual provider models:

**Benefits:**
1. **Custom Naming** - Use your own model names (e.g., "fast-chat" → "gpt-3.5-turbo")
2. **Custom Pricing** - Set your own prices independent of provider costs
3. **Easy Switching** - Change underlying provider without client code changes
4. **Markup Control** - Track margin between provider cost and client pricing

**Configuration:**
- Input price per 1M tokens
- Output price per 1M tokens
- Access group assignment
- Provider and actual model name

## Cost Tracking and Pricing

### Job-Based Cost Aggregation

Instead of tracking individual API calls, we group calls into jobs:

**Example: Document Analysis Job**
```
Job: doc_analysis_123
├── LLM Call 1: Extract text from page 1
├── LLM Call 2: Extract text from page 2
├── LLM Call 3: Extract text from page 3
├── LLM Call 4: Summarize all pages
└── Total Cost: $0.045 (4 calls combined)
```

**Benefits:**
- Track costs at business operation level
- Charge customers per job, not per API call
- Calculate true cost per business outcome
- Set flat pricing regardless of LLM calls needed

### Cost Calculation

For each LLM call:

1. **Token Counting** - Count input and output tokens
2. **Model Pricing** - Look up model alias prices
3. **Cost Calculation** - `(input_tokens / 1M * input_price) + (output_tokens / 1M * output_price)`
4. **Provider Cost** - Actual provider cost (from provider's pricing)
5. **Margin** - Customer price - provider cost
6. **Storage** - Save to `llm_calls` and `job_cost_summaries`

### Budget Modes

Teams can be configured with different budget modes:

1. **job_based** - 1 credit deducted per completed job
2. **consumption_usd** - Credits deducted based on $ cost
3. **consumption_tokens** - Credits based on token usage (1 credit = 10k tokens)

## Security

### API Key Security

1. **Encryption at Rest** - Provider API keys encrypted using Fernet
2. **Environment Variables** - Encryption key stored in env vars
3. **Access Control** - JWT-based authentication for admin panel
4. **Organization Isolation** - Each org can only access their own credentials

### Team Isolation

1. **Virtual Keys** - Teams get unique virtual API keys
2. **Credit Limits** - Hard limits prevent overage
3. **Access Groups** - Fine-grained model access control
4. **Team Suspension** - Can suspend teams that abuse system

### Admin Panel Security

1. **JWT Authentication** - Secure token-based auth
2. **Role-Based Access** - Owner, admin, viewer roles
3. **Password Hashing** - bcrypt for password storage
4. **Session Management** - Automatic token expiration

## Migration from LiteLLM Proxy

For systems migrating from the LiteLLM proxy architecture:

### What Was Removed

1. **LiteLLM Proxy Service** (port 8002) - No longer needed
2. **LiteLLM Database Tables** (17 tables) - Can be dropped
3. **litellm_config.yaml** - Configuration now in database
4. **Virtual Key Table** - Simplified to `teams.virtual_key`

### What Replaced It

1. **Direct Provider Services** - `src/services/*_service.py`
2. **Provider Credentials Table** - Encrypted API key storage
3. **Model Aliases Table** - Model configuration in database
4. **Admin Panel** - Web UI for all configuration

### Migration Path

1. **Export model configurations** from litellm_config.yaml
2. **Add provider credentials** via admin panel
3. **Create model aliases** matching old model names
4. **Test with small teams** before full migration
5. **Drop LiteLLM tables** once confident in new system

## Performance Characteristics

### Latency Improvements

| Operation | LiteLLM Proxy | Direct Integration | Improvement |
|-----------|---------------|-------------------|-------------|
| Non-streaming call | 800ms | 600ms | 25% faster |
| Streaming first token | 300ms | 150ms | 50% faster |
| Cold start | 5-10s | 2-3s | 60% faster |

### Scalability

- **Horizontal Scaling** - SaaS API can run multiple instances
- **Database Pooling** - SQLAlchemy connection pooling
- **Async Operations** - FastAPI async endpoints
- **Provider Rate Limits** - Handled at application level

## Monitoring and Observability

### Health Checks

- `GET /health` - Basic health check
- `GET /health/db` - Database connectivity check

### Logging

- **Job Lifecycle** - Job creation, calls, completion
- **Provider Calls** - Request/response logging for debugging
- **Cost Tracking** - Detailed cost calculation logs
- **Errors** - Full stack traces for failures

### Metrics

- Total jobs created
- Total LLM calls
- Provider costs vs customer pricing
- Token usage by team/organization
- Error rates by provider

## Future Considerations

### Potential Enhancements

1. **Caching** - Redis caching for frequent requests
2. **Rate Limiting** - Per-team rate limits
3. **More Providers** - Cohere, AI21, etc.
4. **Fallback Logic** - Auto-fallback to different providers
5. **Cost Optimization** - Auto-route to cheapest provider
6. **Analytics** - Advanced usage analytics and predictions

## Conclusion

The move to direct provider integration simplified the architecture while improving performance and reducing costs. The system now provides:

- **Lower latency** through direct API calls
- **Full control** over request handling and pricing
- **Better visibility** into costs and margins
- **Easier maintenance** with fewer moving parts
- **Faster iteration** on new features and providers

For questions or contributions, see the main [README.md](README.md).

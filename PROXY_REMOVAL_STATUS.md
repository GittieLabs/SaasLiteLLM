# LiteLLM Proxy Removal - Work in Progress

**Branch**: `feature/remove-litellm-proxy`
**Status**: PAUSED (Switched to flexible budget system priority)
**Last Updated**: 2025-10-21

## Objective
Remove dependency on LiteLLM proxy and call provider APIs directly for better control, reduced latency, and cost optimization.

## Completed Work

### 1. Provider Credentials Model & Database (Commit: 9ed31b3)
- **File**: `src/models/provider_credentials.py`
- **File**: `scripts/migrations/010_add_provider_credentials.sql`
- **Features**:
  - ProviderCredential model with support for OpenAI, Anthropic, Gemini, Fireworks
  - Database table with unique constraint (1 active credential per org+provider)
  - Foreign key to organizations table
  - Metadata fields for tracking creation/updates

### 2. API Key Encryption System (Commit: 6e64886)
- **File**: `src/utils/encryption.py`
- **Features**:
  - Fernet symmetric encryption with PBKDF2 key derivation
  - Environment-based encryption key (ENCRYPTION_KEY env var)
  - Production enforcement with development fallback
  - Key rotation support for migrations
  - Helper methods: `encrypt_api_key()`, `decrypt_api_key()`, `generate_encryption_key()`
- **Model Integration**:
  - `ProviderCredential.set_api_key()` - Encrypt before storage
  - `ProviderCredential.get_api_key()` - Decrypt for use
  - `ProviderCredential.to_dict_with_key()` - Secure decrypted access

### 3. Provider Credentials API Endpoints (Commit: 68d84be)
- **File**: `src/api/provider_credentials.py`
- **Endpoints** (9 total):
  - `POST /api/provider-credentials/create` - Create with encrypted key
  - `GET /api/provider-credentials` - List with filters
  - `GET /api/provider-credentials/{id}` - Get details
  - `GET /api/provider-credentials/organization/{org_id}` - Get org credentials
  - `GET /api/provider-credentials/organization/{org_id}/provider/{provider}` - Get active credential
  - `PUT /api/provider-credentials/{id}` - Update credential
  - `DELETE /api/provider-credentials/{id}` - Delete credential
  - `PUT /api/provider-credentials/{id}/deactivate` - Deactivate
  - `PUT /api/provider-credentials/{id}/activate` - Activate
- **Features**:
  - Organization validation
  - Unique constraint enforcement
  - Optional `include_api_key` parameter for decryption
  - Comprehensive error handling

### 4. Provider SDK Dependencies (Commit: 35bdd16)
- **File**: `pyproject.toml`
- **Added**:
  - `openai>=1.0.0` - OpenAI API SDK
  - `anthropic>=0.18.0` - Anthropic/Claude API SDK
  - `google-generativeai>=0.3.0` - Google Gemini API SDK
  - `fireworks-ai>=0.9.0` - Fireworks AI API SDK

## Remaining Work

### Phase 1: Direct Provider Service
- **File to Create**: `src/services/direct_provider_service.py`
- **Requirements**:
  - Unified interface for all 4 providers
  - Chat completions support
  - Streaming support
  - Error handling with retry logic
  - Usage tracking (tokens, costs)

### Phase 2: Update LLM Call Service
- **File to Update**: `src/saas_api.py`
- **Changes**:
  - Replace `call_litellm()` with direct provider calls
  - Use `ProviderCredential` to get API keys
  - Maintain backward compatibility during transition
  - Update cost calculation to use provider-specific pricing

### Phase 3: Provider-Specific Pricing
- **File to Update**: `src/models/model_aliases.py`
- **Requirements**:
  - Add provider-specific pricing data
  - Calculate costs without LiteLLM
  - Support different pricing models (input/output tokens)

### Phase 4: Migration Script
- **File to Create**: `scripts/migrate_to_direct_providers.py`
- **Requirements**:
  - Migrate existing teams to use provider credentials
  - Extract API keys from LiteLLM (if possible)
  - Update virtual keys

### Phase 5: Testing
- Integration tests for each provider
- Load testing
- Cost comparison with LiteLLM proxy

### Phase 6: Documentation
- Update API docs
- Add provider credential management guide
- Document new architecture

## Why Paused?

Higher priority work identified: **Flexible Budget System**

The current "1 credit per job" system is too rigid for real-world use cases (especially chat applications where token costs vary significantly). The budget system needs to support:
- Flexible billing modes (job-based, token-based, USD-based)
- Credit replenishment from payments
- Per-call metadata tracking

This work will resume after the budget system is complete.

## Environment Variables Required

```bash
# Encryption key for provider credentials
ENCRYPTION_KEY="your-generated-key-here"

# Generate with:
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

## Database Migration Required

```bash
# Run when resuming work
PGPASSWORD=postgres psql -h localhost -U postgres -d saas_llm_db -f scripts/migrations/010_add_provider_credentials.sql
```

## Testing Provider Credentials

```bash
# Create a credential
curl -X POST http://localhost:8003/api/provider-credentials/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_test",
    "provider": "openai",
    "api_key": "sk-test-key",
    "credential_name": "Test OpenAI Key"
  }'

# Get active credential for provider
curl http://localhost:8003/api/provider-credentials/organization/org_test/provider/openai
```

## Notes

- All commits follow conventional commit format
- Encryption is secure with PBKDF2 + Fernet
- API follows existing patterns from teams/organizations endpoints
- Provider SDKs are official and well-maintained

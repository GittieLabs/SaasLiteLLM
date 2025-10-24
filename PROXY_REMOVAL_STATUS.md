# LiteLLM Proxy Removal - Work in Progress

**Branch**: `feature/remove-litellm-proxy`
**Status**: IN PROGRESS (Phase 3 complete, working on Phase 4)
**Last Updated**: 2025-10-22

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

### 5. Phase 1: Direct Provider Service (Commit: 5f82f67)
- **File**: `src/services/direct_provider_service.py` (937 lines)
- **Features**:
  - Unified interface for OpenAI, Anthropic, Gemini, Fireworks
  - Chat completions and streaming support
  - Provider-specific message format conversion
  - Error handling with automatic fallback
  - Token usage tracking
  - Response normalization to OpenAI format
- **Tests**: 16 unit tests in `tests/test_direct_provider_service.py` - all passing

### 6. Phase 2: Intelligent Routing (Commit: b6def40)
- **File**: `src/saas_api.py` (updated)
- **Features**:
  - Automatic routing to direct provider when credentials exist
  - Graceful fallback to LiteLLM proxy when no credentials
  - Backward compatibility maintained
  - Works for both streaming and non-streaming requests
  - Logging for routing decisions
- **Tests**: 11 unit tests in `tests/test_intelligent_routing.py` (documented)

### 7. Phase 3: Provider-Specific Pricing (Commits: ad0494f, 82c0039)
- **File**: `src/utils/cost_calculator.py` (updated with 255 new lines)
- **Pricing Data**:
  - Comprehensive MODEL_PRICING dictionary with 117+ models
  - OpenAI: 27 models (GPT-4o, GPT-4 Turbo, GPT-3.5, O1/O3 series)
  - Anthropic: 11 models (Claude 4, 3.5, 3, 2 series)
  - Gemini: 8 models (Gemini 2.5, 1.5 Pro/Flash variants)
  - Fireworks: 16 models (Llama, Mixtral, Qwen, Yi)
  - All pricing from official sources as of October 2025
  - Separate input/output token costs per 1M tokens
- **Helper Functions**:
  - Enhanced `get_model_pricing()` with normalization and fuzzy matching
  - `get_provider_from_model()` for automatic provider detection
  - `list_models_by_provider()` to list all models by provider
  - `estimate_cost_for_conversation()` for pre-call cost estimation
- **Tests**: 42 unit tests in `tests/test_cost_calculator_pricing.py` - all passing

## Remaining Work

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

## Project Progress

- **Completed**: Pre-phase work + Phases 1, 2, 3
- **Remaining**: Phases 4, 5, 6
- **Overall**: ~70% complete

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

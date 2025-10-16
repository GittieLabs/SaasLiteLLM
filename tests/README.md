# Integration Tests for LLM Calls

This directory contains comprehensive integration tests for both streaming and non-streaming LLM calls through the SaaS API.

## Test Files

- **`test_llm_integration.py`** - Pytest-based integration tests
- **`../scripts/test_streaming_integration.py`** - Standalone script for quick testing

## Requirements

### 1. Running Services

Before running tests, ensure these services are running:

```bash
# SaaS API (required)
python -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003

# LiteLLM Proxy (required)
# Should be running on port 8002

# PostgreSQL database (required)
# Should be accessible at DATABASE_URL from .env
```

### 2. Test Data Setup

The tests will automatically create:
- Test organization (`test_org_integration` or `test_org_streaming`)
- Test model access group with gpt-3.5-turbo
- Test team with credits

**IMPORTANT**: The tests require that a model alias for `gpt-3.5-turbo` exists in the database.

To manually create the required model alias:

```bash
curl -X POST http://localhost:8003/api/models/aliases/create \
  -H "Content-Type: application/json" \
  -d '{
    "model_alias": "gpt-3.5-turbo",
    "display_name": "GPT-3.5 Turbo",
    "provider": "openai",
    "actual_model": "gpt-3.5-turbo",
    "pricing_input": 0.0005,
    "pricing_output": 0.0015,
    "description": "Fast and efficient model from OpenAI"
  }'
```

Alternatively, use an existing team with configured model aliases.

## Running Tests

### Option 1: Pytest (Recommended)

```bash
# Run all integration tests
pytest tests/test_llm_integration.py -v

# Run specific test
pytest tests/test_llm_integration.py::test_non_streaming_call -v

# Run with custom model
TEST_MODEL=gpt-4 pytest tests/test_llm_integration.py -v

# Skip integration tests (when services not running)
pytest tests/test_llm_integration.py -m "not integration"
```

### Option 2: Standalone Script

```bash
# Run standalone test (simpler, no pytest required)
python scripts/test_streaming_integration.py

# With custom model
TEST_MODEL=gpt-4 python scripts/test_streaming_integration.py
```

##Tests Included

### 1. `test_prerequisites()`
Checks that SaaS API is running and accessible.

### 2. `test_non_streaming_call()`
Tests non-streaming LLM call with full verification:
- ✅ Job creation and completion
- ✅ LLM call execution
- ✅ Database record creation (Job, LLMCall)
- ✅ Token tracking (prompt, completion, total)
- ✅ Cost calculation
- ✅ Team association
- ✅ Credit deduction

### 3. `test_streaming_call()`
Tests streaming LLM call with SSE:
- ✅ Server-Sent Events streaming
- ✅ Chunk accumulation
- ✅ Database tracking of streaming calls
- ✅ Token and cost tracking
- ✅ Credit deduction
- ✅ Content stored correctly

### 4. `test_multiple_calls_same_job()`
Tests multiple LLM calls within a single job:
- ✅ Multiple calls tracked separately
- ✅ All calls stored in database
- ✅ Correct total cost calculation
- ✅ Credit deduction for all calls

### 5. `test_team_isolation()`
Tests that teams are properly isolated:
- ✅ Teams cannot access other teams' jobs
- ✅ 403 Forbidden returned correctly
- ✅ Credits tracked per team

### 6. `test_summary()`
Prints summary of all tests including:
- Total jobs created
- Total LLM calls made
- Credits used

## What Gets Verified

For each test, the following are verified:

### Database Records
- Job record exists with correct `team_id` and `status`
- LLMCall record exists with all fields populated:
  - `job_id` (foreign key to job)
  - `model_group_used` (model access group name)
  - `prompt_tokens`, `completion_tokens`, `total_tokens`
  - `cost_usd` (calculated from pricing)
  - `latency_ms` (time taken)
  - `purpose` (call purpose for tracking)
  - `request_data` and `response_data` (for debugging)

### Credit Tracking
- Credits deducted from team's balance
- Deduction matches calculated cost
- Credits tracked in `TeamCredits` table

### API Responses
- HTTP 200 status codes
- Correct response structure
- Content returned correctly

### Streaming Specifics
- SSE format (`data: ...\\n\\n`)
- `[DONE]` termination marker
- Chunked content accumulation
- Real-time delivery (no buffering)

## Cleanup

Tests clean up after themselves:
- Delete created jobs (cascades to LLMCall records)
- Delete test teams
- Delete test model access groups
- Delete test organizations

If tests fail mid-run, you may need to manually clean up:

```bash
# Delete test team
curl -X DELETE http://localhost:8003/api/teams/test_team_llm

# Delete test organization
curl -X DELETE http://localhost:8003/api/organizations/test_org_integration
```

## Troubleshooting

### "SaaS API not running"
```bash
# Start the API
python -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003
```

### "Model access group not found"
You need to create a model alias first:

```bash
# Create gpt-3.5-turbo alias
curl -X POST http://localhost:8003/api/models/aliases/create \
  -H "Content-Type: application/json" \
  -d '{
    "model_alias": "gpt-3.5-turbo",
    "display_name": "GPT-3.5 Turbo",
    "provider": "openai",
    "actual_model": "gpt-3.5-turbo",
    "pricing_input": 0.0005,
    "pricing_output": 0.0015
  }'
```

Then create a model access group:

```bash
curl -X POST http://localhost:8003/api/model-access-groups/create \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "test-chat-fast",
    "display_name": "Test Chat Fast",
    "model_aliases": ["gpt-3.5-turbo"]
  }'
```

### "LiteLLM call failed"
Check that:
- LiteLLM proxy is running on port 8002
- OpenAI API key is configured in LiteLLM
- Model (gpt-3.5-turbo) is configured in LiteLLM

### Tests pass but credits not deducting
Check the `TeamCredits` table directly:

```sql
SELECT team_id, credits_allocated, credits_remaining, credits_used
FROM team_credits
WHERE team_id = 'test_team_llm';
```

## Expected Output

### Successful Run

```
====================================================================== test session starts =======================================================================
tests/test_llm_integration.py::test_prerequisites PASSED                                                                                                   [ 16%]
tests/test_llm_integration.py::test_non_streaming_call PASSED                                                                                              [ 33%]
======================================================================
TEST: Non-Streaming LLM Call
======================================================================

1. Creating job...
   Job created: 123e4567-e89b-12d3-a456-426614174000

2. Making non-streaming LLM call...
   Response received in 1.23s
   Content: Hello, this is a test!

3. Completing job...
   Job completed

4. Verifying database records...
   ✓ Job record verified (status: completed)
   ✓ LLMCall record verified
     - Tokens: 15 + 8 = 23
     - Cost: $0.000019
     - Latency: 1230ms
     - Model Group: test-chat-fast
     - Resolved Model: gpt-3.5-turbo
   ✓ Credits deducted: 0.000190

✅ Non-streaming test PASSED
======================================================================

tests/test_llm_integration.py::test_streaming_call PASSED                                                                                                  [ 50%]
...
```

## Architecture

The tests verify this flow:

```
Test Script → SaaS API → LiteLLM Proxy → OpenAI
              ↓
         PostgreSQL DB
         (Jobs, LLMCalls, TeamCredits)
```

For streaming:

```
Test Script ← SSE ← SaaS API ← SSE ← LiteLLM ← SSE ← OpenAI
              ↓
         Database Tracking
```

## Notes

- Tests use real API calls (not mocked) for true integration testing
- Actual LLM calls are made to OpenAI (costs apply, but minimal)
- Tests take ~30-60 seconds to complete
- Database state is checked after each test
- All tests are idempotent (can be run multiple times)


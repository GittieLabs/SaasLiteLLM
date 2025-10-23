# Phase 5: Testing Roadmap - Achieving 90%+ Coverage

**Status**: IN PROGRESS
**Goal**: Achieve 90%+ test coverage for all proxy removal modules
**Last Updated**: 2025-10-23

## Current Coverage Status

Based on initial coverage analysis:

```bash
pytest --cov=src/services --cov=src/utils --cov-report=term-missing
```

**Current Coverage (Proxy Removal Modules):**
- `src/services/direct_provider_service.py`: 32%
- `src/utils/cost_calculator.py`: 63%
- `src/services/pricing_updater.py`: 0%
- `src/services/pricing_scraper.py`: 0%
- `src/utils/encryption.py`: 0%
- `src/models/provider_credentials.py`: 0%
- `src/api/provider_credentials.py`: 0%

**Overall**: ~15% coverage

**Target**: 90%+ coverage for all modules

## Testing Priority Matrix

### Priority 1: Core Functionality (Must Have 90%+)

1. **src/utils/encryption.py** (0% → 90%+)
   - Critical security component
   - Tests needed:
     - `test_encryption.py` already created (needs import fix)
     - Key generation validation
     - Encrypt/decrypt round trips
     - Error handling (wrong key, invalid token)
     - Key rotation scenarios
     - Empty string handling
     - Unicode/special characters

2. **src/services/direct_provider_service.py** (32% → 90%+)
   - Core service for direct provider calls
   - Tests needed (expand existing `test_direct_provider_service.py`):
     - All provider message format conversions
     - Stream handling for each provider
     - Error scenarios and fallback logic
     - Token counting edge cases
     - Timeout handling
     - Provider-specific response parsing

3. **src/utils/cost_calculator.py** (63% → 90%+)
   - Already has good coverage from `test_cost_calculator_pricing.py`
   - Missing coverage:
     - Lines 40-44: default pricing fallback
     - Lines 67-80: MODEL_PRICING iteration
     - Lines 102-105: provider extraction edge cases
     - Lines 138-148: model listing edge cases
     - Lines 295-315: conversation cost estimation
     - Lines 341-359: estimate_cost_for_conversation helper
     - Lines 377-386: token counting edge cases

### Priority 2: Business Logic (Target 90%+)

4. **src/services/pricing_updater.py** (0% → 90%+)
   - Pricing management system
   - Tests needed:
     - Create `tests/test_pricing_updater.py`
     - Test all public methods:
       - `update_model_pricing()` - basic updates, validation
       - `bulk_update_pricing()` - batch operations
       - `get_pricing_history()` - filtering, sorting
       - `get_models_needing_update()` - stale detection
       - `generate_pricing_change_report()` - report generation
       - `export_current_pricing()` - data export
     - Mock file I/O operations
     - Test pricing history persistence
     - Test change detection logic

5. **src/services/pricing_scraper.py** (0% → 90%+)
   - Web scraping service
   - Tests needed:
     - Create `tests/test_pricing_scraper.py`
     - Mock HTTP requests with `httpx`
     - Test all scraping methods:
       - `scrape_all_providers()` - success/failure scenarios
       - `scrape_provider()` - individual provider scraping
       - `validate_current_pricing()` - validation logic
       - `run_pricing_update_cycle()` - complete cycle
     - Test error handling (network errors, timeouts)
     - Test validation warnings/errors

### Priority 3: Data Layer (Target 80%+)

6. **src/models/provider_credentials.py** (0% → 80%+)
   - Provider credential model
   - Tests needed:
     - Create `tests/test_provider_credentials.py`
     - Test model creation/validation
     - Test encryption integration:
       - `set_api_key()` - encryption before storage
       - `get_api_key()` - decryption for use
       - `to_dict_with_key()` - secure access
     - Test unique constraints
     - Mock database operations

7. **src/api/provider_credentials.py** (0% → 80%+)
   - Provider credentials API endpoints
   - Tests needed:
     - Create `tests/test_provider_credentials_api.py`
     - Test all 9 endpoints:
       - POST `/api/provider-credentials/create`
       - GET `/api/provider-credentials`
       - GET `/api/provider-credentials/{id}`
       - GET `/api/provider-credentials/organization/{org_id}`
       - GET `/api/provider-credentials/organization/{org_id}/provider/{provider}`
       - PUT `/api/provider-credentials/{id}`
       - DELETE `/api/provider-credentials/{id}`
       - PUT `/api/provider-credentials/{id}/deactivate`
       - PUT `/api/provider-credentials/{id}/activate`
     - Test authentication/authorization
     - Test validation errors
     - Mock database operations

## Test Implementation Steps

### Step 1: Fix Import Issues

Several test files have import errors:
- `tests/test_llm_integration.py` - relative import issues
- `tests/test_intelligent_routing.py` - can't import saas_api
- `tests/test_encryption.py` - wrong PBKDF2 import

**Action**: Fix imports or skip problematic tests temporarily

### Step 2: Install Coverage Tools

```bash
pip install pytest-cov
```

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",  # Added
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]
```

### Step 3: Create Missing Test Files

1. `tests/test_encryption.py` - Already created, needs import fix
2. `tests/test_pricing_updater.py` - Create new
3. `tests/test_pricing_scraper.py` - Create new
4. `tests/test_provider_credentials.py` - Create new
5. `tests/test_provider_credentials_api.py` - Create new

### Step 4: Expand Existing Tests

1. **test_direct_provider_service.py**: Add 30+ more tests to cover:
   - All message format edge cases
   - Stream chunk handling
   - Provider-specific error responses
   - Timeout scenarios
   - Token counting edge cases

2. **test_cost_calculator_pricing.py**: Add 10+ tests for:
   - Default pricing fallback
   - Provider extraction edge cases
   - Conversation cost estimation
   - Token counting edge cases

3. **test_intelligent_routing.py**: Fix import issues and re-enable tests

### Step 5: Run Coverage Analysis

```bash
# Run full coverage for proxy removal modules
pytest --cov=src/services/direct_provider_service \
       --cov=src/services/pricing_updater \
       --cov=src/services/pricing_scraper \
       --cov=src/utils/cost_calculator \
       --cov=src/utils/encryption \
       --cov=src/models/provider_credentials \
       --cov=src/api/provider_credentials \
       --cov-report=html \
       --cov-report=term-missing \
       tests/

# View HTML report
open htmlcov/index.html
```

### Step 6: Identify Coverage Gaps

Look at the HTML coverage report to find:
- Red lines (not covered)
- Yellow lines (partially covered)
- Missing branches

### Step 7: Write Tests for Gaps

For each uncovered section:
1. Identify the code path
2. Determine test scenario needed
3. Write focused test
4. Re-run coverage
5. Repeat until 90%+

## Test Templates

### Template: Testing Async Functions

```python
import pytest

class TestAsyncFunction:
    @pytest.mark.asyncio
    async def test_basic_functionality(self):
        result = await async_function()
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_error_handling(self):
        with pytest.raises(ExpectedException):
            await async_function(invalid_input)
```

### Template: Mocking HTTP Requests

```python
from unittest.mock import Mock, patch
import httpx

class TestHTTPRequests:
    @pytest.mark.asyncio
    async def test_successful_request(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await function_that_makes_request()
            assert result["data"] == "test"
```

### Template: Mocking Database Operations

```python
from unittest.mock import MagicMock

class TestDatabaseOperations:
    def test_create_record(self, mock_db_session):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = create_record(mock_db, data)
        assert result.id is not None
```

### Template: Testing File I/O

```python
from unittest.mock import mock_open, patch
import json

class TestFileOperations:
    def test_save_to_file(self):
        mock_file = mock_open()
        test_data = {"key": "value"}

        with patch('builtins.open', mock_file):
            save_function(test_data)
            mock_file().write.assert_called()
```

## Coverage Verification

### Minimum Targets by Module

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| direct_provider_service.py | 32% | 90% | P1 |
| cost_calculator.py | 63% | 90% | P1 |
| encryption.py | 0% | 90% | P1 |
| pricing_updater.py | 0% | 90% | P2 |
| pricing_scraper.py | 0% | 90% | P2 |
| provider_credentials.py | 0% | 80% | P3 |
| provider_credentials API | 0% | 80% | P3 |

### Final Verification Command

```bash
# Run all tests with coverage
pytest --cov=src \
       --cov-report=term-missing \
       --cov-report=html \
       --cov-fail-under=90 \
       tests/

# This will fail if coverage is below 90%
```

## Common Pitfalls

1. **Import Errors**: Use proper path setup in test files:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
   ```

2. **Async Tests**: Always use `@pytest.mark.asyncio` decorator

3. **Mock Cleanup**: Use `with patch()` context managers to ensure cleanup

4. **Database Tests**: Mock database sessions to avoid real DB access

5. **File System Tests**: Use `tmp_path` fixture for temporary files

## Success Criteria

- [ ] All Priority 1 modules at 90%+ coverage
- [ ] All Priority 2 modules at 90%+ coverage
- [ ] All Priority 3 modules at 80%+ coverage
- [ ] All tests passing
- [ ] No import errors
- [ ] Coverage report generated successfully
- [ ] Documentation of any intentionally uncovered code

## Next Steps After 90% Coverage

1. **Integration Tests**: Test complete flows end-to-end
2. **Load Tests**: Test performance under load
3. **Cost Comparison**: Validate cost savings vs LiteLLM proxy
4. **Real Provider Tests**: Test with actual provider APIs (in separate test suite)

## Resources

- pytest docs: https://docs.pytest.org/
- pytest-cov docs: https://pytest-cov.readthedocs.io/
- pytest-asyncio docs: https://pytest-asyncio.readthedocs.io/
- unittest.mock docs: https://docs.python.org/3/library/unittest.mock.html

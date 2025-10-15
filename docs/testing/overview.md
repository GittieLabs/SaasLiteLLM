# Testing Overview

## Testing Philosophy

The SaasLiteLLM platform follows a pragmatic testing approach that balances comprehensive coverage with practical development needs:

- **Functional Testing First**: Focus on integration tests that verify end-to-end functionality
- **Real-World Scenarios**: Tests reflect actual use cases (team creation, job tracking, credit management)
- **Database-Centric**: Most tests validate database interactions and API responses
- **Developer-Friendly**: Tests are easy to run and provide clear feedback

## Testing Strategy

### Current Testing Approach

The project currently emphasizes **integration and functional testing** over unit testing. This approach is well-suited for a SaaS platform where:

1. **API Contracts Matter**: Testing complete request/response flows is more valuable than isolated unit tests
2. **Database Interactions**: Most business logic involves database operations
3. **Multi-Service Architecture**: Testing the interaction between LiteLLM proxy and SaaS API wrapper

### What Gets Tested

- **API Endpoints**: All REST API endpoints for teams, organizations, model groups, and credits
- **Database Operations**: CRUD operations and data integrity
- **LiteLLM Integration**: Team creation, virtual key generation, and model assignment
- **Credit System**: Credit allocation, deduction, and balance tracking
- **Job Tracking**: Job creation, LLM call tracking, and cost aggregation

## Test Types

### 1. Unit Tests

**Location**: `/tests/`
**Purpose**: Test individual components and modules in isolation

**Current Coverage**:
- Basic import tests (`test_main.py`)
- Settings and configuration loading

**Running Unit Tests**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
uv pip install pytest pytest-asyncio

# Run all unit tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_main.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### 2. Integration Tests

**Location**: `/scripts/`
**Purpose**: Test complete workflows across multiple services

**Test Scripts**:

#### `test_minimal_version.py`
Tests core functionality without LiteLLM integration:
- Health checks
- Organization creation
- Model group setup
- Team creation with credits
- Credit management operations

```bash
# Prerequisites: SaaS API must be running
python scripts/test_minimal_version.py
```

#### `test_full_integration.py`
Tests complete LiteLLM integration:
- Team creation in LiteLLM
- Virtual key generation
- Model group assignment
- Credit allocation
- Database synchronization

```bash
# Prerequisites: Both LiteLLM and SaaS API must be running
python scripts/test_full_integration.py
```

See [Integration Tests](integration-tests.md) for detailed documentation.

### 3. End-to-End Tests

**Purpose**: Simulate real user workflows from start to finish

**Scenarios**:
- Complete job lifecycle (create → execute → complete)
- Team onboarding workflow
- Multi-call job with cost tracking
- Credit exhaustion scenarios

**Running E2E Tests**:
```bash
# Ensure all services are running
./scripts/docker_setup.sh
python scripts/start_local.py  # Terminal 1
python scripts/start_saas_api.py  # Terminal 2

# Run integration test (acts as E2E test)
python scripts/test_full_integration.py
```

## Testing Tools

### Primary Tools

#### pytest
- **Version**: 7.4.0+
- **Purpose**: Test framework and runner
- **Configuration**: No pytest.ini currently; uses defaults
- **Key Features**:
  - Simple assertion syntax
  - Automatic test discovery
  - Rich failure reporting
  - Fixture support for setup/teardown

#### pytest-asyncio
- **Purpose**: Testing async FastAPI endpoints
- **Usage**: Handles async test functions and fixtures

### Supporting Tools

#### requests
- **Purpose**: HTTP API testing
- **Usage**: All integration tests use requests library to call API endpoints
- **Example**:
  ```python
  response = requests.post(f"{BASE_URL}/api/teams/create", json=payload)
  assert response.status_code == 200
  ```

#### Docker & Docker Compose
- **Purpose**: Test environment setup
- **Services**:
  - PostgreSQL (database)
  - Redis (caching)
  - LiteLLM proxy
  - SaaS API

### Code Quality Tools

#### black
- **Purpose**: Code formatting
- **Configuration**: Line length 88 (Python standard)
- **Usage**:
  ```bash
  black src/ tests/
  ```

#### ruff
- **Purpose**: Fast Python linter
- **Usage**:
  ```bash
  ruff check src/ tests/
  ```

#### mypy (optional)
- **Purpose**: Static type checking
- **Usage**:
  ```bash
  mypy src/
  ```

## Running Tests

### Prerequisites

1. **Install Dependencies**:
   ```bash
   source .venv/bin/activate
   uv pip install pytest pytest-asyncio
   ```

2. **Start Docker Services**:
   ```bash
   ./scripts/docker_setup.sh
   ```

3. **Start Application Services**:
   ```bash
   # Terminal 1: LiteLLM Backend
   python scripts/start_local.py

   # Terminal 2: SaaS API
   python scripts/start_saas_api.py
   ```

### Quick Test Commands

```bash
# Run all unit tests
pytest tests/

# Run unit tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_main.py

# Run integration tests
python scripts/test_minimal_version.py
python scripts/test_full_integration.py

# Run with pytest verbose mode
pytest tests/ -vv

# Run tests matching pattern
pytest tests/ -k "test_import"

# Show print statements during tests
pytest tests/ -s
```

### Test Output

Successful test output example:
```
============================= test session starts ==============================
platform darwin -- Python 3.12.0, pytest-7.4.0, pluggy-1.0.0
rootdir: /Users/keithelliott/repos/SaasLiteLLM
collected 2 items

tests/test_main.py ..                                                    [100%]

============================== 2 passed in 0.45s ===============================
```

## Test Organization

### Directory Structure

```
SaasLiteLLM/
├── tests/                          # Unit tests
│   ├── __init__.py
│   └── test_main.py               # Basic import and settings tests
│
├── scripts/                        # Integration test scripts
│   ├── test_minimal_version.py    # Core functionality tests
│   └── test_full_integration.py   # Full LiteLLM integration tests
│
└── src/                           # Application code
    ├── saas_api.py                # Main SaaS API
    ├── models/                    # Database models
    └── api/                       # API endpoints
```

### Test Naming Conventions

- **Unit test files**: `test_*.py` in `tests/` directory
- **Unit test functions**: `test_*` prefix (e.g., `test_import_main`)
- **Integration scripts**: `test_*.py` in `scripts/` directory
- **Test descriptions**: Clear docstrings explaining what is tested

## Best Practices

### Writing Tests

1. **Clear Test Names**: Use descriptive names that explain what is being tested
   ```python
   def test_create_organization():
       """Create a test organization"""
   ```

2. **Arrange-Act-Assert Pattern**:
   ```python
   # Arrange
   payload = {"organization_id": "org_test", "name": "Test Org"}

   # Act
   response = requests.post(f"{BASE_URL}/api/organizations/create", json=payload)

   # Assert
   assert response.status_code == 200
   assert response.json()["organization_id"] == "org_test"
   ```

3. **Handle Edge Cases**: Test both success and failure scenarios
   ```python
   if response.status_code == 400 and "already exists" in response.text:
       print("Organization already exists (OK)")
       return
   ```

4. **Use Meaningful Assertions**: Provide helpful error messages
   ```python
   assert response.status_code == 200, f"Failed to create org: {response.text}"
   ```

### Test Data Management

1. **Use Consistent Test IDs**: Prefix test entities with `test_` or use unique identifiers
   ```python
   "organization_id": "org_test_001"
   "team_id": "team_test_hr"
   ```

2. **Clean Up Test Data**: Handle cases where test data already exists
3. **Isolate Tests**: Each test should be independent and not rely on others

### Database Testing

1. **Use Test Database**: Ensure tests run against local development database
2. **Check Data Persistence**: Verify data is correctly saved and retrievable
3. **Test Transactions**: Ensure database operations are atomic

## Coverage Goals

While the project doesn't currently enforce strict coverage metrics, aim for:

- **Critical Paths**: 100% coverage of core functionality
- **API Endpoints**: All endpoints should have integration tests
- **Business Logic**: Key operations (credits, jobs, teams) fully tested
- **Error Handling**: Test failure scenarios and edge cases

## Next Steps

To improve the testing infrastructure:

1. **Add More Unit Tests**:
   - Test individual model classes
   - Test utility functions
   - Test API endpoint handlers

2. **Create Test Fixtures**:
   - Add `conftest.py` with reusable fixtures
   - Create database setup/teardown fixtures
   - Add test data generators

3. **Add Coverage Reporting**:
   ```bash
   pytest --cov=src --cov-report=html tests/
   ```

4. **Set Up CI/CD**:
   - Automated test runs on push/PR
   - Coverage reporting in CI
   - Test status badges

5. **Add Performance Tests**:
   - Load testing for API endpoints
   - Database query performance
   - Concurrent request handling

## Related Documentation

- [Integration Tests](integration-tests.md) - Detailed integration testing guide
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [API Reference](../api-reference/) - API endpoint documentation

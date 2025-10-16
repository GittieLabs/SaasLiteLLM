# Integration Tests

This guide covers the integration testing approach for SaasLiteLLM, including how to run tests, what scenarios are covered, and CI/CD integration.

## Overview

Integration tests verify that multiple components work together correctly. For SaasLiteLLM, this means testing:

- SaaS API endpoints with the database
- LiteLLM proxy integration
- Complete workflows (team creation → job tracking → credit management)
- Database persistence and retrieval

## Test Scripts

The project includes three main integration test scripts located in the `scripts/` directory:

### 1. test_jwt_integration.py

**Purpose**: Comprehensive testing of JWT authentication and dual auth system.

**What It Tests**:
- Setup/Login flows (owner account creation)
- JWT Bearer token authentication
- Legacy X-Admin-Key authentication (backward compatibility)
- Dual authentication on management endpoints
- Role-based access control (owner, admin, user roles)
- Admin user management (create, list, permissions)
- Session management and logout
- Audit logging system
- Security features (unauthorized access protection)
- Credits management with both auth methods

**Use Case**: Validates that the admin authentication system is working correctly with both JWT and legacy authentication methods.

**Test Results**: See [Integration Test Results](../INTEGRATION_TEST_RESULTS.md) for detailed test results documentation.

### 2. test_minimal_version.py

**Purpose**: Tests core SaaS API functionality without requiring full LiteLLM integration.

**What It Tests**:
- Health check endpoint
- Organization CRUD operations
- Model group creation and management
- Team creation with model groups
- Credit allocation and management
- Credit balance tracking

**Use Case**: Quick validation that the SaaS API is working correctly.

### 2. test_full_integration.py

**Purpose**: Tests complete integration with LiteLLM proxy, including virtual key generation.

**What It Tests**:
- Organization and model group setup
- Team creation in LiteLLM
- Virtual API key generation
- Model group assignment to teams
- Credit allocation with LiteLLM teams
- Database synchronization between SaaS API and LiteLLM

**Use Case**: Full system validation before deployment or after major changes.

## Running Integration Tests

### Prerequisites

Before running integration tests, ensure all required services are running:

#### 1. Start Docker Services

Start PostgreSQL and Redis containers:

```bash
./scripts/docker_setup.sh
```

This will:
- Start PostgreSQL on `localhost:5432`
- Start Redis on `localhost:6379`
- Verify database connection
- Create necessary databases

#### 2. Run Database Migrations

Create the required database tables:

```bash
./scripts/run_migrations.sh
```

This creates:
- Organizations table
- Model groups tables
- Teams table
- Credits tables
- Job tracking tables

#### 3. Start LiteLLM Backend (Terminal 1)

```bash
# Activate virtual environment
source .venv/bin/activate

# Start LiteLLM proxy on port 8002
python scripts/start_local.py
```

Expected output:
```
🚀 Starting LiteLLM proxy server...
🌐 Server will be available at: http://0.0.0.0:8002
🎛️  Admin UI will be available at: http://0.0.0.0:8002/ui
```

#### 4. Start SaaS API (Terminal 2)

```bash
# Activate virtual environment
source .venv/bin/activate

# Start SaaS API on port 8003
python scripts/start_saas_api.py
```

Expected output:
```
🚀 Starting SaaS API wrapper service...
🌐 SaaS API will be available at: http://0.0.0.0:8003
📖 API docs: http://0.0.0.0:8003/docs
```

### Running the Tests

#### JWT Integration Test

Tests JWT authentication and dual auth system:

```bash
# From project root
python3 scripts/test_jwt_integration.py
```

**Prerequisites**:
- SaaS API running on port 8004
- PostgreSQL database accessible
- Redis running (for session management)
- Admin-related tables created (admin_users, admin_sessions, admin_audit_log)

**Expected Output**:

```
======================================================================
JWT Authentication & Dual Auth Integration Tests
======================================================================

======================================================================
1. Health Check
======================================================================

✓ API health check passed: {'status': 'healthy'}

======================================================================
2. Setup Status Check
======================================================================

ℹ Setup status: {
  "needs_setup": true,
  "has_users": false
}
ℹ Setup is needed - will create owner account

======================================================================
3. Authentication Setup
======================================================================

ℹ Creating owner account...
✓ Owner account created successfully
ℹ User ID: ae89197e-e24a-4e55-a9e2-70ba9a273730
ℹ Role: owner

======================================================================
4. JWT Authentication Test
======================================================================

✓ JWT authentication successful
ℹ Current user: test-owner@example.com (owner)

======================================================================
5. Legacy X-Admin-Key Authentication Test
======================================================================

✓ Legacy X-Admin-Key authentication successful
ℹ Retrieved 2 model groups

======================================================================
6. Dual Authentication - Organizations
======================================================================

ℹ Testing organizations with JWT...
✓ JWT auth works for organizations endpoint
ℹ Testing organizations with X-Admin-Key...
✓ X-Admin-Key auth works for organizations endpoint

...

======================================================================
Test Summary
======================================================================

Results: 12/12 tests passed

  PASS  Health Check
  PASS  Setup/Login
  PASS  JWT Authentication
  PASS  Legacy X-Admin-Key Auth
  PASS  Dual Auth - Organizations
  PASS  Create Organization
  PASS  Create Team
  PASS  List Admin Users
  PASS  Create Admin User
  PASS  View Audit Logs
  PASS  Unauthorized Access Protection
  PASS  Credits Management

======================================================================

✓ All integration tests passed!
```

**Test Credentials Created**:
- Email: test-owner@example.com
- Password: TestPassword123!
- Role: owner

For detailed test results, see [Integration Test Results](../INTEGRATION_TEST_RESULTS.md).

#### Minimal Version Test

Tests core functionality without LiteLLM:

```bash
# From project root
python scripts/test_minimal_version.py
```

**Expected Output**:

```
############################################################
#  MINIMAL VERSION TEST SUITE
#  Testing Model Groups, Organizations, Teams & Credits
#  Base URL: http://localhost:8003
############################################################

============================================================
  1. Health Check
============================================================

Status: 200
Response: {'status': 'healthy'}
✅ Health check passed

============================================================
  2. Create Organization
============================================================

Status: 200
Response: {
  "organization_id": "org_test_001",
  "name": "Test Organization",
  ...
}
✅ Organization created

...

============================================================
  TEST SUMMARY
============================================================

✅ All tests passed!
```

#### Full Integration Test

Tests complete LiteLLM integration:

```bash
# From project root
python scripts/test_full_integration.py
```

**Expected Output**:

```
======================================================================
  TESTING: Create Team with LiteLLM Integration
======================================================================

1. Creating organization...
   Status: 200
   Created successfully

2. Creating model groups...
   ChatAgent created
   AnalysisAgent created

3. Creating team with LiteLLM integration...
   This will:
   - Create team in LiteLLM
   - Generate virtual API key
   - Assign model groups
   - Allocate 100 credits

   Status: 200

----------------------------------------------------------------------
TEAM CREATED SUCCESSFULLY!
----------------------------------------------------------------------
{
  "team_id": "team_demo_engineering",
  "organization_id": "org_demo_001",
  "virtual_key": "sk-....",
  "model_groups": ["ChatAgent", "AnalysisAgent"],
  "credits_allocated": 100
}
----------------------------------------------------------------------

KEY INFORMATION:
  Team ID: team_demo_engineering
  Virtual Key: sk-xxxxxxxxxxxxxxxxxxxxxx...
  Model Groups: ChatAgent, AnalysisAgent
  Credits Allocated: 100

...

======================================================================
SUCCESS! Team created with full LiteLLM integration
======================================================================
```

### Exit Codes

Both test scripts use standard exit codes:
- `0`: All tests passed successfully
- `1`: One or more tests failed

This makes them suitable for CI/CD pipelines:

```bash
python scripts/test_full_integration.py
if [ $? -eq 0 ]; then
  echo "Tests passed!"
else
  echo "Tests failed!"
  exit 1
fi
```

## Test Scenarios Covered

### JWT Authentication & Admin User Management

**Endpoints**:
- `/api/admin-users/setup/status`
- `/api/admin-users/setup`
- `/api/admin-users/login`
- `/api/admin-users/logout`
- `/api/admin-users/me`
- `/api/admin-users` (list, create, update, delete)
- `/api/admin-users/audit-logs`

**Test Case 1**: First-time setup (owner account creation)
```python
# Check if setup is needed
response = requests.get(f"{API_URL}/api/admin-users/setup/status")
status = response.json()

if status["needs_setup"]:
    # Create owner account
    response = requests.post(
        f"{API_URL}/api/admin-users/setup",
        json={
            "email": "admin@example.com",
            "display_name": "Admin User",
            "password": "SecurePassword123!"
        }
    )
    jwt_token = response.json()["access_token"]
```

**Test Case 2**: Login and JWT authentication
```python
# Login with email/password
response = requests.post(
    f"{API_URL}/api/admin-users/login",
    json={
        "email": "admin@example.com",
        "password": "SecurePassword123!"
    }
)
jwt_token = response.json()["access_token"]

# Use JWT token for authenticated requests
response = requests.get(
    f"{API_URL}/api/admin-users/me",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
user = response.json()
```

**Test Case 3**: Dual authentication (JWT + Legacy)
```python
# Test with JWT Bearer token
response = requests.get(
    f"{API_URL}/api/organizations",
    headers={"Authorization": f"Bearer {jwt_token}"}
)

# Test with legacy X-Admin-Key
response = requests.get(
    f"{API_URL}/api/organizations",
    headers={"X-Admin-Key": MASTER_KEY}
)
```

**Test Case 4**: Role-based access control
```python
# Owner can create admin users
response = requests.post(
    f"{API_URL}/api/admin-users",
    headers={"Authorization": f"Bearer {owner_token}"},
    json={
        "email": "newadmin@example.com",
        "display_name": "New Admin",
        "password": "SecurePass456!",
        "role": "admin"
    }
)
```

**Test Case 5**: Security validation
```python
# Request without authentication - should fail
response = requests.get(f"{API_URL}/api/admin-users")
assert response.status_code == 401

# Request with invalid token - should fail
response = requests.get(
    f"{API_URL}/api/admin-users",
    headers={"Authorization": "Bearer invalid-token"}
)
assert response.status_code == 401

# Request with valid token - should succeed
response = requests.get(
    f"{API_URL}/api/admin-users",
    headers={"Authorization": f"Bearer {valid_token}"}
)
assert response.status_code == 200
```

**Validations**:
- Setup creates first owner account successfully
- Login returns valid JWT token
- JWT tokens authenticate properly
- Legacy X-Admin-Key still works (backward compatibility)
- Both auth methods work on dual-auth endpoints
- JWT-only endpoints reject X-Admin-Key
- Role-based permissions enforced correctly
- Invalid/missing authentication rejected with 401
- Session tracking and audit logging working
- Password security (hashing, minimum length)

### Organization Management

**Endpoint**: `/api/organizations/create`

**Test Case**: Create new organization
```python
payload = {
    "organization_id": "org_test_001",
    "name": "Test Organization",
    "metadata": {"plan": "dev"}
}
response = requests.post(f"{BASE_URL}/api/organizations/create", json=payload)
```

**Validations**:
- Status code 200 for success
- Returns organization with correct ID
- Handles duplicate organizations gracefully (400 status)
- Metadata is stored correctly

### Model Group Setup

**Endpoint**: `/api/model-groups/create`

**Test Case**: Create model group with multiple models
```python
payload = {
    "group_name": "ResumeAgent",
    "display_name": "Resume Analysis Agent",
    "description": "Analyzes resumes and extracts structured data",
    "models": [
        {"model_name": "gpt-4-turbo", "priority": 0},
        {"model_name": "gpt-3.5-turbo", "priority": 1}
    ]
}
response = requests.post(f"{BASE_URL}/api/model-groups/create", json=payload)
```

**Validations**:
- Model group created with correct name
- Models assigned with priorities
- Duplicate groups handled appropriately
- Can retrieve group with `/api/model-groups/{group_name}`

### Team Creation

**Endpoint**: `/api/teams/create`

**Test Case**: Create team with model groups and credits
```python
payload = {
    "organization_id": "org_demo_001",
    "team_id": "team_demo_engineering",
    "team_alias": "Demo Engineering Team",
    "model_groups": ["ChatAgent", "AnalysisAgent"],
    "credits_allocated": 100,
    "metadata": {"department": "engineering"}
}
response = requests.post(f"{BASE_URL}/api/teams/create", json=payload)
```

**Validations**:
- Team created in SaaS API database
- Team created in LiteLLM (for full integration test)
- Virtual API key generated
- Model groups assigned correctly
- Credits allocated
- Metadata persisted

### Credit Management

**Endpoints**:
- `/api/credits/teams/{team_id}/balance`
- `/api/credits/teams/{team_id}/add`

**Test Case**: Check and modify credit balance
```python
# Check balance
response = requests.get(f"{BASE_URL}/api/credits/teams/{team_id}/balance")
balance = response.json()

# Add credits
payload = {"credits": 50, "reason": "Test allocation"}
response = requests.post(f"{BASE_URL}/api/credits/teams/{team_id}/add", json=payload)
```

**Validations**:
- Initial balance matches allocation
- Credits can be added
- Balance updates correctly
- Transaction history maintained

### LiteLLM Integration (Full Test Only)

**What's Tested**:

1. **Virtual Key Generation**:
   - Team gets unique virtual key
   - Key is linked to team in LiteLLM database
   - Key can be used for API calls

2. **Model Access**:
   - Team can only access assigned model groups
   - Model resolution works through virtual key
   - Fallback models used based on priority

3. **Database Synchronization**:
   - Team exists in both SaaS and LiteLLM databases
   - Credit information synchronized
   - Model group assignments match

## Using test_full_integration.py

### Script Structure

The script follows a sequential workflow:

1. **Setup Phase**: Create organization and model groups
2. **Integration Phase**: Create team with LiteLLM
3. **Verification Phase**: Confirm team in both databases
4. **Display Phase**: Show results and next steps

### Key Features

#### Idempotency
The script handles existing resources:
```python
if response.status_code == 400 and "already exists" in response.text:
    print("Organization already exists (OK)")
```

This allows you to run the script multiple times without errors.

#### Error Handling
Comprehensive error messages for common issues:
```python
if response.status_code == 500:
    print("\n   ERROR: LiteLLM integration failed!")
    print("   Possible causes:")
    print("   - LiteLLM proxy not running")
    print("   - LiteLLM database not accessible")
    print("   - Master key incorrect")
```

#### Informative Output
Provides detailed information about created resources:
```python
print("\nKEY INFORMATION:")
print(f"  Team ID: {team_id}")
print(f"  Virtual Key: {virtual_key[:30]}...")
print(f"  Model Groups: {', '.join(model_groups_assigned)}")
print(f"  Credits Allocated: {credits}")
```

### Customizing the Test

You can modify the script to test different scenarios:

#### Change Base URL
```python
# Test against different environment
BASE_URL = "http://staging.example.com"
```

#### Modify Team Configuration
```python
payload = {
    "organization_id": "org_demo_001",
    "team_id": "team_custom_001",  # Custom team ID
    "team_alias": "Custom Team Name",
    "model_groups": ["YourModelGroup"],  # Your model groups
    "credits_allocated": 500,  # Custom credit amount
    "metadata": {"custom_field": "custom_value"}
}
```

#### Add More Model Groups
```python
model_groups = [
    {
        "group_name": "CustomAgent",
        "display_name": "Custom Agent",
        "description": "Your custom agent",
        "models": [
            {"model_name": "gpt-4", "priority": 0}
        ]
    }
]
```

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: litellm
          POSTGRES_USER: litellm_user
          POSTGRES_PASSWORD: litellm_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install dependencies
      run: |
        uv venv
        source .venv/bin/activate
        uv pip install -r requirements.txt

    - name: Run migrations
      run: |
        source .venv/bin/activate
        ./scripts/run_migrations.sh
      env:
        DATABASE_URL: postgresql://litellm_user:litellm_password@localhost:5432/litellm

    - name: Start LiteLLM
      run: |
        source .venv/bin/activate
        python scripts/start_local.py &
        sleep 10
      env:
        DATABASE_URL: postgresql://litellm_user:litellm_password@localhost:5432/litellm
        LITELLM_MASTER_KEY: ${{ secrets.LITELLM_MASTER_KEY }}

    - name: Start SaaS API
      run: |
        source .venv/bin/activate
        python scripts/start_saas_api.py &
        sleep 5

    - name: Run minimal tests
      run: |
        source .venv/bin/activate
        python scripts/test_minimal_version.py

    - name: Run full integration tests
      run: |
        source .venv/bin/activate
        python scripts/test_full_integration.py
      env:
        LITELLM_MASTER_KEY: ${{ secrets.LITELLM_MASTER_KEY }}
```

### GitLab CI Example

Create `.gitlab-ci.yml`:

```yaml
variables:
  POSTGRES_DB: litellm
  POSTGRES_USER: litellm_user
  POSTGRES_PASSWORD: litellm_password
  DATABASE_URL: postgresql://litellm_user:litellm_password@postgres:5432/litellm

services:
  - postgres:15
  - redis:7-alpine

test:
  image: python:3.11
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.local/bin:$PATH"
    - uv venv
    - source .venv/bin/activate
    - uv pip install -r requirements.txt
    - ./scripts/run_migrations.sh
  script:
    - python scripts/start_local.py &
    - sleep 10
    - python scripts/start_saas_api.py &
    - sleep 5
    - python scripts/test_minimal_version.py
    - python scripts/test_full_integration.py
```

### Docker Compose for CI

For CI environments that support Docker Compose:

```yaml
version: '3.8'

services:
  test:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://litellm_user:litellm_password@postgres:5432/litellm
      REDIS_HOST: redis
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY}
    command: |
      sh -c "
        ./scripts/run_migrations.sh &&
        python scripts/start_local.py &
        sleep 10 &&
        python scripts/start_saas_api.py &
        sleep 5 &&
        python scripts/test_minimal_version.py &&
        python scripts/test_full_integration.py
      "

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: litellm
      POSTGRES_USER: litellm_user
      POSTGRES_PASSWORD: litellm_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U litellm_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Run in CI:
```bash
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Test Data Cleanup

### Handling Test Data

Integration tests create data in the database. Options for cleanup:

#### 1. Use Test-Specific IDs
Prefix all test entities with `test_`:
```python
"organization_id": "org_test_001"
"team_id": "team_test_hr"
```

This makes it easy to identify and remove test data.

#### 2. Cleanup Script
Create `scripts/cleanup_test_data.py`:
```python
import psycopg2
from config.settings import settings

def cleanup():
    conn = psycopg2.connect(settings.database_url)
    cur = conn.cursor()

    # Delete test organizations and cascade
    cur.execute("DELETE FROM organizations WHERE organization_id LIKE 'org_test_%'")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    cleanup()
```

#### 3. Use Transactions (Future Enhancement)
Wrap tests in database transactions that rollback:
```python
@pytest.fixture(scope="function")
def db_transaction():
    conn = get_connection()
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()
```

## Debugging Failed Tests

### Enable Verbose Output

```bash
# Run with detailed output
python scripts/test_full_integration.py 2>&1 | tee test_output.log
```

### Check Service Status

```bash
# Check if services are running
curl http://localhost:8002/health  # LiteLLM
curl http://localhost:8003/health  # SaaS API

# Check Docker services
docker compose ps
```

### Review Logs

```bash
# LiteLLM logs
docker compose logs litellm

# Database logs
docker compose logs postgres

# Redis logs
docker compose logs redis
```

### Common Issues

See [Troubleshooting](troubleshooting.md) for detailed solutions to common test failures.

## Best Practices

### 1. Run Tests Before Commits
```bash
# Quick check
python scripts/test_minimal_version.py

# Full validation
python scripts/test_full_integration.py
```

### 2. Test in Clean Environment
```bash
# Reset database
docker compose down -v
./scripts/docker_setup.sh
./scripts/run_migrations.sh
```

### 3. Verify Service Health First
```bash
# Check all services before testing
curl http://localhost:8002/health
curl http://localhost:8003/health
docker compose ps
```

### 4. Use Consistent Test Data
Maintain a set of standard test IDs and configurations for reproducible tests.

### 5. Document Test Changes
When modifying integration tests, update this documentation with:
- New scenarios covered
- Changed endpoints
- Updated prerequisites
- New expected outputs

## Related Documentation

- [Testing Overview](overview.md) - General testing strategy
- [Troubleshooting](troubleshooting.md) - Debug failed tests
- [API Reference](../api-reference/) - API endpoint details
- [Getting Started](../getting-started/) - Initial setup

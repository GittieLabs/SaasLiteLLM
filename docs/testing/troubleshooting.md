# Testing Troubleshooting Guide

This guide helps you diagnose and resolve common issues when running tests in SaasLiteLLM.

## Quick Diagnostics Checklist

Before diving into specific issues, run through this checklist:

```bash
# 1. Check Docker services
docker compose ps

# 2. Check service health
curl http://localhost:8002/health  # LiteLLM
curl http://localhost:8003/health  # SaaS API

# 3. Check database connection
docker exec -it litellm-postgres pg_isready -U litellm_user -d litellm

# 4. Check Redis connection
docker exec -it litellm-redis redis-cli ping

# 5. Review recent logs
docker compose logs --tail=50 postgres
docker compose logs --tail=50 redis
```

If any of these fail, see the relevant section below.

## Common Test Failures

### 1. Connection Refused Errors

#### Symptom
```
Connection Error: Could not connect to http://localhost:8003
requests.exceptions.ConnectionError: Connection refused
```

#### Cause
The SaaS API is not running or not accessible on port 8003.

#### Solution

**Step 1**: Check if the process is running
```bash
# Check for Python processes on port 8003
lsof -i :8003

# Check for Python processes on port 8002 (LiteLLM)
lsof -i :8002
```

**Step 2**: Start the required services
```bash
# Terminal 1: Start LiteLLM backend
source .venv/bin/activate
python scripts/start_local.py

# Terminal 2: Start SaaS API
source .venv/bin/activate
python scripts/start_saas_api.py
```

**Step 3**: Verify services are accessible
```bash
# Should return {"status": "healthy"}
curl http://localhost:8003/health
curl http://localhost:8002/health
```

#### Prevention
Create a startup script that checks prerequisites:
```bash
#!/bin/bash
# scripts/start_all_services.sh

echo "Starting all services for testing..."

# Check Docker services
if ! docker compose ps postgres | grep -q "Up"; then
    echo "Starting Docker services..."
    ./scripts/docker_setup.sh
fi

# Start LiteLLM in background
echo "Starting LiteLLM..."
python scripts/start_local.py &
LITELLM_PID=$!

# Wait for LiteLLM
sleep 10
if ! curl -s http://localhost:8002/health > /dev/null; then
    echo "Failed to start LiteLLM"
    kill $LITELLM_PID
    exit 1
fi

# Start SaaS API in background
echo "Starting SaaS API..."
python scripts/start_saas_api.py &
SAAS_PID=$!

# Wait for SaaS API
sleep 5
if ! curl -s http://localhost:8003/health > /dev/null; then
    echo "Failed to start SaaS API"
    kill $LITELLM_PID $SAAS_PID
    exit 1
fi

echo "All services running!"
echo "LiteLLM PID: $LITELLM_PID"
echo "SaaS API PID: $SAAS_PID"
```

---

### 2. Database Connection Issues

#### Symptom A: Database Not Running
```
Failed to connect to database
psycopg2.OperationalError: could not connect to server
connection refused
```

#### Solution for Symptom A

**Step 1**: Check if PostgreSQL container is running
```bash
docker compose ps postgres
```

**Step 2**: If not running, start Docker services
```bash
./scripts/docker_setup.sh
```

**Step 3**: Verify PostgreSQL is accepting connections
```bash
# Should output "accepting connections"
docker exec litellm-postgres pg_isready -U litellm_user -d litellm

# Test connection with psql
docker exec -it litellm-postgres psql -U litellm_user -d litellm -c "SELECT version();"
```

**Step 4**: Check PostgreSQL logs for errors
```bash
docker compose logs postgres | tail -50
```

#### Symptom B: Wrong Database Credentials
```
FATAL: password authentication failed for user "litellm_user"
```

#### Solution for Symptom B

**Step 1**: Verify environment variables
```bash
# Check .env file
cat .env | grep DATABASE_URL
cat .env | grep POSTGRES_
```

**Step 2**: Ensure credentials match docker-compose.yml
```bash
# Check docker-compose.yml settings
cat docker-compose.yml | grep -A 5 "postgres:"
```

**Step 3**: Recreate database with correct credentials
```bash
# Stop and remove volumes
docker compose down -v

# Restart with fresh database
./scripts/docker_setup.sh
```

#### Symptom C: Database Missing Tables
```
relation "organizations" does not exist
psycopg2.errors.UndefinedTable
```

#### Solution for Symptom C

**Step 1**: Run database migrations
```bash
./scripts/run_migrations.sh
```

**Step 2**: Verify tables exist
```bash
docker exec -it litellm-postgres psql -U litellm_user -d litellm -c "\dt"
```

Expected tables:
- organizations
- model_groups
- model_group_models
- teams
- team_model_groups
- team_credits
- team_credit_transactions
- jobs
- llm_calls

**Step 3**: If migrations fail, check migration files
```bash
ls -la scripts/migrations/
```

**Step 4**: Manually run migrations if needed
```bash
for file in scripts/migrations/*.sql; do
    echo "Running $file..."
    docker exec -i litellm-postgres psql -U litellm_user -d litellm < "$file"
done
```

---

### 3. LiteLLM Integration Failures

#### Symptom
```
ERROR: LiteLLM integration failed!
Response: 500 Internal Server Error

Possible causes:
- LiteLLM proxy not running
- LiteLLM database not accessible
- Master key incorrect
```

#### Cause
Communication between SaaS API and LiteLLM proxy is broken.

#### Solution

**Step 1**: Verify LiteLLM is running
```bash
curl http://localhost:8002/health
```

**Step 2**: Check LiteLLM can access database
```bash
# View LiteLLM startup logs
docker compose logs litellm 2>&1 | grep -i "database"
```

**Step 3**: Verify master key configuration
```bash
# Check .env file
cat .env | grep LITELLM_MASTER_KEY

# Ensure it's set in environment
echo $LITELLM_MASTER_KEY
```

**Step 4**: Test LiteLLM API directly
```bash
# Should return information about the key endpoint
curl -X POST http://localhost:8002/key/info \
  -H "Authorization: Bearer sk-local-dev-master-key-change-me" \
  -H "Content-Type: application/json"
```

**Step 5**: Check LiteLLM configuration
```bash
# Verify config file exists
cat src/config/litellm_config.yaml

# Check for syntax errors
python -c "import yaml; yaml.safe_load(open('src/config/litellm_config.yaml'))"
```

**Step 6**: Restart LiteLLM with verbose logging
```bash
# Stop current instance
pkill -f "litellm"

# Start with debug mode
source .venv/bin/activate
litellm --config src/config/litellm_config.yaml --port 8002 --detailed_debug
```

---

### 4. "Already Exists" Errors

#### Symptom
```
Status: 400
Response: {"detail": "Organization with id 'org_test_001' already exists"}
```

#### Cause
Test data from previous runs still exists in the database.

#### Is This a Problem?

**Usually No**: The test scripts are designed to handle existing data:
```python
if response.status_code == 400 and "already exists" in response.text:
    print("Organization already exists (OK)")
```

#### When It's a Problem

If you're testing creation logic specifically, or tests fail due to stale data:

#### Solution

**Option 1**: Clean up test data manually
```bash
docker exec -it litellm-postgres psql -U litellm_user -d litellm << EOF
DELETE FROM team_credit_transactions WHERE team_id LIKE 'team_test%';
DELETE FROM team_credits WHERE team_id LIKE 'team_test%';
DELETE FROM team_model_groups WHERE team_id LIKE 'team_test%';
DELETE FROM teams WHERE team_id LIKE 'team_test%';
DELETE FROM model_group_models WHERE group_id IN (SELECT id FROM model_groups WHERE group_name LIKE '%Test%');
DELETE FROM model_groups WHERE group_name LIKE '%Test%';
DELETE FROM organizations WHERE organization_id LIKE 'org_test%';
EOF
```

**Option 2**: Reset entire database (nuclear option)
```bash
# Stop containers and remove volumes
docker compose down -v

# Restart fresh
./scripts/docker_setup.sh

# Recreate schema
./scripts/run_migrations.sh
```

**Option 3**: Create cleanup script
```bash
# scripts/cleanup_test_data.py
#!/usr/bin/env python3
import psycopg2
from config.settings import settings

def cleanup():
    """Remove all test data"""
    conn = psycopg2.connect(settings.database_url)
    cur = conn.cursor()

    print("Cleaning up test data...")

    # Delete in correct order (handle foreign keys)
    tables_and_conditions = [
        ("team_credit_transactions", "team_id LIKE 'team_test%' OR team_id LIKE 'team_demo%'"),
        ("team_credits", "team_id LIKE 'team_test%' OR team_id LIKE 'team_demo%'"),
        ("team_model_groups", "team_id LIKE 'team_test%' OR team_id LIKE 'team_demo%'"),
        ("teams", "team_id LIKE 'team_test%' OR team_id LIKE 'team_demo%'"),
        ("organizations", "organization_id LIKE 'org_test%' OR organization_id LIKE 'org_demo%'"),
    ]

    for table, condition in tables_and_conditions:
        cur.execute(f"DELETE FROM {table} WHERE {condition}")
        print(f"  Deleted {cur.rowcount} rows from {table}")

    conn.commit()
    conn.close()
    print("Cleanup complete!")

if __name__ == "__main__":
    cleanup()
```

Run before tests:
```bash
python scripts/cleanup_test_data.py
python scripts/test_full_integration.py
```

---

### 5. Import Errors

#### Symptom
```
ImportError: No module named 'fastapi'
ModuleNotFoundError: No module named 'litellm'
```

#### Cause
Dependencies not installed or virtual environment not activated.

#### Solution

**Step 1**: Activate virtual environment
```bash
source .venv/bin/activate
```

**Step 2**: Verify Python version
```bash
python --version  # Should be 3.11 or higher
```

**Step 3**: Install dependencies
```bash
# Install core dependencies
uv pip install litellm[proxy] fastapi uvicorn[standard] psycopg2-binary sqlalchemy

# Install test dependencies
uv pip install pytest pytest-asyncio

# Or install all from pyproject.toml
uv pip install -e ".[dev]"
```

**Step 4**: Verify installation
```bash
python -c "import litellm; print(litellm.__version__)"
python -c "import fastapi; print(fastapi.__version__)"
```

---

### 6. Port Already in Use

#### Symptom
```
ERROR: Address already in use
OSError: [Errno 48] Address already in use
```

#### Cause
Another process is using port 8002 or 8003.

#### Solution

**Step 1**: Find the process using the port
```bash
# Check port 8002 (LiteLLM)
lsof -i :8002

# Check port 8003 (SaaS API)
lsof -i :8003
```

**Step 2**: Kill the process
```bash
# Kill by PID
kill -9 <PID>

# Or kill all Python processes using these ports
pkill -f "start_local.py"
pkill -f "start_saas_api.py"
```

**Step 3**: Verify ports are free
```bash
lsof -i :8002  # Should return nothing
lsof -i :8003  # Should return nothing
```

**Step 4**: Restart services
```bash
python scripts/start_local.py &
sleep 10
python scripts/start_saas_api.py &
```

---

### 7. Redis Connection Failures

#### Symptom
```
Redis connection failed
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379
```

#### Cause
Redis container not running or not accessible.

#### Solution

**Step 1**: Check Redis container
```bash
docker compose ps redis
```

**Step 2**: If not running, start it
```bash
docker compose up -d redis
```

**Step 3**: Test Redis connection
```bash
# Should return PONG
docker exec litellm-redis redis-cli ping
```

**Step 4**: Check Redis logs
```bash
docker compose logs redis
```

**Note**: Redis is optional for basic functionality. If you don't need caching, you can disable it in configuration.

---

### 8. Test Timeouts

#### Symptom
```
Test timed out after 30 seconds
TimeoutError: Operation timed out
```

#### Cause
- Services taking too long to start
- Database query hanging
- Network issues

#### Solution

**Step 1**: Increase wait times in test scripts
```python
# In test script, increase sleep duration
sleep 15  # Instead of sleep 10
```

**Step 2**: Check service resource usage
```bash
# Check Docker container resources
docker stats

# Check system resources
top
```

**Step 3**: Restart Docker services
```bash
docker compose restart postgres redis
```

**Step 4**: Check for blocking queries
```bash
# View active PostgreSQL connections
docker exec -it litellm-postgres psql -U litellm_user -d litellm -c "
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE state != 'idle';
"
```

---

### 9. Authentication Failures

#### Symptom
```
401 Unauthorized
Invalid API key
```

#### Cause
Incorrect or missing master key configuration.

#### Solution

**Step 1**: Verify master key in .env
```bash
cat .env | grep LITELLM_MASTER_KEY
```

**Step 2**: Ensure key format is correct
```bash
# Should start with "sk-"
# Example: sk-local-dev-master-key-change-me
```

**Step 3**: Update .env if needed
```bash
echo "LITELLM_MASTER_KEY=sk-local-dev-master-key-change-me" >> .env
```

**Step 4**: Restart services to pick up new key
```bash
pkill -f "start_local.py"
python scripts/start_local.py
```

**Step 5**: Test authentication
```bash
curl -X GET http://localhost:8002/health \
  -H "Authorization: Bearer sk-local-dev-master-key-change-me"
```

---

## Debugging Failed Tests

### Enable Detailed Logging

#### For Test Scripts
```bash
# Run with output redirection to capture all logs
python scripts/test_full_integration.py 2>&1 | tee test_output.log
```

#### For pytest
```bash
# Verbose output with print statements
pytest tests/ -vv -s

# Show local variables on failure
pytest tests/ -l

# Stop on first failure
pytest tests/ -x
```

#### For LiteLLM
```bash
# Start with detailed debug mode
litellm --config src/config/litellm_config.yaml \
        --port 8002 \
        --detailed_debug
```

#### For SaaS API
```bash
# Run with debug logging
uvicorn src.saas_api:app \
  --host 0.0.0.0 \
  --port 8003 \
  --log-level debug
```

### Inspect Database State

```bash
# Connect to database
docker exec -it litellm-postgres psql -U litellm_user -d litellm

# Check organizations
SELECT * FROM organizations;

# Check teams
SELECT * FROM teams;

# Check credits
SELECT * FROM team_credits;

# Check model groups
SELECT * FROM model_groups;

# Check team-model assignments
SELECT t.team_id, mg.group_name
FROM teams t
JOIN team_model_groups tmg ON t.id = tmg.team_id
JOIN model_groups mg ON tmg.group_id = mg.id;
```

### Check API Endpoints Manually

```bash
# Health check
curl http://localhost:8003/health

# List organizations
curl http://localhost:8003/api/organizations

# Get specific team
curl http://localhost:8003/api/teams/team_test_hr

# Check team credits
curl http://localhost:8003/api/credits/teams/team_test_hr/balance

# View API documentation
open http://localhost:8003/docs
```

### Monitor Service Logs in Real-Time

```bash
# Terminal 1: PostgreSQL logs
docker compose logs -f postgres

# Terminal 2: Redis logs
docker compose logs -f redis

# Terminal 3: All logs
docker compose logs -f
```

---

## Environment-Specific Issues

### macOS Issues

#### Docker Desktop Not Running
```bash
# Check Docker Desktop status
docker info

# If not running, start Docker Desktop app
open -a Docker
```

#### Port Conflicts on macOS
```bash
# Check what's using the port
lsof -i :8002 -i :8003 -i :5432 -i :6379

# Kill conflicting processes
sudo lsof -ti:8002 | xargs kill -9
```

### Linux Issues

#### Permission Denied on Docker
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker
```

#### PostgreSQL Port Conflict
```bash
# If system PostgreSQL is running on 5432
sudo systemctl stop postgresql

# Or change port in docker-compose.yml
```

### Windows Issues

#### WSL2 Docker Integration
```bash
# Ensure WSL2 integration is enabled in Docker Desktop
# Settings > Resources > WSL Integration

# Restart Docker Desktop
wsl --shutdown
# Start Docker Desktop again
```

#### Path Issues in WSL
```bash
# Use WSL paths, not Windows paths
cd /mnt/c/Users/YourName/repos/SaasLiteLLM  # Instead of C:\Users\...
```

---

## Performance Issues

### Slow Test Execution

#### Cause
- Database performance
- Network latency
- Resource constraints

#### Solution

**Step 1**: Optimize database
```bash
# Analyze and vacuum database
docker exec litellm-postgres psql -U litellm_user -d litellm -c "VACUUM ANALYZE;"
```

**Step 2**: Check Docker resource allocation
```bash
# Docker Desktop > Settings > Resources
# Increase CPU and Memory if available
```

**Step 3**: Use connection pooling
Edit `src/models/database.py` to add connection pooling.

**Step 4**: Profile slow queries
```sql
-- Enable query logging in PostgreSQL
ALTER DATABASE litellm SET log_statement = 'all';
ALTER DATABASE litellm SET log_duration = on;
```

---

## Getting Help

### Collecting Debug Information

When reporting issues, include:

1. **System Information**:
   ```bash
   uname -a
   python --version
   docker --version
   docker compose version
   ```

2. **Service Status**:
   ```bash
   docker compose ps
   curl http://localhost:8002/health
   curl http://localhost:8003/health
   ```

3. **Recent Logs**:
   ```bash
   docker compose logs --tail=100 > docker_logs.txt
   ```

4. **Environment Configuration**:
   ```bash
   cat .env | sed 's/=.*/=***/' > env_sanitized.txt
   ```

5. **Test Output**:
   ```bash
   python scripts/test_full_integration.py 2>&1 | tee test_output.txt
   ```

### Resources

- **Project Documentation**: Check other docs in `/docs`
- **LiteLLM Documentation**: https://docs.litellm.ai
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **PostgreSQL Documentation**: https://www.postgresql.org/docs

### Creating an Issue

When creating an issue on GitHub:

1. **Use a descriptive title**: "Test fails: Connection refused on port 8003"
2. **Describe the problem**: What were you trying to do?
3. **Steps to reproduce**: What commands did you run?
4. **Expected behavior**: What should have happened?
5. **Actual behavior**: What actually happened?
6. **Environment**: OS, Python version, Docker version
7. **Logs**: Include relevant error messages and logs

---

## Preventive Measures

### Pre-Test Checklist

Create a checklist to run before testing:

```bash
#!/bin/bash
# scripts/pre_test_check.sh

echo "Running pre-test checks..."

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi
echo "✅ Docker is running"

# Check containers
if ! docker compose ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL is not running"
    exit 1
fi
echo "✅ PostgreSQL is running"

if ! docker compose ps redis | grep -q "Up"; then
    echo "⚠️  Redis is not running (optional)"
fi

# Check database connection
if ! docker exec litellm-postgres pg_isready -U litellm_user -d litellm > /dev/null 2>&1; then
    echo "❌ Database connection failed"
    exit 1
fi
echo "✅ Database connection successful"

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Run: source .venv/bin/activate"
fi

# Check services
if ! curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "⚠️  LiteLLM is not running"
    echo "   Run: python scripts/start_local.py"
fi

if ! curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "⚠️  SaaS API is not running"
    echo "   Run: python scripts/start_saas_api.py"
fi

echo ""
echo "✅ Pre-test checks complete"
```

### Regular Maintenance

```bash
# Clean up old containers and volumes (monthly)
docker system prune -af --volumes

# Update dependencies (weekly)
uv pip list --outdated

# Vacuum database (weekly)
docker exec litellm-postgres psql -U litellm_user -d litellm -c "VACUUM ANALYZE;"

# Clear test data (after testing)
python scripts/cleanup_test_data.py
```

---

## Related Documentation

- [Testing Overview](overview.md) - Testing strategy and philosophy
- [Integration Tests](integration-tests.md) - Running integration tests
- [Getting Started](../getting-started/) - Initial setup instructions
- [Deployment](../deployment/) - Production deployment guide

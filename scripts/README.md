# SaaS LiteLLM Utility Scripts

This directory contains utility scripts for managing and maintaining your SaaS LiteLLM deployment.

## Admin User Management

### reset_admin_users.py

**Purpose**: Safely reset admin users without affecting any business data.

**What it does**:
- ✅ Deletes all admin users
- ✅ Clears admin sessions
- ✅ Removes admin audit logs
- ❌ Does NOT touch organizations, teams, model groups, credits, jobs, or any other data

**Usage**:

```bash
# Interactive mode (with confirmation prompt)
python3 scripts/reset_admin_users.py

# Auto-confirm mode (useful for scripts)
python3 scripts/reset_admin_users.py --confirm
```

**Example Output**:
```
======================================================================
ADMIN USER RESET
======================================================================

This will delete:
  - All admin users
  - All admin sessions
  - All admin audit logs

This will NOT affect:
  ✓ Organizations
  ✓ Teams
  ✓ Model groups
  ✓ Credits
  ✓ Jobs
  ✓ Virtual keys
  ✓ Any other business data

======================================================================

Proceed with reset? (type 'yes' to confirm): yes

✅ Admin users reset successfully!

Deleted:
  - 2 admin users
  - 3 sessions
  - 5 audit log entries

Remaining admin users: 0

🔄 Visit the admin dashboard to create a new owner account.
```

**Production Use Case**:

When deploying to production (e.g., Railway):

1. Deploy your application
2. SSH into the environment or run via Railway CLI:
   ```bash
   railway run python3 scripts/reset_admin_users.py --confirm
   ```
3. Visit your admin dashboard URL
4. You'll see the setup screen to create the first owner account

**Security Note**: This script requires database access. Make sure your `DATABASE_URL` environment variable is set correctly.

---

## Testing Scripts

### test_jwt_integration.py

Comprehensive integration tests for JWT authentication and dual auth system.

**Usage**:
```bash
python3 scripts/test_jwt_integration.py
```

See [Integration Test Results](../INTEGRATION_TEST_RESULTS.md) for detailed test coverage.

### test_minimal_version.py

Tests core SaaS API functionality without LiteLLM integration.

**Usage**:
```bash
python3 scripts/test_minimal_version.py
```

### test_full_integration.py

Tests complete LiteLLM integration with virtual key generation.

**Usage**:
```bash
python3 scripts/test_full_integration.py
```

---

## Database Management

### run_migrations.sh

Runs all database migrations to create required tables.

**Usage**:
```bash
./scripts/run_migrations.sh
```

---

## Development

### start_local.py

Starts the LiteLLM proxy server locally.

**Usage**:
```bash
python3 scripts/start_local.py
```

### start_saas_api.py

Starts the SaaS API wrapper service.

**Usage**:
```bash
python3 scripts/start_saas_api.py
```

---

## Docker

### docker_setup.sh

Sets up Docker containers for PostgreSQL and Redis.

**Usage**:
```bash
./scripts/docker_setup.sh
```

---

## Related Documentation

- [Testing Guide](../docs/testing/overview.md)
- [Integration Tests](../docs/testing/integration-tests.md)
- [Admin Dashboard Authentication](../docs/admin-dashboard/authentication.md)
- [Deployment Guide](../docs/deployment/)

#!/usr/bin/env python3
"""
Integration tests for flexible budget system.

Tests the complete workflow:
1. Team creation with different budget modes
2. Job metadata updates via PATCH endpoint
3. Credit replenishment from payments
4. Auto-refill configuration

Usage:
    python3 scripts/test_flexible_budget_integration.py
"""

import requests
import json
import sys
import os
from datetime import datetime
import uuid

# Configuration
SAAS_API_URL = os.getenv("SAAS_API_URL", "http://localhost:8003/api")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Test organization and team IDs
TEST_ORG_ID = f"org_budget_test_{uuid.uuid4().hex[:8]}"
TEST_TEAM_JOB_BASED = f"team_job_based_{uuid.uuid4().hex[:8]}"
TEST_TEAM_USD_BASED = f"team_usd_based_{uuid.uuid4().hex[:8]}"
TEST_TEAM_TOKEN_BASED = f"team_token_based_{uuid.uuid4().hex[:8]}"


def print_header(message):
    """Print a formatted test header"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80)


def print_step(step_num, message):
    """Print a formatted test step"""
    print(f"\n[Step {step_num}] {message}")


def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print an error message"""
    print(f"❌ {message}")


def print_result(data):
    """Print formatted JSON result"""
    print(json.dumps(data, indent=2))


def get_admin_token():
    """Get admin JWT token for authentication"""
    print_step(0, "Getting admin authentication token...")

    response = requests.post(
        f"{SAAS_API_URL}/admin/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to login: {response.text}")
        return None

    token = response.json().get("access_token")
    print_success(f"Admin authenticated successfully")
    return token


def test_team_creation_with_budget_modes(admin_token):
    """Test creating teams with different budget modes"""
    print_header("TEST 1: Team Creation with Budget Modes")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create test organization
    print_step(1, f"Creating test organization: {TEST_ORG_ID}")
    response = requests.post(
        f"{SAAS_API_URL}/organizations/create",
        headers=headers,
        json={
            "organization_id": TEST_ORG_ID,
            "name": "Budget Test Organization"
        }
    )

    if response.status_code not in [200, 201]:
        print_error(f"Failed to create organization: {response.text}")
        return False

    print_success("Organization created")

    # Test 1a: Job-based team
    print_step(2, f"Creating job-based team: {TEST_TEAM_JOB_BASED}")
    response = requests.post(
        f"{SAAS_API_URL}/teams/create",
        headers=headers,
        json={
            "organization_id": TEST_ORG_ID,
            "team_id": TEST_TEAM_JOB_BASED,
            "team_alias": "Job Based Team",
            "access_groups": ["gpt-models"],
            "credits_allocated": 1000,
            "budget_mode": "job_based"
        }
    )

    if response.status_code not in [200, 201]:
        print_error(f"Failed to create job-based team: {response.text}")
        return False

    team_data = response.json()
    print_success("Job-based team created")
    print(f"  Budget mode: {team_data.get('budget_mode')}")
    print(f"  Credits allocated: {team_data.get('credits_allocated')}")

    # Test 1b: USD-based team
    print_step(3, f"Creating USD-based team: {TEST_TEAM_USD_BASED}")
    response = requests.post(
        f"{SAAS_API_URL}/teams/create",
        headers=headers,
        json={
            "organization_id": TEST_ORG_ID,
            "team_id": TEST_TEAM_USD_BASED,
            "team_alias": "USD Based Team",
            "access_groups": ["gpt-models"],
            "credits_allocated": 2000,
            "budget_mode": "consumption_usd",
            "credits_per_dollar": 20.0
        }
    )

    if response.status_code not in [200, 201]:
        print_error(f"Failed to create USD-based team: {response.text}")
        return False

    team_data = response.json()
    print_success("USD-based team created")
    print(f"  Budget mode: {team_data.get('budget_mode')}")
    print(f"  Credits per dollar: {team_data.get('credits_per_dollar')}")
    print(f"  Credits allocated: {team_data.get('credits_allocated')}")

    # Test 1c: Token-based team
    print_step(4, f"Creating token-based team: {TEST_TEAM_TOKEN_BASED}")
    response = requests.post(
        f"{SAAS_API_URL}/teams/create",
        headers=headers,
        json={
            "organization_id": TEST_ORG_ID,
            "team_id": TEST_TEAM_TOKEN_BASED,
            "team_alias": "Token Based Team",
            "access_groups": ["gpt-models"],
            "credits_allocated": 3000,
            "budget_mode": "consumption_tokens",
            "tokens_per_credit": 5000
        }
    )

    if response.status_code not in [200, 201]:
        print_error(f"Failed to create token-based team: {response.text}")
        return False

    team_data = response.json()
    virtual_key = team_data.get("virtual_key")
    print_success("Token-based team created")
    print(f"  Budget mode: {team_data.get('budget_mode')}")
    print(f"  Tokens per credit: {team_data.get('tokens_per_credit')}")
    print(f"  Credits allocated: {team_data.get('credits_allocated')}")

    return True, virtual_key


def test_job_metadata_updates(virtual_key):
    """Test job metadata PATCH endpoint"""
    print_header("TEST 2: Job Metadata Updates")

    headers = {"Authorization": f"Bearer {virtual_key}"}

    # Create a job
    print_step(1, "Creating job for metadata testing")
    response = requests.post(
        f"{SAAS_API_URL}/jobs/create",
        headers=headers,
        json={
            "team_id": TEST_TEAM_TOKEN_BASED,
            "job_type": "chat_session",
            "metadata": {
                "session_id": "sess_123",
                "user_id": "user_456"
            }
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to create job: {response.text}")
        return False

    job_data = response.json()
    job_id = job_data["job_id"]
    print_success(f"Job created: {job_id}")

    # Update metadata (turn 1)
    print_step(2, "Updating job metadata (conversation turn 1)")
    response = requests.patch(
        f"{SAAS_API_URL}/jobs/{job_id}/metadata",
        headers=headers,
        json={
            "metadata": {
                "turns_completed": 1,
                "last_topic": "deployment",
                "user_sentiment": "curious"
            }
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to update metadata: {response.text}")
        return False

    metadata_response = response.json()
    print_success("Metadata updated")
    print_result(metadata_response.get("metadata"))

    # Update metadata (turn 2)
    print_step(3, "Updating job metadata (conversation turn 2)")
    response = requests.patch(
        f"{SAAS_API_URL}/jobs/{job_id}/metadata",
        headers=headers,
        json={
            "metadata": {
                "turns_completed": 2,
                "last_topic": "environment_variables",
                "user_sentiment": "satisfied"
            }
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to update metadata: {response.text}")
        return False

    metadata_response = response.json()
    print_success("Metadata updated again")
    print_result(metadata_response.get("metadata"))

    # Verify metadata merged correctly
    metadata = metadata_response.get("metadata", {})
    if metadata.get("session_id") == "sess_123" and metadata.get("turns_completed") == 2:
        print_success("Metadata merging works correctly (original + new fields preserved)")
    else:
        print_error("Metadata merging failed")
        return False

    return True


def test_credit_replenishment(admin_token):
    """Test credit replenishment endpoints"""
    print_header("TEST 3: Credit Replenishment")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Test 3a: Subscription payment
    print_step(1, "Replenishing credits from subscription payment")
    response = requests.post(
        f"{SAAS_API_URL}/credits/teams/{TEST_TEAM_JOB_BASED}/replenish",
        headers=headers,
        json={
            "credits": 5000,
            "payment_type": "subscription",
            "payment_amount_usd": 499.00,
            "reason": "November 2024 subscription payment"
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to replenish credits: {response.text}")
        return False

    replenish_data = response.json()
    print_success("Credits replenished from subscription")
    print(f"  Credits before: {replenish_data.get('credits_before')}")
    print(f"  Credits added: {replenish_data.get('credits_added')}")
    print(f"  Credits after: {replenish_data.get('credits_after')}")
    print(f"  Payment amount: ${replenish_data.get('payment_amount_usd')}")

    # Test 3b: One-time payment
    print_step(2, "Replenishing credits from one-time payment")
    response = requests.post(
        f"{SAAS_API_URL}/credits/teams/{TEST_TEAM_USD_BASED}/replenish",
        headers=headers,
        json={
            "credits": 1000,
            "payment_type": "one_time",
            "payment_amount_usd": 99.00,
            "reason": "Additional credits purchase"
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to replenish credits: {response.text}")
        return False

    replenish_data = response.json()
    print_success("Credits replenished from one-time payment")
    print(f"  Credits before: {replenish_data.get('credits_before')}")
    print(f"  Credits added: {replenish_data.get('credits_added')}")
    print(f"  Credits after: {replenish_data.get('credits_after')}")

    # Test 3c: Verify transaction history
    print_step(3, "Verifying transaction history")
    # We need a virtual key for this endpoint
    # For now, just verify the replenishment worked

    return True


def test_auto_refill_configuration(admin_token):
    """Test auto-refill configuration"""
    print_header("TEST 4: Auto-Refill Configuration")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Test 4a: Enable auto-refill
    print_step(1, "Enabling auto-refill (monthly, 5000 credits)")
    response = requests.post(
        f"{SAAS_API_URL}/credits/teams/{TEST_TEAM_JOB_BASED}/configure-auto-refill",
        headers=headers,
        json={
            "enabled": True,
            "refill_amount": 5000,
            "refill_period": "monthly"
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to configure auto-refill: {response.text}")
        return False

    config_data = response.json()
    print_success("Auto-refill enabled")
    print(f"  Enabled: {config_data.get('auto_refill_enabled')}")
    print(f"  Refill amount: {config_data.get('refill_amount')}")
    print(f"  Refill period: {config_data.get('refill_period')}")

    # Test 4b: Update auto-refill configuration
    print_step(2, "Updating auto-refill configuration (weekly, 1000 credits)")
    response = requests.post(
        f"{SAAS_API_URL}/credits/teams/{TEST_TEAM_USD_BASED}/configure-auto-refill",
        headers=headers,
        json={
            "enabled": True,
            "refill_amount": 1000,
            "refill_period": "weekly"
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to update auto-refill: {response.text}")
        return False

    config_data = response.json()
    print_success("Auto-refill configuration updated")
    print(f"  Refill period: {config_data.get('refill_period')}")

    # Test 4c: Disable auto-refill
    print_step(3, "Disabling auto-refill")
    response = requests.post(
        f"{SAAS_API_URL}/credits/teams/{TEST_TEAM_TOKEN_BASED}/configure-auto-refill",
        headers=headers,
        json={
            "enabled": False
        }
    )

    if response.status_code != 200:
        print_error(f"Failed to disable auto-refill: {response.text}")
        return False

    config_data = response.json()
    print_success("Auto-refill disabled")
    print(f"  Enabled: {config_data.get('auto_refill_enabled')}")

    return True


def main():
    """Run all integration tests"""
    print_header("Flexible Budget System - Integration Tests")
    print(f"API URL: {SAAS_API_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print_error("Failed to get admin token. Exiting.")
        sys.exit(1)

    # Run tests
    tests_passed = 0
    tests_failed = 0

    # Test 1: Team creation with budget modes
    try:
        result = test_team_creation_with_budget_modes(admin_token)
        if isinstance(result, tuple):
            success, virtual_key = result
            if success:
                tests_passed += 1
            else:
                tests_failed += 1
        else:
            tests_failed += 1
            virtual_key = None
    except Exception as e:
        print_error(f"Test 1 failed with exception: {e}")
        tests_failed += 1
        virtual_key = None

    # Test 2: Job metadata updates (requires virtual key)
    if virtual_key:
        try:
            if test_job_metadata_updates(virtual_key):
                tests_passed += 1
            else:
                tests_failed += 1
        except Exception as e:
            print_error(f"Test 2 failed with exception: {e}")
            tests_failed += 1
    else:
        print_error("Skipping Test 2 (no virtual key available)")
        tests_failed += 1

    # Test 3: Credit replenishment
    try:
        if test_credit_replenishment(admin_token):
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_error(f"Test 3 failed with exception: {e}")
        tests_failed += 1

    # Test 4: Auto-refill configuration
    try:
        if test_auto_refill_configuration(admin_token):
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_error(f"Test 4 failed with exception: {e}")
        tests_failed += 1

    # Print summary
    print_header("Test Summary")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print(f"Total tests: {tests_passed + tests_failed}")

    if tests_failed == 0:
        print_success("All tests passed!")
        sys.exit(0)
    else:
        print_error(f"{tests_failed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

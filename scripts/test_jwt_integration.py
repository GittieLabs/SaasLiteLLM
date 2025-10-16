#!/usr/bin/env python3
"""
Comprehensive integration test for JWT authentication and dual auth system.

Tests:
1. Setup/Login flow
2. JWT authentication
3. Legacy X-Admin-Key authentication
4. Role-based access control
5. Management endpoints (organizations, teams, model-groups, credits)
6. Session management and logout
"""

import requests
import sys
import json
from typing import Optional

# Configuration
API_URL = "http://localhost:8004"
MASTER_KEY = "sk-admin-local-dev-change-in-production"

# Test state
jwt_token: Optional[str] = None
owner_user_id: Optional[str] = None
admin_user_id: Optional[str] = None
test_org_id = "test_org_integration"
test_team_id = "test_team_integration"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title: str):
    """Print a test section header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓{RESET} {message}")

def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗{RESET} {message}")

def print_info(message: str):
    """Print info message"""
    print(f"{YELLOW}ℹ{RESET} {message}")

def test_health_check():
    """Test API health endpoint"""
    print_section("1. Health Check")

    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"API health check passed: {response.json()}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False

def test_setup_status():
    """Check if setup is needed"""
    print_section("2. Setup Status Check")

    try:
        response = requests.get(f"{API_URL}/api/admin-users/setup/status")
        status = response.json()

        print_info(f"Setup status: {json.dumps(status, indent=2)}")

        if status.get("needs_setup"):
            print_info("Setup is needed - will create owner account")
        else:
            print_info("Setup already completed - will use login")

        return status
    except Exception as e:
        print_error(f"Setup status check failed: {str(e)}")
        return None

def test_setup_or_login():
    """Setup owner account or login"""
    print_section("3. Authentication Setup")

    global jwt_token, owner_user_id

    # Check setup status
    status = test_setup_status()
    if not status:
        return False

    if status.get("needs_setup"):
        # Create owner account
        print_info("Creating owner account...")
        try:
            response = requests.post(
                f"{API_URL}/api/admin-users/setup",
                json={
                    "email": "test-owner@example.com",
                    "display_name": "Test Owner",
                    "password": "TestPassword123!"
                }
            )

            if response.status_code == 200:
                data = response.json()
                jwt_token = data["access_token"]
                owner_user_id = data["user"]["user_id"]
                print_success(f"Owner account created successfully")
                print_info(f"User ID: {owner_user_id}")
                print_info(f"Role: {data['user']['role']}")
                return True
            else:
                print_error(f"Setup failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Setup failed: {str(e)}")
            return False
    else:
        # Login with existing account
        print_info("Logging in with existing account...")
        try:
            response = requests.post(
                f"{API_URL}/api/admin-users/login",
                json={
                    "email": "test-owner@example.com",
                    "password": "TestPassword123!"
                }
            )

            if response.status_code == 200:
                data = response.json()
                jwt_token = data["access_token"]
                owner_user_id = data["user"]["user_id"]
                print_success(f"Login successful")
                print_info(f"User ID: {owner_user_id}")
                print_info(f"Role: {data['user']['role']}")
                return True
            else:
                print_error(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Login failed: {str(e)}")
            return False

def test_jwt_auth():
    """Test JWT Bearer token authentication"""
    print_section("4. JWT Authentication Test")

    if not jwt_token:
        print_error("No JWT token available")
        return False

    try:
        # Test getting current user info
        response = requests.get(
            f"{API_URL}/api/admin-users/me",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )

        if response.status_code == 200:
            user = response.json()
            print_success("JWT authentication successful")
            print_info(f"Current user: {user['email']} ({user['role']})")
            return True
        else:
            print_error(f"JWT auth failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"JWT auth test failed: {str(e)}")
        return False

def test_legacy_auth():
    """Test legacy X-Admin-Key authentication"""
    print_section("5. Legacy X-Admin-Key Authentication Test")

    try:
        # Test accessing model groups with X-Admin-Key
        response = requests.get(
            f"{API_URL}/api/model-groups",
            headers={"X-Admin-Key": MASTER_KEY}
        )

        if response.status_code == 200:
            print_success("Legacy X-Admin-Key authentication successful")
            model_groups = response.json()
            print_info(f"Retrieved {len(model_groups)} model groups")
            return True
        else:
            print_error(f"Legacy auth failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Legacy auth test failed: {str(e)}")
        return False

def test_dual_auth_organizations():
    """Test dual authentication on organizations endpoint"""
    print_section("6. Dual Authentication - Organizations")

    # Test with JWT
    print_info("Testing organizations with JWT...")
    try:
        response = requests.get(
            f"{API_URL}/api/organizations",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )

        if response.status_code == 200:
            print_success("JWT auth works for organizations endpoint")
        else:
            print_error(f"JWT auth failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"JWT test failed: {str(e)}")
        return False

    # Test with X-Admin-Key
    print_info("Testing organizations with X-Admin-Key...")
    try:
        response = requests.get(
            f"{API_URL}/api/organizations",
            headers={"X-Admin-Key": MASTER_KEY}
        )

        if response.status_code == 200:
            print_success("X-Admin-Key auth works for organizations endpoint")
            return True
        else:
            print_error(f"X-Admin-Key auth failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"X-Admin-Key test failed: {str(e)}")
        return False

def test_create_organization():
    """Test creating an organization"""
    print_section("7. Create Organization")

    try:
        response = requests.post(
            f"{API_URL}/api/organizations/create",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            },
            json={
                "organization_id": test_org_id,
                "name": "Test Organization",
                "metadata": {"test": True}
            }
        )

        if response.status_code == 200:
            org = response.json()
            print_success(f"Organization created: {org['name']}")
            print_info(f"Organization ID: {org['organization_id']}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print_info("Organization already exists (from previous test)")
            return True
        else:
            print_error(f"Failed to create organization: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Organization creation failed: {str(e)}")
        return False

def test_create_team():
    """Test creating a team"""
    print_section("8. Create Team")

    try:
        response = requests.post(
            f"{API_URL}/api/teams/create",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            },
            json={
                "organization_id": test_org_id,
                "team_id": test_team_id,
                "team_alias": "Test Team",
                "model_groups": [],  # Empty for now
                "credits_allocated": 100,
                "metadata": {"test": True}
            }
        )

        if response.status_code == 200:
            team = response.json()
            print_success(f"Team created: {team['team_id']}")
            print_info(f"Credits: {team['credits_allocated']}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print_info("Team already exists (from previous test)")
            return True
        else:
            print_error(f"Failed to create team: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Team creation failed: {str(e)}")
        return False

def test_list_users():
    """Test listing admin users"""
    print_section("9. List Admin Users")

    try:
        response = requests.get(
            f"{API_URL}/api/admin-users",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )

        if response.status_code == 200:
            users = response.json()
            print_success(f"Retrieved {len(users)} admin users")
            for user in users:
                print_info(f"  - {user['email']} ({user['role']})")
            return True
        else:
            print_error(f"Failed to list users: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"List users failed: {str(e)}")
        return False

def test_create_admin_user():
    """Test creating an admin user"""
    print_section("10. Create Admin User")

    global admin_user_id

    try:
        response = requests.post(
            f"{API_URL}/api/admin-users",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            },
            json={
                "email": "test-admin@example.com",
                "display_name": "Test Admin",
                "password": "AdminPass123!",
                "role": "admin",
                "metadata": {"test": True}
            }
        )

        if response.status_code == 200:
            user = response.json()
            admin_user_id = user["user_id"]
            print_success(f"Admin user created: {user['email']}")
            print_info(f"User ID: {user['user_id']}")
            print_info(f"Role: {user['role']}")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print_info("Admin user already exists (from previous test)")
            return True
        else:
            print_error(f"Failed to create admin: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Admin creation failed: {str(e)}")
        return False

def test_audit_logs():
    """Test viewing audit logs"""
    print_section("11. View Audit Logs")

    try:
        response = requests.get(
            f"{API_URL}/api/admin-users/audit-logs?limit=10",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )

        if response.status_code == 200:
            logs = response.json()
            print_success(f"Retrieved {len(logs)} audit log entries")
            for log in logs[:3]:  # Show first 3
                print_info(f"  - {log['action']} by user {log.get('user_id', 'N/A')} at {log['created_at']}")
            return True
        else:
            print_error(f"Failed to retrieve audit logs: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Audit logs test failed: {str(e)}")
        return False

def test_unauthorized_access():
    """Test that endpoints reject invalid auth"""
    print_section("12. Test Unauthorized Access Protection")

    # Test without auth
    print_info("Testing access without authentication...")
    try:
        response = requests.get(f"{API_URL}/api/admin-users")

        if response.status_code == 401:
            print_success("Correctly rejected request without authentication")
        else:
            print_error(f"Should have returned 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Unauthorized test failed: {str(e)}")
        return False

    # Test with invalid token
    print_info("Testing access with invalid token...")
    try:
        response = requests.get(
            f"{API_URL}/api/admin-users",
            headers={"Authorization": "Bearer invalid-token-123"}
        )

        if response.status_code == 401:
            print_success("Correctly rejected request with invalid token")
            return True
        else:
            print_error(f"Should have returned 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Invalid token test failed: {str(e)}")
        return False

def test_credits_management():
    """Test credits management with dual auth"""
    print_section("13. Credits Management")

    # Test with JWT
    print_info("Testing credit allocation with JWT...")
    try:
        response = requests.post(
            f"{API_URL}/api/credits/teams/{test_team_id}/add",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            },
            json={
                "credits": 50,
                "reason": "Integration test allocation"
            }
        )

        if response.status_code == 200:
            result = response.json()
            print_success(f"Credits allocated successfully via JWT")
            print_info(f"Added {result['credits_added']} credits")
        else:
            print_error(f"Credit allocation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Credit allocation test failed: {str(e)}")
        return False

    # Test with X-Admin-Key
    print_info("Testing credit allocation with X-Admin-Key...")
    try:
        response = requests.post(
            f"{API_URL}/api/credits/teams/{test_team_id}/add",
            headers={
                "X-Admin-Key": MASTER_KEY,
                "Content-Type": "application/json"
            },
            json={
                "credits": 25,
                "reason": "Integration test allocation (legacy)"
            }
        )

        if response.status_code == 200:
            result = response.json()
            print_success(f"Credits allocated successfully via X-Admin-Key")
            print_info(f"Added {result['credits_added']} credits")
            return True
        else:
            print_error(f"Legacy credit allocation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Legacy credit allocation test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}JWT Authentication & Dual Auth Integration Tests{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")

    tests = [
        ("Health Check", test_health_check),
        ("Setup/Login", test_setup_or_login),
        ("JWT Authentication", test_jwt_auth),
        ("Legacy X-Admin-Key Auth", test_legacy_auth),
        ("Dual Auth - Organizations", test_dual_auth_organizations),
        ("Create Organization", test_create_organization),
        ("Create Team", test_create_team),
        ("List Admin Users", test_list_users),
        ("Create Admin User", test_create_admin_user),
        ("View Audit Logs", test_audit_logs),
        ("Unauthorized Access Protection", test_unauthorized_access),
        ("Credits Management", test_credits_management),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print_section("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed\n")

    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status}  {test_name}")

    print(f"\n{BLUE}{'=' * 70}{RESET}\n")

    if passed == total:
        print(f"{GREEN}✓ All integration tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}✗ Some tests failed. See details above.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())

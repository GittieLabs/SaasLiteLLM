#!/usr/bin/env python3
"""
Minimal Version Test Script
Tests the new model groups, organizations, teams, and credits functionality
"""
import requests
import json
import sys

# Base URL - change if testing remotely
BASE_URL = "http://localhost:8003"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health():
    """Test health endpoint"""
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, "Health check failed"
    print("✅ Health check passed")

def test_create_organization():
    """Create a test organization"""
    print_section("2. Create Organization")
    payload = {
        "organization_id": "org_test_001",
        "name": "Test Organization",
        "metadata": {"plan": "dev"}
    }
    response = requests.post(f"{BASE_URL}/api/organizations/create", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 400 and "already exists" in response.text:
        print("ℹ️  Organization already exists (OK)")
        return "org_test_001"

    assert response.status_code == 200, f"Failed to create organization: {response.text}"
    print("✅ Organization created")
    return response.json()["organization_id"]

def test_create_model_groups():
    """Create model groups"""
    print_section("3. Create Model Groups")

    model_groups = [
        {
            "group_name": "ResumeAgent",
            "display_name": "Resume Analysis Agent",
            "description": "Analyzes resumes and extracts structured data",
            "models": [
                {"model_name": "gpt-4-turbo", "priority": 0},
                {"model_name": "gpt-3.5-turbo", "priority": 1}
            ]
        },
        {
            "group_name": "ParsingAgent",
            "display_name": "Document Parsing Agent",
            "description": "Parses documents into structured format",
            "models": [
                {"model_name": "gpt-3.5-turbo", "priority": 0}
            ]
        },
        {
            "group_name": "RAGAgent",
            "display_name": "RAG Agent",
            "description": "Retrieval Augmented Generation",
            "models": [
                {"model_name": "gpt-4-turbo-preview", "priority": 0}
            ]
        }
    ]

    created_groups = []
    for group in model_groups:
        response = requests.post(f"{BASE_URL}/api/model-groups/create", json=group)
        print(f"\nCreating {group['group_name']}...")
        print(f"Status: {response.status_code}")

        if response.status_code == 400 and "already exists" in response.text:
            print(f"ℹ️  {group['group_name']} already exists (OK)")
            created_groups.append(group['group_name'])
        elif response.status_code == 200:
            print(f"✅ {group['group_name']} created")
            created_groups.append(response.json()["group_name"])
        else:
            print(f"❌ Failed: {response.text}")

    # List all model groups
    print("\nListing all model groups:")
    response = requests.get(f"{BASE_URL}/api/model-groups")
    groups = response.json()
    for group in groups:
        print(f"  - {group['group_name']}: {len(group['models'])} models configured")

    print(f"\n✅ Model groups ready: {created_groups}")
    return created_groups

def test_create_team(org_id, model_groups):
    """Create a team with model groups and credits"""
    print_section("4. Create Team")

    payload = {
        "organization_id": org_id,
        "team_id": "team_test_hr",
        "team_alias": "Test HR Team",
        "model_groups": model_groups,
        "credits_allocated": 100,
        "metadata": {"department": "HR"}
    }

    response = requests.post(f"{BASE_URL}/api/teams/create", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 400 and "already exists" in response.text:
        print("ℹ️  Team already exists (OK)")
        return "team_test_hr"

    assert response.status_code == 200, f"Failed to create team: {response.text}"
    print("✅ Team created with model groups and credits")
    return response.json()["team_id"]

def test_check_credits(team_id):
    """Check team credit balance"""
    print_section("5. Check Credit Balance")

    response = requests.get(f"{BASE_URL}/api/credits/teams/{team_id}/balance")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Failed to get credits: {response.text}"
    print("✅ Credit balance retrieved")
    return response.json()

def test_add_credits(team_id):
    """Add credits to team"""
    print_section("6. Add Credits")

    payload = {
        "credits": 50,
        "reason": "Test allocation"
    }

    response = requests.post(f"{BASE_URL}/api/credits/teams/{team_id}/add", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Failed to add credits: {response.text}"
    print("✅ Credits added successfully")

def test_get_model_group(group_name):
    """Get specific model group details"""
    print_section(f"7. Get Model Group: {group_name}")

    response = requests.get(f"{BASE_URL}/api/model-groups/{group_name}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Failed to get model group: {response.text}"
    print(f"✅ Model group {group_name} retrieved")

def test_get_team(team_id):
    """Get team details"""
    print_section(f"8. Get Team Details")

    response = requests.get(f"{BASE_URL}/api/teams/{team_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Failed to get team: {response.text}"
    print("✅ Team details retrieved")

def main():
    """Run all tests"""
    print(f"\n{'#'*60}")
    print(f"#  MINIMAL VERSION TEST SUITE")
    print(f"#  Testing Model Groups, Organizations, Teams & Credits")
    print(f"#  Base URL: {BASE_URL}")
    print(f"{'#'*60}")

    try:
        # Run tests
        test_health()
        org_id = test_create_organization()
        model_groups = test_create_model_groups()
        team_id = test_create_team(org_id, model_groups)
        test_check_credits(team_id)
        test_add_credits(team_id)
        test_get_model_group("ResumeAgent")
        test_get_team(team_id)

        # Summary
        print_section("TEST SUMMARY")
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("1. Run migrations: ./scripts/run_migrations.sh")
        print("2. Check API docs: http://localhost:8003/docs")
        print("3. Test model resolution and credit deduction with actual jobs")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Could not connect to {BASE_URL}")
        print("Make sure the SaaS API is running:")
        print("  python scripts/start_saas_api.py")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

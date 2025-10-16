#!/usr/bin/env python3
"""
Test organization creation with automatic default team
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8003"

def test_organization_with_default_team():
    print("\n" + "="*70)
    print("  TESTING: Organization Creation with Default Team")
    print("="*70 + "\n")

    # 1. Create organization with default team
    print("1. Creating organization with default team...")
    response = requests.post(
        f"{BASE_URL}/api/organizations/create",
        json={
            "organization_id": "org_test_002",
            "name": "Test Organization 2",
            "metadata": {"tier": "basic"},
            "create_default_team": True,
            "default_team_model_groups": ["ChatAgent"],
            "default_team_credits": 50
        }
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 400 and "already exists" in response.text:
        print("   Organization already exists (OK)")
        # Try to get the organization
        org_response = requests.get(f"{BASE_URL}/api/organizations/org_test_002")
        org_data = org_response.json()
        print("\n   Existing organization:")
        print(json.dumps(org_data, indent=2))
    elif response.status_code == 200:
        org_data = response.json()
        print("\n" + "-"*70)
        print("ORGANIZATION CREATED WITH DEFAULT TEAM!")
        print("-"*70)
        print(json.dumps(org_data, indent=2))
        print("-"*70)

        # Check if default team was created
        if org_data.get("default_team"):
            default_team = org_data["default_team"]
            print("\nDEFAULT TEAM INFORMATION:")
            print(f"  Team ID: {default_team.get('team_id')}")
            print(f"  Team Alias: {default_team.get('team_alias')}")
            print(f"  Virtual Key: {default_team.get('virtual_key', 'Not generated')}")
            print(f"  Model Groups: {default_team.get('model_groups')}")
            print(f"  Credits: {default_team.get('credits_allocated')}")

            # Verify team exists in database
            team_id = default_team.get('team_id')
            if team_id:
                print(f"\n2. Verifying team '{team_id}' in database...")
                team_response = requests.get(f"{BASE_URL}/api/teams/{team_id}")
                if team_response.status_code == 200:
                    print("   ✓ Team found in database")
                    team_data = team_response.json()
                    print(f"   - Credits: {team_data.get('credits_allocated')} allocated")
                    print(f"   - Model Groups: {team_data.get('model_groups')}")
                    print(f"   - Virtual Key: {'Present' if team_data.get('virtual_key') else 'None'}")
                else:
                    print(f"   ✗ Team not found: {team_response.status_code}")
        else:
            print("\n⚠ No default team was created")

    else:
        print(f"\n✗ Failed to create organization: {response.text}")
        return False

    # 3. Test creating organization WITHOUT default team
    print("\n3. Creating organization WITHOUT default team...")
    response = requests.post(
        f"{BASE_URL}/api/organizations/create",
        json={
            "organization_id": "org_test_003",
            "name": "Test Organization 3 (No Team)",
            "metadata": {"tier": "basic"},
            "create_default_team": False
        }
    )

    if response.status_code == 400 and "already exists" in response.text:
        print("   Organization already exists (OK)")
    elif response.status_code == 200:
        org_data = response.json()
        print("   ✓ Organization created without default team")
        if org_data.get("default_team") is None:
            print("   ✓ Confirmed: No default team created")
        else:
            print("   ⚠ Unexpected: default_team field present")

    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)

    return True


if __name__ == "__main__":
    try:
        test_organization_with_default_team()
        sys.exit(0)
    except requests.exceptions.ConnectionError:
        print(f"\nConnection Error: Could not connect to {BASE_URL}")
        print("Make sure the SaaS API is running")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

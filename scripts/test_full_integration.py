#!/usr/bin/env python3
"""
Test creating a team with LiteLLM integration
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8003"

def test_create_team_with_litellm():
    print("\n" + "="*70)
    print("  TESTING: Create Team with LiteLLM Integration")
    print("="*70 + "\n")

    # 1. Create organization
    print("1. Creating organization...")
    response = requests.post(
        f"{BASE_URL}/api/organizations/create",
        json={
            "organization_id": "org_demo_001",
            "name": "Demo Organization",
            "metadata": {"tier": "premium"}
        }
    )
    if response.status_code == 400 and "already exists" in response.text:
        print("   Organization already exists (OK)")
    else:
        print(f"   Status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        print("   Created successfully")

    # 2. Create model groups
    print("\n2. Creating model groups...")
    model_groups = [
        {
            "group_name": "ChatAgent",
            "display_name": "Chat Agent",
            "description": "General purpose chat agent",
            "models": [
                {"model_name": "gpt-3.5-turbo", "priority": 0},
                {"model_name": "gpt-4", "priority": 1}
            ]
        },
        {
            "group_name": "AnalysisAgent",
            "display_name": "Analysis Agent",
            "description": "Data analysis agent",
            "models": [
                {"model_name": "gpt-4", "priority": 0}
            ]
        }
    ]

    for group in model_groups:
        response = requests.post(
            f"{BASE_URL}/api/model-groups/create",
            json=group
        )
        if response.status_code == 400 and "already exists" in response.text:
            print(f"   {group['group_name']} already exists (OK)")
        else:
            assert response.status_code == 200, f"Failed to create {group['group_name']}: {response.text}"
            print(f"   {group['group_name']} created")

    # 3. Create team with LiteLLM integration
    print("\n3. Creating team with LiteLLM integration...")
    print("   This will:")
    print("   - Create team in LiteLLM")
    print("   - Generate virtual API key")
    print("   - Assign model groups")
    print("   - Allocate 100 credits")
    print()

    response = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "organization_id": "org_demo_001",
            "team_id": "team_demo_engineering",
            "team_alias": "Demo Engineering Team",
            "model_groups": ["ChatAgent", "AnalysisAgent"],
            "credits_allocated": 100,
            "metadata": {"department": "engineering"}
        }
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 400 and "already exists" in response.text:
        print("   Team already exists, fetching details...")
        response = requests.get(f"{BASE_URL}/api/teams/team_demo_engineering")
        team_data = response.json()
    elif response.status_code == 500:
        print("\n   ERROR: LiteLLM integration failed!")
        print("   Response:", response.text)
        print("\n   Possible causes:")
        print("   - LiteLLM proxy not running")
        print("   - LiteLLM database not accessible")
        print("   - Master key incorrect")
        return False
    else:
        team_data = response.json()

    print("\n" + "-"*70)
    print("TEAM CREATED SUCCESSFULLY!")
    print("-"*70)
    print(json.dumps(team_data, indent=2))
    print("-"*70)

    # Extract key information
    team_id = team_data.get("team_id")
    virtual_key = team_data.get("virtual_key")
    model_groups_assigned = team_data.get("model_groups", [])
    credits = team_data.get("credits_allocated")

    print("\nKEY INFORMATION:")
    print(f"  Team ID: {team_id}")
    print(f"  Virtual Key: {virtual_key[:30]}..." if virtual_key else "  Virtual Key: Not generated")
    print(f"  Model Groups: {', '.join(model_groups_assigned)}")
    print(f"  Credits Allocated: {credits}")

    # 4. Verify team appears in our database
    print("\n4. Verifying team in SaaS API database...")
    response = requests.get(f"{BASE_URL}/api/teams/{team_id}")
    assert response.status_code == 200, "Team not found in database"
    print("   Team verified in database")

    # 5. Check credit balance
    print("\n5. Checking credit balance...")
    response = requests.get(f"{BASE_URL}/api/credits/teams/{team_id}/balance")
    assert response.status_code == 200, "Failed to get credits"
    credits_data = response.json()
    print(f"   Credits: {credits_data['credits_remaining']} remaining")

    # 6. Instructions for viewing in LiteLLM
    print("\n" + "="*70)
    print("SUCCESS! Team created with full LiteLLM integration")
    print("="*70)
    print("\nTO VIEW IN LITELLM DASHBOARD:")
    print("  1. Open: http://localhost:8002/ui/")
    print("  2. Login with master key: sk-local-dev-master-key-change-me")
    print("  3. Go to 'Teams' section")
    print(f"  4. Look for team: {team_id}")
    print("\nTO VIEW VIRTUAL KEYS:")
    print("  - Go to 'Keys' section in LiteLLM dashboard")
    print(f"  - Look for key: {team_id}_key")
    print("\nNEXT STEPS:")
    print("  - Add OpenAI API key in LiteLLM dashboard")
    print("  - Create models (gpt-3.5-turbo, gpt-4) in LiteLLM")
    print("  - Test making LLM calls with the team's virtual key")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_create_team_with_litellm()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\nConnection Error: Could not connect to {BASE_URL}")
        print("Make sure the SaaS API is running:")
        print("  python -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

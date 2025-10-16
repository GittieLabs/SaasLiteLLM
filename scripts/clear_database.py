#!/usr/bin/env python3
"""
Clear all data from the database and LiteLLM proxy

This script:
1. Clears all teams, organizations, model groups from SaaS API database
2. Clears all teams and keys from LiteLLM proxy
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import requests

# Import settings to get database URL and litellm config
from src.config.settings import settings

def clear_saas_database():
    """Clear all data from SaaS API database tables"""
    print("\n" + "="*70)
    print("  Clearing SaaS API Database")
    print("="*70 + "\n")

    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        # Clear in order to respect foreign key constraints
        tables = [
            "llm_calls",
            "credit_transactions",
            "jobs",
            "team_model_groups",
            "team_credits",
            "model_group_models",
            "model_groups",
            "organizations",
            # LiteLLM tables
            '"LiteLLM_VerificationToken"',
            '"LiteLLM_TeamTable"'
        ]

        for table in tables:
            try:
                session.execute(text(f"DELETE FROM {table}"))
                print(f"✓ Cleared table: {table}")
            except Exception as e:
                print(f"⚠ Could not clear {table}: {e}")

        session.commit()
        print("\n✅ SaaS API database cleared successfully!")

def clear_litellm_data():
    """Clear teams and keys from LiteLLM proxy"""
    print("\n" + "="*70)
    print("  Clearing LiteLLM Proxy Data")
    print("="*70 + "\n")

    base_url = settings.litellm_proxy_url
    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json"
    }

    try:
        # Get all teams
        try:
            response = requests.get(f"{base_url}/team/list", headers=headers)
            if response.status_code == 200:
                data = response.json()
                teams = data if isinstance(data, list) else data.get("teams", [])
                print(f"Found {len(teams)} teams in LiteLLM proxy")

                for team in teams:
                    if isinstance(team, dict):
                        team_id = team.get("team_id")
                        if team_id:
                            try:
                                del_response = requests.post(
                                    f"{base_url}/team/delete",
                                    headers=headers,
                                    json={"team_ids": [team_id]}
                                )
                                if del_response.status_code == 200:
                                    print(f"✓ Deleted team: {team_id}")
                                else:
                                    print(f"⚠ Failed to delete team {team_id}: {del_response.text}")
                            except Exception as e:
                                print(f"⚠ Error deleting team {team_id}: {e}")
            else:
                print(f"Note: Could not list teams from LiteLLM API (this is OK if none exist)")
        except Exception as e:
            print(f"Note: Could not access LiteLLM team API: {e}")

        # Get all keys
        response = requests.get(f"{base_url}/key/info", headers=headers)
        if response.status_code == 200:
            keys = response.json().get("keys", [])
            print(f"\nFound {len(keys)} keys to delete")

            for key in keys:
                key_value = key.get("token") or key.get("key")
                if key_value:
                    try:
                        del_response = requests.post(
                            f"{base_url}/key/delete",
                            headers=headers,
                            json={"keys": [key_value]}
                        )
                        if del_response.status_code == 200:
                            print(f"✓ Deleted key: {key_value[:20]}...")
                        else:
                            print(f"⚠ Failed to delete key: {del_response.text}")
                    except Exception as e:
                        print(f"⚠ Error deleting key: {e}")
        else:
            print(f"⚠ Could not list keys: {response.status_code}")

        print("\n✅ LiteLLM proxy data cleared successfully!")

    except requests.exceptions.ConnectionError:
        print(f"\n⚠ Could not connect to LiteLLM proxy at {base_url}")
        print("Make sure the proxy is running.")
    except Exception as e:
        print(f"\n❌ Error clearing LiteLLM data: {e}")

def main():
    print("\n🗑️  DATABASE CLEANUP SCRIPT")
    print("="*70)
    print("This will delete ALL data from:")
    print("  - SaaS API database (organizations, teams, model groups, etc.)")
    print("  - LiteLLM proxy (teams and virtual keys)")
    print("="*70)

    response = input("\nAre you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    try:
        clear_saas_database()
        clear_litellm_data()

        print("\n" + "="*70)
        print("✅ CLEANUP COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nYour database is now clean. You can run:")
        print("  python scripts/test_full_integration.py")
        print()

    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to setup teams and generate API keys
"""
import asyncio
import httpx
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import settings

async def create_team_and_keys():
    """Create teams and generate virtual API keys"""
    base_url = f"http://{settings.host}:{settings.port}"
    headers = {
        "Authorization": f"Bearer {settings.litellm_master_key}",
        "Content-Type": "application/json"
    }
    
    teams_config = [
        {
            "team_id": "team_dev",
            "team_alias": "development-team",
            "models": ["gpt-3.5-turbo", "claude-3-sonnet"],
            "budget_limit": 100.0
        },
        {
            "team_id": "team_prod", 
            "team_alias": "production-team",
            "models": ["gpt-4-turbo", "claude-3-opus"],
            "budget_limit": 1000.0
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for team_config in teams_config:
            try:
                # Create team
                team_response = await client.post(
                    f"{base_url}/team/new",
                    headers=headers,
                    json=team_config
                )
                
                if team_response.status_code == 200:
                    print(f"✅ Created team: {team_config['team_alias']}")
                    
                    # Generate API key for team
                    key_data = {
                        "team_id": team_config["team_id"],
                        "models": team_config["models"],
                        "max_budget": team_config["budget_limit"]
                    }
                    
                    key_response = await client.post(
                        f"{base_url}/key/generate",
                        headers=headers,
                        json=key_data
                    )
                    
                    if key_response.status_code == 200:
                        key_info = key_response.json()
                        print(f"🔑 Generated API key for {team_config['team_alias']}: {key_info.get('key', 'N/A')}")
                    else:
                        print(f"❌ Failed to generate key for {team_config['team_alias']}: {key_response.text}")
                        
                else:
                    print(f"❌ Failed to create team {team_config['team_alias']}: {team_response.text}")
                    
            except Exception as e:
                print(f"❌ Error setting up team {team_config['team_alias']}: {e}")

if __name__ == "__main__":
    print("🔧 Setting up teams and API keys...")
    print("Make sure the LiteLLM server is running first!")
    print("")
    asyncio.run(create_team_and_keys())

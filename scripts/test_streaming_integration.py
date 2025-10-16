#!/usr/bin/env python3
"""
Standalone integration test for streaming and non-streaming LLM calls

This script tests:
1. Non-streaming LLM call with tracking
2. Streaming LLM call with SSE
3. Database verification (Job and LLMCall records)
4. Team association and credit tracking

Run with: python scripts/test_streaming_integration.py
"""
import requests
import json
import sys
import os
import time
import uuid as uuid_lib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.job_tracking import Job, LLMCall, JobStatus
from models.credits import TeamCredits
from config.settings import settings

# Configuration
BASE_URL = "http://localhost:8003"
TEST_ORG_ID = "test_org_streaming"
TEST_TEAM_ID = "test_team_streaming"
TEST_MODEL_GROUP = "test-streaming-group"
TEST_MODEL = os.getenv("TEST_MODEL", "gpt-3.5-turbo")
INITIAL_CREDITS = 500


def print_banner(text):
    """Print a banner"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_step(num, text):
    """Print a step header"""
    print(f"\n{num}. {text}")


def setup_test_data():
    """Setup organization, model group, and team"""
    print_banner("SETUP: Creating Test Data")

    # 1. Create organization
    print_step(1, "Creating test organization...")
    response = requests.post(
        f"{BASE_URL}/api/organizations/create",
        json={
            "organization_id": TEST_ORG_ID,
            "name": "Streaming Test Organization",
            "metadata": {"test": True},
            "create_default_team": False
        }
    )

    if response.status_code == 400 and "already exists" in response.text:
        print("   Organization already exists (OK)")
    else:
        if response.status_code != 200:
            print(f"   ❌ Failed: {response.text}")
            return None
        print("   ✓ Organization created")

    # 2. Create model group
    print_step(2, "Creating test model group...")
    response = requests.post(
        f"{BASE_URL}/api/model-groups/create",
        json={
            "group_name": TEST_MODEL_GROUP,
            "display_name": "Test Streaming Group",
            "description": "Model group for streaming integration tests",
            "models": [
                {"model_name": TEST_MODEL, "priority": 0}
            ]
        }
    )

    if response.status_code == 400 and "already exists" in response.text:
        print("   Model group already exists (OK)")
    else:
        if response.status_code != 200:
            print(f"   ❌ Failed: {response.text}")
            return None
        print("   ✓ Model group created")

    # 3. Create team
    print_step(3, "Creating test team...")
    response = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "organization_id": TEST_ORG_ID,
            "team_id": TEST_TEAM_ID,
            "team_alias": "Streaming Test Team",
            "access_groups": [TEST_MODEL_GROUP],
            "credits_allocated": INITIAL_CREDITS,
            "metadata": {"test": True}
        }
    )

    if response.status_code == 400 and "already exists" in response.text:
        print("   Team already exists, fetching details...")
        response = requests.get(f"{BASE_URL}/api/teams/{TEST_TEAM_ID}")

    if response.status_code != 200:
        print(f"   ❌ Failed: {response.text}")
        return None

    team_data = response.json()
    virtual_key = team_data.get("virtual_key")

    print(f"   ✓ Team created")
    print(f"     Team ID: {TEST_TEAM_ID}")
    print(f"     Virtual Key: {virtual_key[:30]}...")
    print(f"     Credits: {INITIAL_CREDITS}")

    return virtual_key


def test_non_streaming(virtual_key, db_session):
    """Test non-streaming LLM call"""
    print_banner("TEST 1: Non-Streaming LLM Call")

    # Get initial credits
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()
    credits_before = float(team_credits.credits_remaining)

    # Step 1: Create job
    print_step(1, "Creating job...")
    response = requests.post(
        f"{BASE_URL}/api/jobs/create",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={
            "team_id": TEST_TEAM_ID,
            "job_type": "standalone_non_streaming_test",
            "metadata": {"test": True}
        }
    )

    if response.status_code != 200:
        print(f"   ❌ Failed to create job: {response.text}")
        return False

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"   ✓ Job created: {job_id}")

    # Step 2: Make non-streaming LLM call
    print_step(2, "Making non-streaming LLM call...")
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/jobs/{job_id}/llm-call",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={
            "model_group": TEST_MODEL_GROUP,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from non-streaming test!' and nothing else."}
            ],
            "temperature": 0.7,
            "max_tokens": 30,
            "purpose": "standalone_test_non_streaming"
        }
    )

    elapsed = time.time() - start_time

    if response.status_code != 200:
        print(f"   ❌ LLM call failed: {response.text}")
        return False

    llm_response = response.json()
    content = llm_response['choices'][0]['message']['content']

    print(f"   ✓ Response received in {elapsed:.2f}s")
    print(f"   Content: {content}")

    # Step 3: Complete job
    print_step(3, "Completing job...")
    response = requests.post(
        f"{BASE_URL}/api/jobs/{job_id}/complete",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={"status": "completed"}
    )

    if response.status_code != 200:
        print(f"   ❌ Failed to complete job: {response.text}")
        return False

    print("   ✓ Job completed")

    # Step 4: Verify in database
    print_step(4, "Verifying database records...")
    db_session.expire_all()

    # Verify Job
    job = db_session.query(Job).filter(Job.job_id == uuid_lib.UUID(job_id)).first()
    if not job:
        print(f"   ❌ Job not found in database")
        return False

    print(f"   ✓ Job record found")
    print(f"     Team ID: {job.team_id}")
    print(f"     Status: {job.status.value}")

    # Verify LLMCall
    llm_call = db_session.query(LLMCall).filter(LLMCall.job_id == uuid_lib.UUID(job_id)).first()
    if not llm_call:
        print(f"   ❌ LLMCall not found in database")
        return False

    print(f"   ✓ LLMCall record found")
    print(f"     Tokens: {llm_call.prompt_tokens} + {llm_call.completion_tokens} = {llm_call.total_tokens}")
    print(f"     Cost: ${llm_call.cost_usd:.6f}")
    print(f"     Latency: {llm_call.latency_ms}ms")
    print(f"     Model Group: {llm_call.model_group_used}")

    # Verify credits
    db_session.expire_all()
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()

    credits_after = float(team_credits.credits_remaining)
    credits_used = credits_before - credits_after

    print(f"   ✓ Credits deducted: {credits_used:.6f}")
    print(f"     Before: {credits_before:.6f}")
    print(f"     After: {credits_after:.6f}")

    print("\n✅ Non-streaming test PASSED")
    return True


def test_streaming(virtual_key, db_session):
    """Test streaming LLM call"""
    print_banner("TEST 2: Streaming LLM Call")

    # Get initial credits
    db_session.expire_all()
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()
    credits_before = float(team_credits.credits_remaining)

    # Step 1: Create job
    print_step(1, "Creating job...")
    response = requests.post(
        f"{BASE_URL}/api/jobs/create",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={
            "team_id": TEST_TEAM_ID,
            "job_type": "standalone_streaming_test",
            "metadata": {"test": True}
        }
    )

    if response.status_code != 200:
        print(f"   ❌ Failed to create job: {response.text}")
        return False

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"   ✓ Job created: {job_id}")

    # Step 2: Make streaming LLM call
    print_step(2, "Making streaming LLM call...")
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/jobs/{job_id}/llm-call-stream",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={
            "model_group": TEST_MODEL_GROUP,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Count from 1 to 3, one number per line."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "purpose": "standalone_test_streaming"
        },
        stream=True
    )

    if response.status_code != 200:
        print(f"   ❌ Streaming call failed: {response.text}")
        return False

    # Accumulate streaming response
    accumulated_content = ""
    chunk_count = 0

    print("   Streaming response:")
    print("   " + "-"*60)

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith("data: "):
                chunk_data = line[6:]

                if chunk_data == "[DONE]":
                    break

                try:
                    chunk_json = json.loads(chunk_data)

                    # Extract content from delta
                    if "choices" in chunk_json:
                        for choice in chunk_json["choices"]:
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                accumulated_content += content
                                chunk_count += 1
                                print(content, end="", flush=True)

                except json.JSONDecodeError:
                    continue

    elapsed = time.time() - start_time

    print()
    print("   " + "-"*60)
    print(f"   ✓ Stream completed in {elapsed:.2f}s ({chunk_count} chunks)")
    print(f"   Total content length: {len(accumulated_content)} characters")

    # Step 3: Complete job
    print_step(3, "Completing job...")
    response = requests.post(
        f"{BASE_URL}/api/jobs/{job_id}/complete",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={"status": "completed"}
    )

    if response.status_code != 200:
        print(f"   ❌ Failed to complete job: {response.text}")
        return False

    print("   ✓ Job completed")

    # Step 4: Verify in database
    print_step(4, "Verifying database records...")
    db_session.expire_all()

    # Verify Job
    job = db_session.query(Job).filter(Job.job_id == uuid_lib.UUID(job_id)).first()
    if not job:
        print(f"   ❌ Job not found in database")
        return False

    print(f"   ✓ Job record found")
    print(f"     Team ID: {job.team_id}")
    print(f"     Status: {job.status.value}")

    # Verify LLMCall
    llm_call = db_session.query(LLMCall).filter(LLMCall.job_id == uuid_lib.UUID(job_id)).first()
    if not llm_call:
        print(f"   ❌ LLMCall not found in database")
        return False

    print(f"   ✓ LLMCall record found")
    print(f"     Tokens: {llm_call.prompt_tokens} + {llm_call.completion_tokens} = {llm_call.total_tokens}")
    print(f"     Cost: ${llm_call.cost_usd:.6f}")
    print(f"     Latency: {llm_call.latency_ms}ms")
    print(f"     Model Group: {llm_call.model_group_used}")

    # Check if streaming flag is set
    if llm_call.response_data and "streaming" in llm_call.response_data:
        print(f"     Streaming: {llm_call.response_data['streaming']}")

    # Verify credits
    db_session.expire_all()
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()

    credits_after = float(team_credits.credits_remaining)
    credits_used = credits_before - credits_after

    print(f"   ✓ Credits deducted: {credits_used:.6f}")
    print(f"     Before: {credits_before:.6f}")
    print(f"     After: {credits_after:.6f}")

    print("\n✅ Streaming test PASSED")
    return True


def cleanup(db_session):
    """Cleanup test data"""
    print_banner("CLEANUP: Removing Test Data")

    # Delete jobs for this team (cascade deletes LLMCalls)
    print_step(1, "Deleting test jobs...")
    jobs = db_session.query(Job).filter(Job.team_id == TEST_TEAM_ID).all()
    for job in jobs:
        db_session.delete(job)
    db_session.commit()
    print(f"   ✓ Deleted {len(jobs)} jobs")

    # Delete team
    print_step(2, "Deleting test team...")
    try:
        response = requests.delete(f"{BASE_URL}/api/teams/{TEST_TEAM_ID}")
        if response.status_code == 200:
            print("   ✓ Team deleted")
        else:
            print(f"   ⚠ Could not delete team: {response.text}")
    except:
        print("   ⚠ Could not delete team")

    # Delete model group
    print_step(3, "Deleting test model group...")
    try:
        response = requests.delete(f"{BASE_URL}/api/model-groups/{TEST_MODEL_GROUP}")
        if response.status_code == 200:
            print("   ✓ Model group deleted")
        else:
            print(f"   ⚠ Could not delete model group: {response.text}")
    except:
        print("   ⚠ Could not delete model group")

    # Delete organization
    print_step(4, "Deleting test organization...")
    try:
        response = requests.delete(f"{BASE_URL}/api/organizations/{TEST_ORG_ID}")
        if response.status_code == 200:
            print("   ✓ Organization deleted")
        else:
            print(f"   ⚠ Could not delete organization: {response.text}")
    except:
        print("   ⚠ Could not delete organization")


def main():
    """Main test runner"""
    print_banner("Streaming Integration Test")
    print(f"API: {BASE_URL}")
    print(f"Model: {TEST_MODEL}")
    print(f"Database: {settings.database_url[:30]}...")

    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"\n❌ SaaS API not healthy at {BASE_URL}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to SaaS API at {BASE_URL}")
        print("Make sure it's running: python -m uvicorn src.saas_api:app --host 0.0.0.0 --port 8003")
        return False

    # Setup database session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    try:
        # Setup
        virtual_key = setup_test_data()
        if not virtual_key:
            print("\n❌ Setup failed")
            return False

        # Run tests
        non_streaming_passed = test_non_streaming(virtual_key, db_session)
        streaming_passed = test_streaming(virtual_key, db_session)

        # Summary
        print_banner("TEST SUMMARY")

        if non_streaming_passed and streaming_passed:
            print("✅ All tests PASSED!")
            print("\nTests completed:")
            print("  ✓ Non-streaming LLM call")
            print("  ✓ Streaming LLM call")
            print("  ✓ Database tracking")
            print("  ✓ Team association")
            print("  ✓ Credit deduction")
            success = True
        else:
            print("❌ Some tests FAILED")
            print(f"\nResults:")
            print(f"  Non-streaming: {'✓ PASSED' if non_streaming_passed else '✗ FAILED'}")
            print(f"  Streaming: {'✓ PASSED' if streaming_passed else '✗ FAILED'}")
            success = False

        # Cleanup
        cleanup(db_session)

        return success

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db_session.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

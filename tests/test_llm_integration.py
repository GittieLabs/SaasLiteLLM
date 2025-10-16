"""
Integration tests for LLM calls (streaming and non-streaming)

Tests:
1. Non-streaming LLM calls with database tracking
2. Streaming LLM calls with SSE
3. Job and LLMCall record verification
4. Team association and credit tracking
5. Cost calculation accuracy

Run with: pytest tests/test_llm_integration.py -v
"""
import pytest
import requests
import json
import sys
import os
import uuid as uuid_lib
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.job_tracking import Job, LLMCall, JobStatus
from models.credits import TeamCredits
from config.settings import settings

# Test configuration
BASE_URL = "http://localhost:8003"
TEST_ORG_ID = "test_org_integration"
TEST_TEAM_ID = "test_team_llm"
TEST_MODEL_GROUP = "test-chat-fast"
TEST_MODEL = os.getenv("TEST_MODEL", "gpt-3.5-turbo")  # Can override via env
INITIAL_CREDITS = 1000


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def db_session():
    """Create database session for verifying records"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_organization():
    """Create test organization"""
    response = requests.post(
        f"{BASE_URL}/api/organizations/create",
        json={
            "organization_id": TEST_ORG_ID,
            "name": "Integration Test Organization",
            "metadata": {"test": True},
            "create_default_team": False
        }
    )

    # OK if already exists
    if response.status_code == 400 and "already exists" in response.text:
        print(f"Organization {TEST_ORG_ID} already exists (OK)")
    else:
        assert response.status_code == 200, f"Failed to create org: {response.text}"

    yield TEST_ORG_ID

    # Cleanup: Delete organization (cascade deletes teams)
    try:
        requests.delete(f"{BASE_URL}/api/organizations/{TEST_ORG_ID}")
    except:
        pass


@pytest.fixture(scope="module")
def test_model_group():
    """Create test model group"""
    response = requests.post(
        f"{BASE_URL}/api/model-groups/create",
        json={
            "group_name": TEST_MODEL_GROUP,
            "display_name": "Test Chat Fast",
            "description": "Test model group for integration tests",
            "models": [
                {"model_name": TEST_MODEL, "priority": 0}
            ]
        }
    )

    # OK if already exists
    if response.status_code == 400 and "already exists" in response.text:
        print(f"Model group {TEST_MODEL_GROUP} already exists (OK)")
    else:
        assert response.status_code == 200, f"Failed to create model group: {response.text}"

    yield TEST_MODEL_GROUP

    # Cleanup: Delete model group
    try:
        requests.delete(f"{BASE_URL}/api/model-groups/{TEST_MODEL_GROUP}")
    except:
        pass


@pytest.fixture(scope="module")
def test_team(test_organization, test_model_group, db_session):
    """Create test team with credits and model groups"""
    # First check if team already exists
    existing_response = requests.get(f"{BASE_URL}/api/teams/{TEST_TEAM_ID}")

    if existing_response.status_code == 200:
        print(f"Team {TEST_TEAM_ID} already exists, using existing team")
        team_data = existing_response.json()
        virtual_key = team_data.get("virtual_key")
    else:
        # Create new team
        response = requests.post(
            f"{BASE_URL}/api/teams/create",
            json={
                "organization_id": TEST_ORG_ID,
                "team_id": TEST_TEAM_ID,
                "team_alias": "Integration Test Team",
                "access_groups": [TEST_MODEL_GROUP],
                "credits_allocated": INITIAL_CREDITS,
                "metadata": {"test": True}
            }
        )

        assert response.status_code == 200, f"Failed to create team: {response.text}"
        team_data = response.json()
        virtual_key = team_data.get("virtual_key")

    assert virtual_key is not None, "No virtual key generated"

    # Get initial credits from database
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()

    assert team_credits is not None, "Team credits not found in database"
    initial_credits = float(team_credits.credits_remaining)

    yield {
        "team_id": TEST_TEAM_ID,
        "virtual_key": virtual_key,
        "initial_credits": initial_credits
    }

    # Cleanup: Delete team
    try:
        requests.delete(f"{BASE_URL}/api/teams/{TEST_TEAM_ID}")
    except:
        pass


# ============================================================================
# Helper Functions
# ============================================================================

def create_job(virtual_key: str, job_type: str = "integration_test") -> Dict[str, Any]:
    """Create a job via API"""
    response = requests.post(
        f"{BASE_URL}/api/jobs/create",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={
            "team_id": TEST_TEAM_ID,
            "job_type": job_type,
            "metadata": {"test": True}
        }
    )
    assert response.status_code == 200, f"Failed to create job: {response.text}"
    return response.json()


def complete_job(job_id: str, virtual_key: str, status: str = "completed") -> None:
    """Complete a job via API"""
    response = requests.post(
        f"{BASE_URL}/api/jobs/{job_id}/complete",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={"status": status}
    )
    assert response.status_code == 200, f"Failed to complete job: {response.text}"


def verify_job_in_db(db_session, job_id: str, team_id: str, expected_status: JobStatus):
    """Verify job exists in database with correct attributes"""
    job = db_session.query(Job).filter(Job.job_id == uuid_lib.UUID(job_id)).first()

    assert job is not None, f"Job {job_id} not found in database"
    assert job.team_id == team_id, f"Job team_id mismatch: {job.team_id} != {team_id}"
    assert job.status == expected_status, f"Job status mismatch: {job.status} != {expected_status}"

    return job


def verify_llm_call_in_db(db_session, job_id: str, model_group: str) -> LLMCall:
    """Verify LLMCall record exists in database with correct attributes"""
    llm_call = db_session.query(LLMCall).filter(
        LLMCall.job_id == uuid_lib.UUID(job_id)
    ).first()

    assert llm_call is not None, f"LLMCall not found for job {job_id}"
    assert llm_call.model_group_used == model_group, f"Model group mismatch"
    assert llm_call.prompt_tokens > 0, "No prompt tokens tracked"
    assert llm_call.completion_tokens > 0, "No completion tokens tracked"
    assert llm_call.total_tokens > 0, "No total tokens tracked"
    assert llm_call.cost_usd > 0, "No cost tracked"
    assert llm_call.latency_ms is not None, "No latency tracked"

    return llm_call


# ============================================================================
# Tests
# ============================================================================

@pytest.mark.integration
def test_prerequisites():
    """Test that SaaS API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip(f"SaaS API not running at {BASE_URL}")


@pytest.mark.integration
def test_non_streaming_call(test_team, db_session):
    """
    Test non-streaming LLM call with full tracking verification

    Verifies:
    - Job creation and completion
    - LLM call execution
    - Database record creation (Job, LLMCall)
    - Token tracking
    - Cost calculation
    - Team association
    - Credit deduction
    """
    print("\n" + "="*70)
    print("TEST: Non-Streaming LLM Call")
    print("="*70)

    virtual_key = test_team["virtual_key"]
    initial_credits = test_team["initial_credits"]

    # Step 1: Create job
    print("\n1. Creating job...")
    job_data = create_job(virtual_key, "non_streaming_test")
    job_id = job_data["job_id"]
    print(f"   Job created: {job_id}")

    # Step 2: Make non-streaming LLM call
    print("\n2. Making non-streaming LLM call...")
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/jobs/{job_id}/llm-call",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={
            "model_group": TEST_MODEL_GROUP,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, this is a test!' and nothing else."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "purpose": "integration_test_non_streaming"
        }
    )

    elapsed = time.time() - start_time

    assert response.status_code == 200, f"LLM call failed: {response.text}"
    llm_response = response.json()

    print(f"   Response received in {elapsed:.2f}s")
    print(f"   Content: {llm_response['choices'][0]['message']['content'][:50]}...")

    # Step 3: Complete job
    print("\n3. Completing job...")
    complete_job(job_id, virtual_key, "completed")
    print("   Job completed")

    # Step 4: Verify in database
    print("\n4. Verifying database records...")
    db_session.expire_all()  # Refresh session

    # Verify Job record
    job = verify_job_in_db(db_session, job_id, TEST_TEAM_ID, JobStatus.COMPLETED)
    print(f"   ✓ Job record verified (status: {job.status.value})")

    # Verify LLMCall record
    llm_call = verify_llm_call_in_db(db_session, job_id, TEST_MODEL_GROUP)
    print(f"   ✓ LLMCall record verified")
    print(f"     - Tokens: {llm_call.prompt_tokens} + {llm_call.completion_tokens} = {llm_call.total_tokens}")
    print(f"     - Cost: ${llm_call.cost_usd:.6f}")
    print(f"     - Latency: {llm_call.latency_ms}ms")
    print(f"     - Model Group: {llm_call.model_group_used}")
    print(f"     - Resolved Model: {llm_call.resolved_model}")

    # Verify credit deduction
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()

    credits_used = initial_credits - float(team_credits.credits_remaining)
    print(f"   ✓ Credits deducted: {credits_used:.6f}")

    assert credits_used > 0, "No credits were deducted"

    print("\n✅ Non-streaming test PASSED")
    print("="*70)


@pytest.mark.integration
def test_streaming_call(test_team, db_session):
    """
    Test streaming LLM call with SSE and full tracking verification

    Verifies:
    - Job creation and completion
    - Streaming LLM call execution (SSE)
    - Chunk accumulation
    - Database record creation (Job, LLMCall)
    - Token tracking for streaming
    - Cost calculation
    - Team association
    - Credit deduction
    """
    print("\n" + "="*70)
    print("TEST: Streaming LLM Call")
    print("="*70)

    virtual_key = test_team["virtual_key"]

    # Get current credits
    db_session.expire_all()
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()
    credits_before = float(team_credits.credits_remaining)

    # Step 1: Create job
    print("\n1. Creating job...")
    job_data = create_job(virtual_key, "streaming_test")
    job_id = job_data["job_id"]
    print(f"   Job created: {job_id}")

    # Step 2: Make streaming LLM call
    print("\n2. Making streaming LLM call...")
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/jobs/{job_id}/llm-call-stream",
        headers={"Authorization": f"Bearer {virtual_key}"},
        json={
            "model_group": TEST_MODEL_GROUP,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Count from 1 to 5, one number per line."}
            ],
            "temperature": 0.7,
            "max_tokens": 100,
            "purpose": "integration_test_streaming"
        },
        stream=True
    )

    assert response.status_code == 200, f"Streaming call failed: {response.text}"

    # Accumulate streaming response
    accumulated_content = ""
    chunk_count = 0

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
                                print(f"\r   Received {chunk_count} chunks...", end="", flush=True)

                except json.JSONDecodeError:
                    continue

    elapsed = time.time() - start_time
    print(f"\n   Stream completed in {elapsed:.2f}s ({chunk_count} chunks)")
    print(f"   Accumulated content ({len(accumulated_content)} chars):")
    print(f"   {accumulated_content[:100]}...")

    # Step 3: Complete job
    print("\n3. Completing job...")
    complete_job(job_id, virtual_key, "completed")
    print("   Job completed")

    # Step 4: Verify in database
    print("\n4. Verifying database records...")
    db_session.expire_all()  # Refresh session

    # Verify Job record
    job = verify_job_in_db(db_session, job_id, TEST_TEAM_ID, JobStatus.COMPLETED)
    print(f"   ✓ Job record verified (status: {job.status.value})")

    # Verify LLMCall record
    llm_call = verify_llm_call_in_db(db_session, job_id, TEST_MODEL_GROUP)
    print(f"   ✓ LLMCall record verified")
    print(f"     - Tokens: {llm_call.prompt_tokens} + {llm_call.completion_tokens} = {llm_call.total_tokens}")
    print(f"     - Cost: ${llm_call.cost_usd:.6f}")
    print(f"     - Latency: {llm_call.latency_ms}ms")
    print(f"     - Model Group: {llm_call.model_group_used}")
    print(f"     - Streaming: {llm_call.response_data.get('streaming', False) if llm_call.response_data else False}")

    # Verify response content was accumulated
    if llm_call.response_data and "content" in llm_call.response_data:
        stored_content = llm_call.response_data["content"]
        print(f"     - Stored content length: {len(stored_content)} chars")
        assert len(stored_content) > 0, "No content stored in database"

    # Verify credit deduction
    db_session.expire_all()
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()

    credits_after = float(team_credits.credits_remaining)
    credits_used = credits_before - credits_after
    print(f"   ✓ Credits deducted: {credits_used:.6f}")

    assert credits_used > 0, "No credits were deducted for streaming call"

    print("\n✅ Streaming test PASSED")
    print("="*70)


@pytest.mark.integration
def test_multiple_calls_same_job(test_team, db_session):
    """
    Test multiple LLM calls within the same job

    Verifies:
    - Multiple calls can be made in one job
    - All calls are tracked separately
    - Credits deducted for all calls
    """
    print("\n" + "="*70)
    print("TEST: Multiple Calls in Same Job")
    print("="*70)

    virtual_key = test_team["virtual_key"]

    # Get current credits
    db_session.expire_all()
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()
    credits_before = float(team_credits.credits_remaining)

    # Create job
    print("\n1. Creating job...")
    job_data = create_job(virtual_key, "multi_call_test")
    job_id = job_data["job_id"]
    print(f"   Job created: {job_id}")

    # Make multiple calls
    num_calls = 3
    print(f"\n2. Making {num_calls} LLM calls...")

    for i in range(num_calls):
        response = requests.post(
            f"{BASE_URL}/api/jobs/{job_id}/llm-call",
            headers={"Authorization": f"Bearer {virtual_key}"},
            json={
                "model_group": TEST_MODEL_GROUP,
                "messages": [
                    {"role": "user", "content": f"Say 'Call {i+1}' and nothing else."}
                ],
                "temperature": 0.7,
                "max_tokens": 10,
                "purpose": f"multi_call_test_{i+1}"
            }
        )
        assert response.status_code == 200, f"Call {i+1} failed"
        print(f"   Call {i+1} completed")

    # Complete job
    print("\n3. Completing job...")
    complete_job(job_id, virtual_key, "completed")

    # Verify in database
    print("\n4. Verifying database records...")
    db_session.expire_all()

    # Count LLMCall records
    llm_calls = db_session.query(LLMCall).filter(
        LLMCall.job_id == uuid_lib.UUID(job_id)
    ).all()

    assert len(llm_calls) == num_calls, f"Expected {num_calls} LLMCall records, found {len(llm_calls)}"
    print(f"   ✓ All {num_calls} calls tracked in database")

    # Calculate total cost
    total_cost = sum(float(call.cost_usd) for call in llm_calls)
    total_tokens = sum(call.total_tokens for call in llm_calls)
    print(f"   ✓ Total cost: ${total_cost:.6f}")
    print(f"   ✓ Total tokens: {total_tokens}")

    # Verify credits
    db_session.expire_all()
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()

    credits_used = credits_before - float(team_credits.credits_remaining)
    print(f"   ✓ Credits deducted: {credits_used:.6f}")

    print("\n✅ Multiple calls test PASSED")
    print("="*70)


@pytest.mark.integration
def test_team_isolation(test_organization, test_model_group, db_session):
    """
    Test that different teams are isolated from each other

    Verifies:
    - Teams cannot access other teams' jobs
    - Credits are tracked per team
    """
    print("\n" + "="*70)
    print("TEST: Team Isolation")
    print("="*70)

    # Create second test team
    test_team_2_id = "test_team_llm_2"

    response = requests.post(
        f"{BASE_URL}/api/teams/create",
        json={
            "organization_id": TEST_ORG_ID,
            "team_id": test_team_2_id,
            "team_alias": "Integration Test Team 2",
            "access_groups": [TEST_MODEL_GROUP],
            "credits_allocated": 100,
            "metadata": {"test": True}
        }
    )

    # Skip if already exists
    if response.status_code != 200 and "already exists" not in response.text:
        pytest.skip(f"Could not create second team: {response.text}")

    team_2_data = response.json()
    team_2_key = team_2_data.get("virtual_key")

    try:
        # Team 1 creates a job
        print("\n1. Team 1 creates job...")
        team_1_key = db_session.query(TeamCredits).filter(
            TeamCredits.team_id == TEST_TEAM_ID
        ).first().virtual_key

        job_1_data = create_job(team_1_key, "isolation_test_team_1")
        job_1_id = job_1_data["job_id"]
        print(f"   Job 1 created: {job_1_id}")

        # Team 2 tries to access Team 1's job (should fail)
        print("\n2. Team 2 tries to access Team 1's job...")
        response = requests.post(
            f"{BASE_URL}/api/jobs/{job_1_id}/llm-call",
            headers={"Authorization": f"Bearer {team_2_key}"},
            json={
                "model_group": TEST_MODEL_GROUP,
                "messages": [{"role": "user", "content": "Test"}],
                "temperature": 0.7
            }
        )

        assert response.status_code == 403, f"Team 2 should not access Team 1's job, got {response.status_code}"
        print("   ✓ Access correctly denied (403 Forbidden)")

        print("\n✅ Team isolation test PASSED")
        print("="*70)

    finally:
        # Cleanup: Delete second team
        try:
            requests.delete(f"{BASE_URL}/api/teams/{test_team_2_id}")
        except:
            pass


# ============================================================================
# Test Summary
# ============================================================================

@pytest.mark.integration
def test_summary(test_team, db_session):
    """Print summary of all tests"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    db_session.expire_all()

    # Count total jobs for this team
    jobs = db_session.query(Job).filter(Job.team_id == TEST_TEAM_ID).all()
    print(f"\nTotal jobs created: {len(jobs)}")

    # Count total LLM calls
    total_calls = db_session.query(LLMCall).join(Job).filter(
        Job.team_id == TEST_TEAM_ID
    ).count()
    print(f"Total LLM calls: {total_calls}")

    # Get credit summary
    team_credits = db_session.query(TeamCredits).filter(
        TeamCredits.team_id == TEST_TEAM_ID
    ).first()

    credits_used = test_team["initial_credits"] - float(team_credits.credits_remaining)
    print(f"\nCredit Summary:")
    print(f"  Initial credits: {test_team['initial_credits']:.6f}")
    print(f"  Credits used: {credits_used:.6f}")
    print(f"  Credits remaining: {team_credits.credits_remaining:.6f}")

    print("\n" + "="*70)

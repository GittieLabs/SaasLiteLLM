# Full Chain Example

Complete end-to-end workflow demonstrating the full SaaS LiteLLM platform lifecycle.

## Overview

This example shows the complete workflow from organization setup to making LLM calls:

1. Create organization
2. Create model groups
3. Create team with credits
4. Create job
5. Make LLM calls
6. Complete job
7. Track credits

## Prerequisites

- SaaS API running on `http://localhost:8003`
- LiteLLM Backend running on `http://localhost:8002`
- LiteLLM configured with at least one model (e.g., `gpt-3.5-turbo`)

## Python Example

### Complete Workflow

```python
import requests
import json
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8003/api"
ADMIN_KEY = "sk-admin-key-change-me"  # For org/team creation

class SaaSLiteLLMClient:
    """Complete client for SaaS LiteLLM platform"""

    def __init__(self, api_url: str = "http://localhost:8003/api"):
        self.api_url = api_url
        self.admin_headers = {
            "Authorization": f"Bearer {ADMIN_KEY}",
            "Content-Type": "application/json"
        }
        self.team_headers = None
        self.team_id = None
        self.virtual_key = None

    # ========================================================================
    # Step 1: Organization Management
    # ========================================================================

    def create_organization(self, org_id: str, name: str, metadata: Dict = None) -> Dict[str, Any]:
        """Create a new organization"""
        response = requests.post(
            f"{self.api_url}/organizations/create",
            headers=self.admin_headers,
            json={
                "organization_id": org_id,
                "name": name,
                "metadata": metadata or {}
            }
        )

        if response.status_code == 400 and "already exists" in response.text:
            print(f"Organization {org_id} already exists, fetching details...")
            return self.get_organization(org_id)

        response.raise_for_status()
        return response.json()

    def get_organization(self, org_id: str) -> Dict[str, Any]:
        """Get organization details"""
        response = requests.get(
            f"{self.api_url}/organizations/{org_id}",
            headers=self.admin_headers
        )
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Step 2: Model Group Management
    # ========================================================================

    def create_model_group(
        self,
        group_name: str,
        display_name: str,
        description: str,
        models: list
    ) -> Dict[str, Any]:
        """Create a model group with prioritized models"""
        response = requests.post(
            f"{self.api_url}/model-groups/create",
            headers=self.admin_headers,
            json={
                "group_name": group_name,
                "display_name": display_name,
                "description": description,
                "models": models
            }
        )

        if response.status_code == 400 and "already exists" in response.text:
            print(f"Model group {group_name} already exists")
            return self.get_model_group(group_name)

        response.raise_for_status()
        return response.json()

    def get_model_group(self, group_name: str) -> Dict[str, Any]:
        """Get model group details"""
        response = requests.get(
            f"{self.api_url}/model-groups/{group_name}",
            headers=self.admin_headers
        )
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Step 3: Team Management
    # ========================================================================

    def create_team(
        self,
        organization_id: str,
        team_id: str,
        team_alias: str,
        model_groups: list,
        credits_allocated: int
    ) -> Dict[str, Any]:
        """Create team with LiteLLM integration and credits"""
        response = requests.post(
            f"{self.api_url}/teams/create",
            headers=self.admin_headers,
            json={
                "organization_id": organization_id,
                "team_id": team_id,
                "team_alias": team_alias,
                "model_groups": model_groups,
                "credits_allocated": credits_allocated
            }
        )

        if response.status_code == 400 and "already exists" in response.text:
            print(f"Team {team_id} already exists, fetching details...")
            return self.get_team(team_id)

        response.raise_for_status()
        result = response.json()

        # Store virtual key for future requests
        self.virtual_key = result.get("virtual_key")
        self.team_id = team_id
        self.team_headers = {
            "Authorization": f"Bearer {self.virtual_key}",
            "Content-Type": "application/json"
        }

        return result

    def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get team details"""
        response = requests.get(
            f"{self.api_url}/teams/{team_id}",
            headers=self.admin_headers
        )
        response.raise_for_status()
        return response.json()

    def set_virtual_key(self, virtual_key: str, team_id: str):
        """Set virtual key for team operations"""
        self.virtual_key = virtual_key
        self.team_id = team_id
        self.team_headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json"
        }

    # ========================================================================
    # Step 4: Credit Management
    # ========================================================================

    def get_credit_balance(self) -> Dict[str, Any]:
        """Get credit balance for authenticated team"""
        if not self.team_headers:
            raise ValueError("No team authenticated. Call create_team or set_virtual_key first.")

        response = requests.get(
            f"{self.api_url}/credits/teams/{self.team_id}/balance",
            headers=self.team_headers
        )
        response.raise_for_status()
        return response.json()

    def add_credits(self, credits: int, reason: str = "Manual allocation") -> Dict[str, Any]:
        """Add credits to team"""
        if not self.team_headers:
            raise ValueError("No team authenticated")

        response = requests.post(
            f"{self.api_url}/credits/teams/{self.team_id}/add",
            headers=self.team_headers,
            json={
                "credits": credits,
                "reason": reason
            }
        )
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Step 5: Job & LLM Call Workflow
    # ========================================================================

    def create_job(self, job_type: str, metadata: Dict = None) -> str:
        """Create a new job"""
        if not self.team_headers:
            raise ValueError("No team authenticated")

        response = requests.post(
            f"{self.api_url}/jobs/create",
            headers=self.team_headers,
            json={
                "team_id": self.team_id,
                "job_type": job_type,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["job_id"]

    def make_llm_call(
        self,
        job_id: str,
        model_group: str,
        messages: list,
        purpose: str = None,
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """Make an LLM call within a job"""
        if not self.team_headers:
            raise ValueError("No team authenticated")

        payload = {
            "model_group": model_group,
            "messages": messages,
            "temperature": temperature
        }

        if purpose:
            payload["purpose"] = purpose
        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = requests.post(
            f"{self.api_url}/jobs/{job_id}/llm-call",
            headers=self.team_headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def complete_job(
        self,
        job_id: str,
        status: str = "completed",
        error_message: str = None
    ) -> Dict[str, Any]:
        """Complete a job and get cost summary"""
        if not self.team_headers:
            raise ValueError("No team authenticated")

        payload = {"status": status}
        if error_message:
            payload["error_message"] = error_message

        response = requests.post(
            f"{self.api_url}/jobs/{job_id}/complete",
            headers=self.team_headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job details"""
        if not self.team_headers:
            raise ValueError("No team authenticated")

        response = requests.get(
            f"{self.api_url}/jobs/{job_id}",
            headers=self.team_headers
        )
        response.raise_for_status()
        return response.json()


# ============================================================================
# Complete End-to-End Example
# ============================================================================

def full_workflow_example():
    """
    Complete workflow:
    1. Create organization
    2. Create model groups
    3. Create team
    4. Create job
    5. Make LLM calls
    6. Complete job
    7. Check credits
    """

    client = SaaSLiteLLMClient()

    print("="*70)
    print("SAAS LITELLM - FULL WORKFLOW EXAMPLE")
    print("="*70)

    # Step 1: Create Organization
    print("\n[1/7] Creating Organization...")
    org = client.create_organization(
        org_id="acme-corp",
        name="Acme Corporation",
        metadata={"industry": "technology", "tier": "enterprise"}
    )
    print(f"✓ Organization created: {org['organization_id']}")

    # Step 2: Create Model Groups
    print("\n[2/7] Creating Model Groups...")

    # Fast model group for quick tasks
    fast_group = client.create_model_group(
        group_name="ChatFast",
        display_name="Fast Chat Model",
        description="Quick responses for simple queries",
        models=[
            {"model_name": "gpt-3.5-turbo", "priority": 0},
            {"model_name": "gpt-4o-mini", "priority": 1}
        ]
    )
    print(f"✓ Model group created: {fast_group['group_name']}")

    # Advanced model group for complex tasks
    advanced_group = client.create_model_group(
        group_name="ChatAdvanced",
        display_name="Advanced Chat Model",
        description="Powerful model for complex reasoning",
        models=[
            {"model_name": "gpt-4", "priority": 0},
            {"model_name": "gpt-4-turbo", "priority": 1}
        ]
    )
    print(f"✓ Model group created: {advanced_group['group_name']}")

    # Step 3: Create Team
    print("\n[3/7] Creating Team with Credits...")
    team = client.create_team(
        organization_id="acme-corp",
        team_id="engineering-team",
        team_alias="Engineering Team",
        model_groups=["ChatFast", "ChatAdvanced"],
        credits_allocated=100
    )
    print(f"✓ Team created: {team['team_id']}")
    print(f"  Virtual Key: {team['virtual_key'][:50]}...")
    print(f"  Credits: {team['credits_allocated']}")
    print(f"  Model Groups: {', '.join(team['model_groups'])}")

    # Step 4: Check Initial Credits
    print("\n[4/7] Checking Initial Credit Balance...")
    credits = client.get_credit_balance()
    print(f"✓ Credits available: {credits['credits_remaining']}/{credits['credits_allocated']}")

    # Step 5: Create Job
    print("\n[5/7] Creating Job...")
    job_id = client.create_job(
        job_type="customer_support",
        metadata={
            "customer_id": "customer_12345",
            "priority": "high"
        }
    )
    print(f"✓ Job created: {job_id}")

    # Step 6: Make LLM Calls
    print("\n[6/7] Making LLM Calls...")

    # First call - initial response
    print("  → Call 1: Initial customer query...")
    response1 = client.make_llm_call(
        job_id=job_id,
        model_group="ChatFast",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful customer support assistant."
            },
            {
                "role": "user",
                "content": "How do I reset my password?"
            }
        ],
        purpose="initial_response"
    )
    print(f"    Response: {response1['response']['content'][:100]}...")
    print(f"    Tokens: {response1['metadata']['tokens_used']}")
    print(f"    Latency: {response1['metadata']['latency_ms']}ms")

    # Second call - follow-up
    print("\n  → Call 2: Follow-up question...")
    response2 = client.make_llm_call(
        job_id=job_id,
        model_group="ChatFast",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful customer support assistant."
            },
            {
                "role": "user",
                "content": "How do I reset my password?"
            },
            {
                "role": "assistant",
                "content": response1['response']['content']
            },
            {
                "role": "user",
                "content": "I didn't receive the reset email."
            }
        ],
        purpose="follow_up"
    )
    print(f"    Response: {response2['response']['content'][:100]}...")
    print(f"    Tokens: {response2['metadata']['tokens_used']}")

    # Third call - complex analysis using advanced model
    print("\n  → Call 3: Complex analysis...")
    response3 = client.make_llm_call(
        job_id=job_id,
        model_group="ChatAdvanced",
        messages=[
            {
                "role": "user",
                "content": "Analyze this customer interaction and suggest improvements to our password reset process."
            }
        ],
        purpose="analysis",
        temperature=0.3
    )
    print(f"    Response: {response3['response']['content'][:100]}...")
    print(f"    Tokens: {response3['metadata']['tokens_used']}")

    # Step 7: Complete Job
    print("\n[7/7] Completing Job...")
    completion = client.complete_job(
        job_id=job_id,
        status="completed"
    )

    print(f"✓ Job completed: {completion['job_id']}")
    print(f"\n  Cost Summary:")
    print(f"    Total calls: {completion['costs']['total_calls']}")
    print(f"    Successful: {completion['costs']['successful_calls']}")
    print(f"    Failed: {completion['costs']['failed_calls']}")
    print(f"    Total tokens: {completion['costs']['total_tokens']}")
    print(f"    Total cost: ${completion['costs']['total_cost_usd']:.6f}")
    print(f"    Avg latency: {completion['costs']['avg_latency_ms']}ms")
    print(f"    Credit applied: {completion['costs']['credit_applied']}")
    print(f"    Credits remaining: {completion['costs']['credits_remaining']}")

    # Final credit check
    print("\n[FINAL] Credit Balance After Job...")
    final_credits = client.get_credit_balance()
    print(f"✓ Credits: {final_credits['credits_remaining']}/{final_credits['credits_allocated']}")
    print(f"  Credits used: {final_credits['credits_used']}")

    print("\n" + "="*70)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*70)

    return {
        "organization": org,
        "team": team,
        "job_id": job_id,
        "completion": completion
    }


if __name__ == "__main__":
    try:
        result = full_workflow_example()
        print("\n✅ All steps completed successfully!")
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: Could not connect to API")
        print("Make sure SaaS API is running: http://localhost:8003")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
```

## JavaScript/Node.js Example

```javascript
const axios = require('axios');

class SaaSLiteLLMClient {
    constructor(apiUrl = 'http://localhost:8003/api') {
        this.apiUrl = apiUrl;
        this.adminKey = 'sk-admin-key-change-me';
        this.virtualKey = null;
        this.teamId = null;
    }

    // Create Organization
    async createOrganization(orgId, name, metadata = {}) {
        try {
            const response = await axios.post(
                `${this.apiUrl}/organizations/create`,
                {
                    organization_id: orgId,
                    name: name,
                    metadata: metadata
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.adminKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            return response.data;
        } catch (error) {
            if (error.response?.status === 400 && error.response.data.detail?.includes('already exists')) {
                return await this.getOrganization(orgId);
            }
            throw error;
        }
    }

    // Create Model Group
    async createModelGroup(groupName, displayName, description, models) {
        try {
            const response = await axios.post(
                `${this.apiUrl}/model-groups/create`,
                {
                    group_name: groupName,
                    display_name: displayName,
                    description: description,
                    models: models
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.adminKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            return response.data;
        } catch (error) {
            if (error.response?.status === 400) {
                return await this.getModelGroup(groupName);
            }
            throw error;
        }
    }

    // Create Team
    async createTeam(organizationId, teamId, teamAlias, modelGroups, creditsAllocated) {
        const response = await axios.post(
            `${this.apiUrl}/teams/create`,
            {
                organization_id: organizationId,
                team_id: teamId,
                team_alias: teamAlias,
                model_groups: modelGroups,
                credits_allocated: creditsAllocated
            },
            {
                headers: {
                    'Authorization': `Bearer ${this.adminKey}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        this.virtualKey = response.data.virtual_key;
        this.teamId = teamId;
        return response.data;
    }

    // Get team headers
    getTeamHeaders() {
        if (!this.virtualKey) {
            throw new Error('No team authenticated');
        }
        return {
            'Authorization': `Bearer ${this.virtualKey}`,
            'Content-Type': 'application/json'
        };
    }

    // Create Job
    async createJob(jobType, metadata = {}) {
        const response = await axios.post(
            `${this.apiUrl}/jobs/create`,
            {
                team_id: this.teamId,
                job_type: jobType,
                metadata: metadata
            },
            { headers: this.getTeamHeaders() }
        );
        return response.data.job_id;
    }

    // Make LLM Call
    async makeLLMCall(jobId, modelGroup, messages, options = {}) {
        const response = await axios.post(
            `${this.apiUrl}/jobs/${jobId}/llm-call`,
            {
                model_group: modelGroup,
                messages: messages,
                temperature: options.temperature || 0.7,
                purpose: options.purpose,
                max_tokens: options.maxTokens
            },
            { headers: this.getTeamHeaders() }
        );
        return response.data;
    }

    // Complete Job
    async completeJob(jobId, status = 'completed', errorMessage = null) {
        const response = await axios.post(
            `${this.apiUrl}/jobs/${jobId}/complete`,
            {
                status: status,
                error_message: errorMessage
            },
            { headers: this.getTeamHeaders() }
        );
        return response.data;
    }

    // Get Credit Balance
    async getCreditBalance() {
        const response = await axios.get(
            `${this.apiUrl}/credits/teams/${this.teamId}/balance`,
            { headers: this.getTeamHeaders() }
        );
        return response.data;
    }
}

// Full workflow example
async function fullWorkflowExample() {
    const client = new SaaSLiteLLMClient();

    console.log('='.repeat(70));
    console.log('SAAS LITELLM - FULL WORKFLOW EXAMPLE (JavaScript)');
    console.log('='.repeat(70));

    try {
        // 1. Create Organization
        console.log('\n[1/6] Creating Organization...');
        const org = await client.createOrganization(
            'acme-corp-js',
            'Acme Corporation (JS)',
            { industry: 'technology' }
        );
        console.log(`✓ Organization: ${org.organization_id}`);

        // 2. Create Model Group
        console.log('\n[2/6] Creating Model Group...');
        const modelGroup = await client.createModelGroup(
            'ChatFastJS',
            'Fast Chat (JS)',
            'Quick responses',
            [
                { model_name: 'gpt-3.5-turbo', priority: 0 },
                { model_name: 'gpt-4o-mini', priority: 1 }
            ]
        );
        console.log(`✓ Model Group: ${modelGroup.group_name}`);

        // 3. Create Team
        console.log('\n[3/6] Creating Team...');
        const team = await client.createTeam(
            'acme-corp-js',
            'js-team',
            'JavaScript Team',
            ['ChatFastJS'],
            50
        );
        console.log(`✓ Team: ${team.team_id}`);
        console.log(`  Credits: ${team.credits_allocated}`);

        // 4. Create Job
        console.log('\n[4/6] Creating Job...');
        const jobId = await client.createJob('demo', { example: 'javascript' });
        console.log(`✓ Job: ${jobId}`);

        // 5. Make LLM Call
        console.log('\n[5/6] Making LLM Call...');
        const response = await client.makeLLMCall(
            jobId,
            'ChatFastJS',
            [
                { role: 'user', content: 'What is Node.js?' }
            ],
            { purpose: 'demo' }
        );
        console.log(`✓ Response: ${response.response.content.substring(0, 100)}...`);
        console.log(`  Tokens: ${response.metadata.tokens_used}`);

        // 6. Complete Job
        console.log('\n[6/6] Completing Job...');
        const completion = await client.completeJob(jobId);
        console.log(`✓ Job completed`);
        console.log(`  Total calls: ${completion.costs.total_calls}`);
        console.log(`  Credits remaining: ${completion.costs.credits_remaining}`);

        console.log('\n' + '='.repeat(70));
        console.log('WORKFLOW COMPLETED SUCCESSFULLY!');
        console.log('='.repeat(70));

    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

// Run the example
fullWorkflowExample();
```

## cURL Example

```bash
#!/bin/bash

# Configuration
API_URL="http://localhost:8003/api"
ADMIN_KEY="sk-admin-key-change-me"

echo "======================================================================"
echo "SAAS LITELLM - FULL WORKFLOW EXAMPLE (cURL)"
echo "======================================================================"

# 1. Create Organization
echo -e "\n[1/6] Creating Organization..."
ORG_RESPONSE=$(curl -s -X POST "${API_URL}/organizations/create" \
  -H "Authorization: Bearer ${ADMIN_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "acme-corp-curl",
    "name": "Acme Corporation (cURL)",
    "metadata": {"industry": "technology"}
  }')
echo "✓ Organization created"

# 2. Create Model Group
echo -e "\n[2/6] Creating Model Group..."
curl -s -X POST "${API_URL}/model-groups/create" \
  -H "Authorization: Bearer ${ADMIN_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "ChatFastCurl",
    "display_name": "Fast Chat (cURL)",
    "description": "Quick responses",
    "models": [
      {"model_name": "gpt-3.5-turbo", "priority": 0}
    ]
  }' > /dev/null
echo "✓ Model Group: ChatFastCurl"

# 3. Create Team
echo -e "\n[3/6] Creating Team..."
TEAM_RESPONSE=$(curl -s -X POST "${API_URL}/teams/create" \
  -H "Authorization: Bearer ${ADMIN_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "acme-corp-curl",
    "team_id": "curl-team",
    "team_alias": "cURL Team",
    "model_groups": ["ChatFastCurl"],
    "credits_allocated": 50
  }')

VIRTUAL_KEY=$(echo $TEAM_RESPONSE | jq -r '.virtual_key')
echo "✓ Team created"
echo "  Virtual Key: ${VIRTUAL_KEY:0:50}..."

# 4. Create Job
echo -e "\n[4/6] Creating Job..."
JOB_RESPONSE=$(curl -s -X POST "${API_URL}/jobs/create" \
  -H "Authorization: Bearer ${VIRTUAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "curl-team",
    "job_type": "demo",
    "metadata": {"example": "curl"}
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "✓ Job: $JOB_ID"

# 5. Make LLM Call
echo -e "\n[5/6] Making LLM Call..."
LLM_RESPONSE=$(curl -s -X POST "${API_URL}/jobs/${JOB_ID}/llm-call" \
  -H "Authorization: Bearer ${VIRTUAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_group": "ChatFastCurl",
    "messages": [
      {"role": "user", "content": "What is cURL?"}
    ],
    "purpose": "demo"
  }')

TOKENS=$(echo $LLM_RESPONSE | jq -r '.metadata.tokens_used')
echo "✓ LLM Call completed"
echo "  Tokens: $TOKENS"

# 6. Complete Job
echo -e "\n[6/6] Completing Job..."
COMPLETE_RESPONSE=$(curl -s -X POST "${API_URL}/jobs/${JOB_ID}/complete" \
  -H "Authorization: Bearer ${VIRTUAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }')

CREDITS_REMAINING=$(echo $COMPLETE_RESPONSE | jq -r '.costs.credits_remaining')
echo "✓ Job completed"
echo "  Credits remaining: $CREDITS_REMAINING"

echo -e "\n======================================================================"
echo "WORKFLOW COMPLETED SUCCESSFULLY!"
echo "======================================================================"
```

## Expected Output

```
======================================================================
SAAS LITELLM - FULL WORKFLOW EXAMPLE
======================================================================

[1/7] Creating Organization...
✓ Organization created: acme-corp

[2/7] Creating Model Groups...
✓ Model group created: ChatFast
✓ Model group created: ChatAdvanced

[3/7] Creating Team with Credits...
✓ Team created: engineering-team
  Virtual Key: sk-b6f4a8c2d1e9f3a7b8c4d2e1f9a8b7c6d5e4f3a2b1c...
  Credits: 100
  Model Groups: ChatFast, ChatAdvanced

[4/7] Checking Initial Credit Balance...
✓ Credits available: 100/100

[5/7] Creating Job...
✓ Job created: 550e8400-e29b-41d4-a716-446655440000

[6/7] Making LLM Calls...
  → Call 1: Initial customer query...
    Response: To reset your password, please click on the "Forgot Password" link on the login page...
    Tokens: 156
    Latency: 842ms

  → Call 2: Follow-up question...
    Response: If you didn't receive the reset email, please check your spam folder...
    Tokens: 134

  → Call 3: Complex analysis...
    Response: Based on this interaction, I suggest the following improvements to your password reset...
    Tokens: 287

[7/7] Completing Job...
✓ Job completed: 550e8400-e29b-41d4-a716-446655440000

  Cost Summary:
    Total calls: 3
    Successful: 3
    Failed: 0
    Total tokens: 577
    Total cost: $0.000867
    Avg latency: 783ms
    Credit applied: True
    Credits remaining: 99

[FINAL] Credit Balance After Job...
✓ Credits: 99/100
  Credits used: 1

======================================================================
WORKFLOW COMPLETED SUCCESSFULLY!
======================================================================

✅ All steps completed successfully!
```

## Key Concepts Demonstrated

### 1. Organization Hierarchy
- Organizations contain teams
- Teams have model groups and credits
- Isolation between organizations

### 2. Model Groups
- Abstract model selection from clients
- Support fallback models
- Centralized model management

### 3. Credit System
- Pre-allocated credits per team
- 1 credit per successfully completed job
- Failed jobs don't consume credits

### 4. Job-Based Tracking
- Jobs group related LLM calls
- Track costs per business operation
- Associate metadata with jobs

### 5. Authentication
- Admin key for setup operations
- Virtual keys for team operations
- Team isolation enforced

## Next Steps

1. **[Agent Integration](agent-integration.md)** - Use with AI agent frameworks
2. **[Streaming Examples](streaming-examples.md)** - Real-time streaming responses
3. **[Structured Outputs](structured-outputs.md)** - Type-safe structured data
4. **[Error Handling](../integration/error-handling.md)** - Production error handling
5. **[Best Practices](../integration/best-practices.md)** - Production deployment guide

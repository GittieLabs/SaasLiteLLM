# SaaS API Usage Examples

## Quick Start

### 1. Start Both Services

```bash
# Terminal 1: Start LiteLLM (backend)
source .venv/bin/activate
python scripts/start_local.py

# Terminal 2: Initialize job tracking database
python scripts/init_job_tracking_db.py

# Terminal 3: Start SaaS API (frontend for teams)
python scripts/start_saas_api.py
```

**Services:**
- LiteLLM Backend: `http://localhost:8000` (internal only)
- SaaS API: `http://localhost:8001` (exposed to teams)
- SaaS API Docs: `http://localhost:8001/docs`

---

## Example 1: Document Analysis Job

Your SaaS app processes a 5-page document by making multiple LLM calls:

```python
import requests

API_BASE = "http://localhost:8001/api"

# 1. Create a job
response = requests.post(f"{API_BASE}/jobs/create", json={
    "team_id": "acme-corp",
    "user_id": "john@acme.com",
    "job_type": "document_analysis",
    "metadata": {
        "document_id": "doc_12345",
        "filename": "contract.pdf",
        "pages": 5
    }
})

job = response.json()
job_id = job["job_id"]
print(f"Created job: {job_id}")

# 2. Analyze each page
for page_num in range(1, 6):
    response = requests.post(
        f"{API_BASE}/jobs/{job_id}/llm-call",
        json={
            "messages": [
                {
                    "role": "system",
                    "content": "You are a legal document analyzer."
                },
                {
                    "role": "user",
                    "content": f"Analyze page {page_num}: [page content here]"
                }
            ],
            "purpose": f"page_{page_num}_analysis"
        }
    )

    result = response.json()
    print(f"Page {page_num}: {result['metadata']['tokens_used']} tokens, "
          f"{result['metadata']['latency_ms']}ms")

# 3. Generate summary
response = requests.post(
    f"{API_BASE}/jobs/{job_id}/llm-call",
    json={
        "messages": [
            {
                "role": "user",
                "content": "Summarize all the analyzed pages..."
            }
        ],
        "purpose": "final_summary"
    }
)

# 4. Complete the job and get costs
response = requests.post(
    f"{API_BASE}/jobs/{job_id}/complete",
    json={
        "status": "completed",
        "metadata": {
            "output_file": "summary_12345.pdf"
        }
    }
)

result = response.json()
print(f"\nJob completed!")
print(f"Total LLM calls: {result['costs']['total_calls']}")
print(f"Total tokens: {result['costs']['total_tokens']}")
print(f"Avg latency: {result['costs']['avg_latency_ms']}ms")
print(f"ACTUAL COST: ${result['costs']['total_cost_usd']}")

# Your pricing to customer (markup)
customer_price = 0.50  # Flat $0.50 per document analysis
your_profit = customer_price - result['costs']['total_cost_usd']
print(f"Customer price: ${customer_price}")
print(f"Your profit: ${your_profit}")
```

**Expected Output:**
```
Created job: 789abc-def-1234-5678
Page 1: 1250 tokens, 850ms
Page 2: 1180 tokens, 820ms
Page 3: 1320 tokens, 890ms
Page 4: 1200 tokens, 840ms
Page 5: 1150 tokens, 860ms

Job completed!
Total LLM calls: 6
Total tokens: 7650
Avg latency: 860ms
ACTUAL COST: $0.0234

Customer price: $0.50
Your profit: $0.4766
```

---

## Example 2: Chat Session Job

Track all messages in a multi-turn conversation:

```python
import requests

API_BASE = "http://localhost:8001/api"

# 1. Start chat session
response = requests.post(f"{API_BASE}/jobs/create", json={
    "team_id": "startup-xyz",
    "user_id": "alice@startup.com",
    "job_type": "chat_session",
    "metadata": {
        "session_id": "chat_567",
        "topic": "customer_support"
    }
})

job_id = response.json()["job_id"]

# 2. User asks multiple questions
conversation = [
    {"role": "system", "content": "You are a helpful assistant."}
]

questions = [
    "How do I reset my password?",
    "What are your business hours?",
    "Can I get a refund?"
]

for question in questions:
    conversation.append({"role": "user", "content": question})

    response = requests.post(
        f"{API_BASE}/jobs/{job_id}/llm-call",
        json={
            "messages": conversation,
            "purpose": "chat_turn",
            "temperature": 0.7
        }
    )

    result = response.json()
    answer = result["response"]["content"]
    conversation.append({"role": "assistant", "content": answer})

    print(f"Q: {question}")
    print(f"A: {answer}\n")

# 3. End session
response = requests.post(
    f"{API_BASE}/jobs/{job_id}/complete",
    json={"status": "completed"}
)

costs = response.json()["costs"]
print(f"Chat session cost: ${costs['total_cost_usd']}")
```

---

## Example 3: Failed Job Handling

```python
import requests

API_BASE = "http://localhost:8001/api"

# Create job
response = requests.post(f"{API_BASE}/jobs/create", json={
    "team_id": "beta-testing",
    "user_id": "test@example.com",
    "job_type": "data_extraction"
})

job_id = response.json()["job_id"]

try:
    # Attempt LLM call
    response = requests.post(
        f"{API_BASE}/jobs/{job_id}/llm-call",
        json={
            "messages": [{"role": "user", "content": "Extract data..."}]
        }
    )
    response.raise_for_status()

except Exception as e:
    # Mark job as failed
    requests.post(
        f"{API_BASE}/jobs/{job_id}/complete",
        json={
            "status": "failed",
            "error_message": str(e),
            "metadata": {"failed_at_step": "extraction"}
        }
    )
    print(f"Job failed: {e}")
```

---

## Example 4: Get Team Usage (Internal Admin)

```python
import requests

API_BASE = "http://localhost:8001/api"

# Get team usage for October 2024
response = requests.get(
    f"{API_BASE}/teams/acme-corp/usage",
    params={"period": "2024-10"}
)

usage = response.json()
print(f"Team: {usage['team_id']}")
print(f"Period: {usage['period']}")
print(f"\nSummary:")
print(f"  Total jobs: {usage['summary']['total_jobs']}")
print(f"  Successful: {usage['summary']['successful_jobs']}")
print(f"  Failed: {usage['summary']['failed_jobs']}")
print(f"  Total cost: ${usage['summary']['total_cost_usd']}")
print(f"  Avg per job: ${usage['summary']['avg_cost_per_job']}")

print(f"\nBy Job Type:")
for job_type, stats in usage['job_types'].items():
    print(f"  {job_type}: {stats['count']} jobs, ${stats['cost_usd']}")
```

**Expected Output:**
```
Team: acme-corp
Period: 2024-10

Summary:
  Total jobs: 250
  Successful: 245
  Failed: 5
  Total cost: $18.75
  Avg per job: $0.075

By Job Type:
  document_analysis: 120 jobs, $12.20
  chat_session: 100 jobs, $5.25
  data_extraction: 30 jobs, $1.30
```

---

## Example 5: Get Detailed Job Costs (Admin Only)

```python
import requests

API_BASE = "http://localhost:8001/api"

# Get internal cost breakdown for a specific job
response = requests.get(f"{API_BASE}/jobs/{job_id}/costs")

data = response.json()
print(f"Job: {data['job_id']}")
print(f"Team: {data['team_id']}")
print(f"Total Cost: ${data['costs']['total_cost_usd']}")

print(f"\nDetailed Breakdown:")
for call in data['costs']['breakdown']:
    print(f"  Call {call['call_id'][:8]}...")
    print(f"    Model: {call['model']}")
    print(f"    Purpose: {call['purpose']}")
    print(f"    Tokens: {call['prompt_tokens']} + {call['completion_tokens']}")
    print(f"    Cost: ${call['cost_usd']}")
```

---

## Curl Examples

### Create Job
```bash
curl -X POST http://localhost:8001/api/jobs/create \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "demo-team",
    "user_id": "user123",
    "job_type": "test_job"
  }'
```

### Make LLM Call
```bash
curl -X POST http://localhost:8001/api/jobs/{JOB_ID}/llm-call \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "purpose": "greeting"
  }'
```

### Complete Job
```bash
curl -X POST http://localhost:8001/api/jobs/{JOB_ID}/complete \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

### Get Team Usage
```bash
curl "http://localhost:8001/api/teams/demo-team/usage?period=2024-10"
```

---

## Integration with Your SaaS App

### Flask Example
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
LITELLM_API = "http://localhost:8001/api"

@app.route('/analyze-document', methods=['POST'])
def analyze_document():
    # Your SaaS endpoint
    document_id = request.json['document_id']
    team_id = request.headers['X-Team-ID']

    # Create LLM job
    job = requests.post(f"{LITELLM_API}/jobs/create", json={
        "team_id": team_id,
        "job_type": "document_analysis",
        "metadata": {"document_id": document_id}
    }).json()

    # Process document...
    # Make LLM calls...
    # Complete job...

    return jsonify({"status": "success", "job_id": job["job_id"]})
```

### FastAPI Example
```python
from fastapi import FastAPI, Header
import httpx

app = FastAPI()
LITELLM_API = "http://localhost:8001/api"

@app.post("/process-text")
async def process_text(text: str, team_id: str = Header(...)):
    async with httpx.AsyncClient() as client:
        # Create job
        job_response = await client.post(
            f"{LITELLM_API}/jobs/create",
            json={"team_id": team_id, "job_type": "text_processing"}
        )
        job_id = job_response.json()["job_id"]

        # Process...
        # Complete...

        return {"job_id": job_id}
```

---

## Pricing Strategies

### Strategy 1: Flat Rate per Job Type
```python
JOB_PRICING = {
    "document_analysis": 0.50,
    "chat_session": 0.10,
    "data_extraction": 0.25
}

def calculate_customer_price(job_type: str, actual_cost: float):
    # Charge flat rate regardless of actual cost
    return JOB_PRICING.get(job_type, actual_cost * 2.0)
```

### Strategy 2: Tiered Pricing
```python
def calculate_customer_price(total_tokens: int):
    if total_tokens < 1000:
        return 0.05
    elif total_tokens < 5000:
        return 0.15
    else:
        return 0.30
```

### Strategy 3: Markup Percentage
```python
def calculate_customer_price(actual_cost: float, markup: float = 1.5):
    # 150% markup (50% profit margin)
    return round(actual_cost * markup, 2)
```

---

## Monitoring & Analytics Queries

### Get Today's Jobs
```python
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%d")
response = requests.get(
    f"{API_BASE}/teams/{team_id}/jobs",
    params={"status": "completed"}
)
```

### Calculate Profit
```python
response = requests.get(f"{API_BASE}/teams/{team_id}/usage?period=2024-10")
actual_cost = response.json()["summary"]["total_cost_usd"]

# Your pricing to customers
customer_revenue = 250 * 0.50  # 250 jobs at $0.50 each

profit = customer_revenue - actual_cost
margin = (profit / customer_revenue) * 100

print(f"Revenue: ${customer_revenue}")
print(f"Costs: ${actual_cost}")
print(f"Profit: ${profit}")
print(f"Margin: {margin:.1f}%")
```

---

## Next Steps

1. **Add Authentication** - Protect your SaaS API with JWT/API keys
2. **Add Webhooks** - Notify your app when jobs complete
3. **Build Dashboard** - Show teams their usage (without costs/models)
4. **Set Up Billing** - Charge teams based on job counts or pricing strategy
5. **Add Rate Limits** - Prevent abuse per team
6. **Monitor Costs** - Set alerts when teams approach budget limits

See [ARCHITECTURE.md](ARCHITECTURE.md) for full design details.

# Basic Usage Examples

Simple, working code examples to get you started with SaaS LiteLLM.

## Prerequisites

Before running these examples:

1. **Services Running**:
   - SaaS API on http://localhost:8003
   - LiteLLM Backend on http://localhost:8002

2. **Team Created**:
   - Organization and team set up
   - Virtual key obtained
   - Credits allocated

3. **Environment Variables**:
   ```bash
   export SAAS_LITELLM_VIRTUAL_KEY="sk-your-virtual-key"
   export SAAS_LITELLM_TEAM_ID="your-team-id"
   ```

## Example 1: Simple LLM Call

The most basic workflow: create job → make LLM call → complete job.

```python
import requests
import os

# Configuration
API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = os.environ.get("SAAS_LITELLM_VIRTUAL_KEY")
TEAM_ID = os.environ.get("SAAS_LITELLM_TEAM_ID")

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

def simple_llm_call():
    """Simple LLM call example"""

    # 1. Create job
    print("Creating job...")
    job_response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={
            "team_id": TEAM_ID,
            "job_type": "simple_query"
        }
    )
    job = job_response.json()
    job_id = job["job_id"]
    print(f"Created job: {job_id}")

    # 2. Make LLM call
    print("\nMaking LLM call...")
    llm_response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={
            "messages": [
                {"role": "user", "content": "What is Python programming?"}
            ]
        }
    )
    llm_result = llm_response.json()
    content = llm_result["response"]["content"]
    print(f"\nResponse:\n{content}")

    # 3. Complete job
    print("\nCompleting job...")
    complete_response = requests.post(
        f"{API_URL}/jobs/{job_id}/complete",
        headers=headers,
        json={"status": "completed"}
    )
    result = complete_response.json()
    print(f"Credits remaining: {result['costs']['credits_remaining']}")

if __name__ == "__main__":
    simple_llm_call()
```

**Expected Output:**
```
Creating job...
Created job: 550e8400-e29b-41d4-a716-446655440000

Making LLM call...

Response:
Python is a high-level, interpreted programming language...

Completing job...
Credits remaining: 95
```

## Example 2: Multi-Turn Conversation

Have a conversation with context:

```python
import requests
import os

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = os.environ["SAAS_LITELLM_VIRTUAL_KEY"]
TEAM_ID = os.environ["SAAS_LITELLM_TEAM_ID"]

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

def multi_turn_conversation():
    """Multi-turn conversation with context"""

    # Create job
    job_response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={"team_id": TEAM_ID, "job_type": "conversation"}
    )
    job_id = job_response.json()["job_id"]

    messages = []

    # Turn 1
    print("User: What is FastAPI?")
    messages.append({"role": "user", "content": "What is FastAPI?"})

    response1 = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages}
    ).json()

    assistant_reply1 = response1["response"]["content"]
    print(f"Assistant: {assistant_reply1}\n")
    messages.append({"role": "assistant", "content": assistant_reply1})

    # Turn 2 - Builds on previous context
    print("User: How is it different from Flask?")
    messages.append({"role": "user", "content": "How is it different from Flask?"})

    response2 = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages}
    ).json()

    assistant_reply2 = response2["response"]["content"]
    print(f"Assistant: {assistant_reply2}\n")

    # Complete job
    result = requests.post(
        f"{API_URL}/jobs/{job_id}/complete",
        headers=headers,
        json={"status": "completed"}
    ).json()

    print(f"Conversation complete. Credits remaining: {result['costs']['credits_remaining']}")

if __name__ == "__main__":
    multi_turn_conversation()
```

## Example 3: Document Analysis

Analyze a document with multiple LLM calls in one job:

```python
import requests
import os

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = os.environ["SAAS_LITELLM_VIRTUAL_KEY"]
TEAM_ID = os.environ["SAAS_LITELLM_TEAM_ID"]

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

def analyze_document(document_text: str):
    """Analyze a document: extract key points, generate summary"""

    # Create job
    job_response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={
            "team_id": TEAM_ID,
            "job_type": "document_analysis",
            "metadata": {"document_length": len(document_text)}
        }
    )
    job_id = job_response.json()["job_id"]
    print(f"Analyzing document (Job ID: {job_id})...\n")

    # Step 1: Extract key points
    print("Extracting key points...")
    key_points_response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={
            "messages": [
                {
                    "role": "system",
                    "content": "Extract key points as bullet points."
                },
                {
                    "role": "user",
                    "content": f"Extract key points from:\n\n{document_text}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
    ).json()

    key_points = key_points_response["response"]["content"]
    print(f"Key Points:\n{key_points}\n")

    # Step 2: Generate summary
    print("Generating summary...")
    summary_response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={
            "messages": [
                {
                    "role": "system",
                    "content": "Create concise summaries."
                },
                {
                    "role": "user",
                    "content": f"Summarize in 2-3 sentences:\n\n{document_text}"
                }
            ],
            "temperature": 0.5,
            "max_tokens": 200
        }
    ).json()

    summary = summary_response["response"]["content"]
    print(f"Summary:\n{summary}\n")

    # Complete job
    result = requests.post(
        f"{API_URL}/jobs/{job_id}/complete",
        headers=headers,
        json={"status": "completed"}
    ).json()

    print(f"Analysis complete!")
    print(f"Total calls: {result['costs']['total_calls']}")
    print(f"Credits remaining: {result['costs']['credits_remaining']}")

    return {
        "key_points": key_points,
        "summary": summary
    }

if __name__ == "__main__":
    document = """
    Artificial intelligence (AI) is transforming industries worldwide.
    Machine learning algorithms can now process vast amounts of data
    and identify patterns that humans might miss. This technology is
    being applied in healthcare for disease diagnosis, in finance for
    fraud detection, and in transportation for autonomous vehicles.
    """

    result = analyze_document(document)
```

## Example 4: Error Handling

Handle errors gracefully:

```python
import requests
import os
import time

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = os.environ["SAAS_LITELLM_VIRTUAL_KEY"]
TEAM_ID = os.environ["SAAS_LITELLM_TEAM_ID"]

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

def llm_call_with_error_handling(prompt: str, max_retries=3):
    """Make LLM call with comprehensive error handling"""

    # Create job
    job_response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={"team_id": TEAM_ID, "job_type": "query"}
    )
    job_id = job_response.json()["job_id"]

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{API_URL}/jobs/{job_id}/llm-call",
                headers=headers,
                json={
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            response.raise_for_status()

            # Success
            result = response.json()
            content = result["response"]["content"]

            # Complete job
            requests.post(
                f"{API_URL}/jobs/{job_id}/complete",
                headers=headers,
                json={"status": "completed"}
            )

            return content

        except requests.exceptions.Timeout:
            print(f"Timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                # Mark job as failed
                requests.post(
                    f"{API_URL}/jobs/{job_id}/complete",
                    headers=headers,
                    json={"status": "failed"}
                )
                raise

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            detail = e.response.json().get("detail", "Unknown error")

            if status_code == 401:
                print("Authentication failed")
                raise

            elif status_code == 403:
                print(f"Access denied: {detail}")
                raise

            elif status_code == 429:
                print(f"Rate limited (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

            elif status_code in [500, 503]:
                print(f"Server error (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

            else:
                print(f"HTTP {status_code}: {detail}")
                raise

if __name__ == "__main__":
    try:
        response = llm_call_with_error_handling("What is Python?")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Failed after retries: {e}")
```

## Example 5: Using Type-Safe Client

Use the provided Python client for easier integration:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def typed_client_example():
    """Example using the type-safe client"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-virtual-key"
    ) as client:

        # Create job
        job_id = await client.create_job("simple_query")
        print(f"Created job: {job_id}")

        # Make LLM call
        response = await client.chat(
            job_id=job_id,
            messages=[
                {"role": "user", "content": "Explain recursion in Python"}
            ]
        )

        print(f"\nResponse:\n{response.choices[0].message['content']}")

        # Complete job
        result = await client.complete_job(job_id, "completed")
        print(f"\nCredits remaining: {result.credits_remaining}")

if __name__ == "__main__":
    asyncio.run(typed_client_example())
```

## Example 6: Batch Processing

Process multiple items efficiently:

```python
import requests
import os

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = os.environ["SAAS_LITELLM_VIRTUAL_KEY"]
TEAM_ID = os.environ["SAAS_LITELLM_TEAM_ID"]

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

def batch_classify(texts: list):
    """Classify multiple texts in one job"""

    # Create job
    job_response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={
            "team_id": TEAM_ID,
            "job_type": "batch_classification",
            "metadata": {"count": len(texts)}
        }
    )
    job_id = job_response.json()["job_id"]

    results = []

    # Process each text
    for i, text in enumerate(texts, 1):
        print(f"Classifying text {i}/{len(texts)}...")

        response = requests.post(
            f"{API_URL}/jobs/{job_id}/llm-call",
            headers=headers,
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "Classify sentiment as positive, negative, or neutral."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.3
            }
        ).json()

        classification = response["response"]["content"].strip().lower()
        results.append({
            "text": text,
            "sentiment": classification
        })

    # Complete job
    complete_response = requests.post(
        f"{API_URL}/jobs/{job_id}/complete",
        headers=headers,
        json={"status": "completed"}
    ).json()

    print(f"\nBatch complete!")
    print(f"Processed {len(texts)} texts")
    print(f"Credits remaining: {complete_response['costs']['credits_remaining']}")

    return results

if __name__ == "__main__":
    texts = [
        "This product is amazing! I love it.",
        "Terrible experience. Would not recommend.",
        "It's okay, nothing special.",
    ]

    results = batch_classify(texts)

    print("\nResults:")
    for result in results:
        print(f"  '{result['text']}' → {result['sentiment']}")
```

## Example 7: Check Credit Balance

Monitor your team's credit balance:

```python
import requests
import os

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = os.environ["SAAS_LITELLM_VIRTUAL_KEY"]
TEAM_ID = os.environ["SAAS_LITELLM_TEAM_ID"]

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

def check_credits():
    """Check team credit balance"""

    # Get team info
    response = requests.get(
        f"{API_URL}/teams/{TEAM_ID}",
        headers=headers
    )

    team = response.json()

    print(f"Team: {team['team_id']}")
    print(f"Organization: {team['organization_id']}")
    print(f"Status: {team['status']}")
    print(f"Credits allocated: {team['credits_allocated']}")
    print(f"Credits remaining: {team['credits_remaining']}")

    # Calculate usage
    credits_used = team['credits_allocated'] - team['credits_remaining']
    usage_percent = (credits_used / team['credits_allocated']) * 100

    print(f"Credits used: {credits_used}")
    print(f"Usage: {usage_percent:.1f}%")

    # Warnings
    if team['credits_remaining'] < team['credits_allocated'] * 0.1:
        print("\n⚠️  WARNING: Less than 10% of credits remaining!")

if __name__ == "__main__":
    check_credits()
```

## Running the Examples

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Set Environment Variables

```bash
export SAAS_LITELLM_VIRTUAL_KEY="sk-your-virtual-key"
export SAAS_LITELLM_TEAM_ID="your-team-id"
```

### 3. Run Examples

```bash
# Example 1: Simple LLM call
python example1_simple.py

# Example 2: Multi-turn conversation
python example2_conversation.py

# Example 3: Document analysis
python example3_document.py

# Example 4: Error handling
python example4_errors.py

# Example 5: Type-safe client
python example5_typed_client.py

# Example 6: Batch processing
python example6_batch.py

# Example 7: Check credits
python example7_credits.py
```

## Common Patterns

### Pattern 1: Job Wrapper

Wrap job lifecycle management:

```python
from contextlib import contextmanager

@contextmanager
def managed_job(team_id: str, job_type: str):
    """Context manager for automatic job completion"""

    # Create job
    job_response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={"team_id": team_id, "job_type": job_type}
    )
    job_id = job_response.json()["job_id"]

    try:
        yield job_id
        # Success - complete job
        requests.post(
            f"{API_URL}/jobs/{job_id}/complete",
            headers=headers,
            json={"status": "completed"}
        )
    except Exception as e:
        # Failure - mark as failed
        requests.post(
            f"{API_URL}/jobs/{job_id}/complete",
            headers=headers,
            json={"status": "failed"}
        )
        raise

# Usage
with managed_job(TEAM_ID, "query") as job_id:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": [{"role": "user", "content": "Hello"}]}
    )
```

### Pattern 2: Response Helper

Extract content easily:

```python
def get_llm_response(job_id: str, prompt: str) -> str:
    """Make LLM call and extract content"""
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={
            "messages": [{"role": "user", "content": prompt}]
        }
    ).json()

    return response["response"]["content"]

# Usage
with managed_job(TEAM_ID, "query") as job_id:
    answer = get_llm_response(job_id, "What is Python?")
    print(answer)
```

## Next Steps

Now that you've seen basic usage:

1. **[Try Streaming Examples](streaming-examples.md)** - Real-time responses
2. **[Try Structured Outputs](structured-outputs.md)** - Type-safe responses
3. **[See Full Chain Example](full-chain.md)** - Complete application flow
4. **[Review Integration Guides](../integration/overview.md)** - Detailed documentation
5. **[Explore API Reference](../api-reference/overview.md)** - Complete API docs

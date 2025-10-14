# Non-Streaming LLM Calls

Learn how to make standard (buffered) LLM calls where the complete response is returned at once.

## Overview

Non-streaming calls are the simplest way to interact with LLMs. The client sends a request and waits for the complete response to be returned at once.

**Best for:**
- Batch processing workflows
- Simple requests with short responses
- Structured outputs (JSON, Pydantic models)
- When progressive display isn't needed
- Background tasks

**Characteristics:**
- ✅ Simpler to implement
- ✅ Complete response at once
- ✅ Easier error handling
- ✅ Perfect for structured outputs
- ❌ Higher perceived latency (wait for full response)
- ❌ No progressive display

## Basic Non-Streaming Call

### Complete Workflow

```python
import requests

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = "sk-your-virtual-key-here"

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

# 1. Create job
job_response = requests.post(
    f"{API_URL}/jobs/create",
    headers=headers,
    json={
        "team_id": "acme-corp",
        "job_type": "document_analysis"
    }
).json()

job_id = job_response["job_id"]
print(f"Created job: {job_id}")

# 2. Make LLM call
llm_response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "Analyze this document and summarize the key points"}
        ]
    }
).json()

print(f"Response: {llm_response['response']['content']}")

# 3. Complete job
complete_response = requests.post(
    f"{API_URL}/jobs/{job_id}/complete",
    headers=headers,
    json={"status": "completed"}
).json()

print(f"Job completed. Credits remaining: {complete_response['costs']['credits_remaining']}")
```

### Request Format

**Endpoint:** `POST /api/jobs/{job_id}/llm-call`

**Headers:**
```json
{
  "Authorization": "Bearer sk-your-virtual-key",
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Optional Parameters:**
- `temperature` (float, 0.0-2.0) - Controls randomness
- `max_tokens` (int) - Maximum response length
- `top_p` (float, 0.0-1.0) - Nucleus sampling
- `frequency_penalty` (float, -2.0 to 2.0) - Reduce repetition
- `presence_penalty` (float, -2.0 to 2.0) - Encourage new topics
- `stop` (string or array) - Stop sequences

### Response Format

**Success Response:**
```json
{
  "call_id": "call_abc123",
  "response": {
    "content": "The capital of France is Paris.",
    "role": "assistant",
    "finish_reason": "stop"
  },
  "metadata": {
    "tokens_used": 125,
    "latency_ms": 850
  }
}
```

**Fields:**
- `call_id` - Unique identifier for this LLM call
- `response.content` - The LLM's response text
- `response.role` - Always "assistant"
- `response.finish_reason` - Why the response ended ("stop", "length", "content_filter")
- `metadata.tokens_used` - Total tokens consumed (prompt + completion)
- `metadata.latency_ms` - Response time in milliseconds

## Multi-Turn Conversations

For chat-like interactions, include conversation history in the messages:

```python
# First message
response1 = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "What is Python?"}
        ]
    }
).json()

# Second message - include history
response2 = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": response1["response"]["content"]},
            {"role": "user", "content": "What are its main uses?"}
        ]
    }
).json()

print(response2["response"]["content"])
```

!!! tip "Managing Context"
    Each LLM call is independent. To maintain conversation context, you must include all previous messages in each request.

## System Prompts

Use system messages to set the assistant's behavior:

```python
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {
                "role": "system",
                "content": "You are a professional Python tutor. Explain concepts clearly and provide code examples."
            },
            {
                "role": "user",
                "content": "How do I read a CSV file in Python?"
            }
        ]
    }
).json()
```

## Temperature and Creativity

Control the randomness of responses with temperature:

```python
# Creative response (temperature = 1.5)
creative = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "Write a creative tagline for a coffee shop"}
        ],
        "temperature": 1.5
    }
).json()

# Factual response (temperature = 0.2)
factual = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "What is 2 + 2?"}
        ],
        "temperature": 0.2
    }
).json()
```

**Temperature Guidelines:**
- **0.0-0.3** - Deterministic, factual (code generation, data extraction)
- **0.4-0.7** - Balanced (general assistant, Q&A)
- **0.8-1.2** - Creative (content writing, brainstorming)
- **1.3-2.0** - Very creative (poetry, experimental)

## Limiting Response Length

Use `max_tokens` to control response length:

```python
# Short summary
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "Summarize the theory of relativity"}
        ],
        "max_tokens": 100  # ~75 words
    }
).json()
```

!!! warning "Token Limits"
    - Tokens include both input (prompt) and output (response)
    - If `max_tokens` is too low, responses may be cut off
    - Different models have different context limits

## Using Stop Sequences

Stop generation when certain text is encountered:

```python
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "List the first 5 planets:\n1."}
        ],
        "stop": ["\n6.", "END"]  # Stop at 6th planet or "END"
    }
).json()
```

## Structured Outputs

For JSON responses, prompt the model explicitly:

```python
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "messages": [
            {
                "role": "system",
                "content": "You are a data extraction API. Always respond with valid JSON."
            },
            {
                "role": "user",
                "content": "Extract person info: John Smith, age 35, email john@example.com. Return as JSON with keys: name, age, email"
            }
        ],
        "temperature": 0.1  # Low temperature for consistency
    }
).json()

import json
data = json.loads(response["response"]["content"])
print(data["name"])  # "John Smith"
```

For type-safe structured outputs, use the typed client with Pydantic models:

[:octicons-arrow-right-24: Learn more about structured outputs](structured-outputs.md)

## Error Handling

### HTTP Error Handling

```python
import requests

def make_llm_call(job_id, messages):
    try:
        response = requests.post(
            f"{API_URL}/jobs/{job_id}/llm-call",
            headers=headers,
            json={"messages": messages},
            timeout=30  # 30 second timeout
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        print("Request timed out")
        # Retry logic here
        raise

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"Bad request: {e.response.json()}")
        elif e.response.status_code == 401:
            print("Authentication failed")
        elif e.response.status_code == 403:
            print("Insufficient credits or access denied")
        elif e.response.status_code == 429:
            print("Rate limit exceeded")
        else:
            print(f"HTTP error: {e}")
        raise

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

# Usage
result = make_llm_call(job_id, [
    {"role": "user", "content": "Hello"}
])
```

### Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| 400 | Invalid request format | Check message structure and parameters |
| 401 | Invalid virtual key | Verify your virtual key is correct |
| 403 | Insufficient credits | Add credits to your team |
| 404 | Job not found | Verify job_id exists |
| 429 | Rate limit exceeded | Wait and retry with exponential backoff |
| 500 | Internal server error | Retry with exponential backoff |
| 503 | Service unavailable | Wait and retry |

[:octicons-arrow-right-24: See comprehensive error handling guide](error-handling.md)

## Best Practices

### 1. Reuse Jobs for Related Calls

Group related LLM calls into a single job for cost tracking:

```python
# ✅ Good - One job for related calls
job_id = create_job("document_analysis")
extract_text(job_id)
classify_content(job_id)
generate_summary(job_id)
complete_job(job_id)

# ❌ Bad - Separate jobs for related calls
job1 = create_job("extract_text")
extract_text(job1)
complete_job(job1)

job2 = create_job("classify_content")
classify_content(job2)
complete_job(job2)
```

### 2. Set Reasonable Timeouts

```python
# Set appropriate timeout based on expected response time
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={"messages": messages},
    timeout=30  # 30 seconds
)
```

### 3. Validate Responses

```python
response = make_llm_call(job_id, messages)

# Check finish_reason
if response["response"]["finish_reason"] != "stop":
    print(f"Warning: Response ended with {response['response']['finish_reason']}")
    if response["response"]["finish_reason"] == "length":
        print("Response was truncated. Consider increasing max_tokens.")

# Validate content
content = response["response"]["content"]
if not content or len(content) == 0:
    print("Warning: Empty response received")
```

### 4. Cache Common Requests

For frequently repeated requests, consider caching responses:

```python
import hashlib
import json

# Simple in-memory cache
response_cache = {}

def make_cached_llm_call(job_id, messages):
    # Create cache key from messages
    cache_key = hashlib.md5(
        json.dumps(messages, sort_keys=True).encode()
    ).hexdigest()

    # Check cache
    if cache_key in response_cache:
        print("Cache hit!")
        return response_cache[cache_key]

    # Make actual call
    response = make_llm_call(job_id, messages)

    # Store in cache
    response_cache[cache_key] = response
    return response
```

!!! note "Redis Caching"
    SaaS LiteLLM automatically caches responses in Redis. This is an additional application-level cache.

### 5. Monitor Performance

Track token usage and latency:

```python
def make_llm_call_with_metrics(job_id, messages):
    response = make_llm_call(job_id, messages)

    # Log metrics
    print(f"Tokens used: {response['metadata']['tokens_used']}")
    print(f"Latency: {response['metadata']['latency_ms']}ms")

    # Alert on high usage
    if response['metadata']['tokens_used'] > 2000:
        print("Warning: High token usage")

    if response['metadata']['latency_ms'] > 5000:
        print("Warning: High latency")

    return response
```

## Complete Example

Here's a complete example of a document analysis workflow:

```python
import requests
import json

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = "sk-your-virtual-key-here"

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

def analyze_document(team_id, document_text):
    """Analyze a document and return structured insights"""

    # 1. Create job
    job = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={
            "team_id": team_id,
            "job_type": "document_analysis",
            "metadata": {"document_length": len(document_text)}
        }
    ).json()
    job_id = job["job_id"]

    try:
        # 2. Extract key points
        extraction = requests.post(
            f"{API_URL}/jobs/{job_id}/llm-call",
            headers=headers,
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "Extract key points from documents as bullet points."
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

        key_points = extraction["response"]["content"]

        # 3. Generate summary
        summary = requests.post(
            f"{API_URL}/jobs/{job_id}/llm-call",
            headers=headers,
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "Create concise summaries of documents."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this in 2-3 sentences:\n\n{document_text}"
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 200
            }
        ).json()

        summary_text = summary["response"]["content"]

        # 4. Complete job
        result = requests.post(
            f"{API_URL}/jobs/{job_id}/complete",
            headers=headers,
            json={
                "status": "completed",
                "metadata": {"success": True}
            }
        ).json()

        return {
            "job_id": job_id,
            "key_points": key_points,
            "summary": summary_text,
            "credits_remaining": result["costs"]["credits_remaining"]
        }

    except Exception as e:
        # Mark job as failed
        requests.post(
            f"{API_URL}/jobs/{job_id}/complete",
            headers=headers,
            json={
                "status": "failed",
                "metadata": {"error": str(e)}
            }
        )
        raise

# Usage
document = """
Artificial intelligence (AI) is transforming industries...
[long document text]
"""

result = analyze_document("acme-corp", document)
print(f"Summary: {result['summary']}")
print(f"Key Points:\n{result['key_points']}")
print(f"Credits remaining: {result['credits_remaining']}")
```

## Next Steps

Now that you understand non-streaming calls:

1. **[Learn Streaming Calls](streaming.md)** - Real-time responses
2. **[Try Structured Outputs](structured-outputs.md)** - Type-safe Pydantic models
3. **[See Full Examples](../examples/basic-usage.md)** - Working code
4. **[Error Handling](error-handling.md)** - Comprehensive error handling

## Additional Resources

- **[Job Workflow Guide](job-workflow.md)** - Understanding jobs
- **[Best Practices](best-practices.md)** - Optimization tips
- **[API Reference](../api-reference/llm-calls.md)** - Complete API docs

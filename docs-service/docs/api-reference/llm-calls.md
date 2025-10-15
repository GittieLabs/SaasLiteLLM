# LLM Calls API

The LLM Calls API provides endpoints for making both non-streaming and streaming LLM calls within job contexts. All calls are tracked, aggregated, and billed at the job level.

## Overview

LLM calls are always made within the context of a job. The API supports:

- **Non-streaming calls** - Standard request/response pattern
- **Streaming calls** - Real-time Server-Sent Events (SSE) streaming
- **Model group resolution** - Automatic model selection based on team permissions
- **OpenAI-compatible format** - Standard messages format
- **Cost tracking** - Automatic tracking of tokens and costs

**Base URL:** `/api/jobs/{job_id}`

**Authentication:** All endpoints require a Bearer token (virtual API key) in the `Authorization` header.

## Endpoints

### Non-Streaming LLM Call

Make a standard LLM call within a job context.

**Endpoint:** `POST /api/jobs/{job_id}/llm-call`

**Authentication:** Required (virtual key)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string (UUID) | The job identifier |

**Request Body:**

```json
{
  "model_group": "ResumeAgent",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Parse this resume..."
    }
  ],
  "purpose": "resume_parsing",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_group` | string | Yes | Name of model group (e.g., "ResumeAgent", "ChatAgent") |
| `messages` | array | Yes | OpenAI-compatible messages array |
| `messages[].role` | string | Yes | Message role: "system", "user", or "assistant" |
| `messages[].content` | string | Yes | Message content |
| `purpose` | string | No | Optional label for tracking (e.g., "parsing", "analysis") |
| `temperature` | number | No | Sampling temperature (0.0-2.0, default: 0.7) |
| `max_tokens` | integer | No | Maximum tokens to generate (optional) |

**Response (200 OK):**

```json
{
  "call_id": "call-uuid-123",
  "response": {
    "content": "Here is the parsed resume information...",
    "finish_reason": "stop"
  },
  "metadata": {
    "tokens_used": 450,
    "latency_ms": 1250,
    "model_group": "ResumeAgent"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `call_id` | string (UUID) | Unique identifier for this LLM call |
| `response.content` | string | The generated response content |
| `response.finish_reason` | string | Why generation stopped: "stop", "length", or "content_filter" |
| `metadata.tokens_used` | integer | Total tokens used (prompt + completion) |
| `metadata.latency_ms` | integer | Call latency in milliseconds |
| `metadata.model_group` | string | Model group that was used |

**Example Request:**

=== "cURL"

    ```bash
    curl -X POST http://localhost:8003/api/jobs/{job_id}/llm-call \
      -H "Authorization: Bearer sk-your-virtual-key" \
      -H "Content-Type: application/json" \
      -d '{
        "model_group": "ResumeAgent",
        "messages": [
          {
            "role": "system",
            "content": "You are a resume parsing assistant."
          },
          {
            "role": "user",
            "content": "Extract key skills from this resume: ..."
          }
        ],
        "purpose": "skill_extraction",
        "temperature": 0.3
      }'
    ```

=== "Python"

    ```python
    import requests

    API_URL = "http://localhost:8003/api"
    VIRTUAL_KEY = "sk-your-virtual-key"

    headers = {
        "Authorization": f"Bearer {VIRTUAL_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={
            "model_group": "ResumeAgent",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a resume parsing assistant."
                },
                {
                    "role": "user",
                    "content": "Extract key skills from this resume: ..."
                }
            ],
            "purpose": "skill_extraction",
            "temperature": 0.3
        }
    )

    result = response.json()
    print(result['response']['content'])
    print(f"Tokens used: {result['metadata']['tokens_used']}")
    print(f"Latency: {result['metadata']['latency_ms']}ms")
    ```

=== "JavaScript"

    ```javascript
    const API_URL = "http://localhost:8003/api";
    const VIRTUAL_KEY = "sk-your-virtual-key";

    const response = await fetch(`${API_URL}/jobs/${jobId}/llm-call`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${VIRTUAL_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model_group: 'ResumeAgent',
        messages: [
          {
            role: 'system',
            content: 'You are a resume parsing assistant.'
          },
          {
            role: 'user',
            content: 'Extract key skills from this resume: ...'
          }
        ],
        purpose: 'skill_extraction',
        temperature: 0.3
      })
    });

    const result = await response.json();
    console.log(result.response.content);
    console.log(`Tokens used: ${result.metadata.tokens_used}`);
    console.log(`Latency: ${result.metadata.latency_ms}ms`);
    ```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing virtual key |
| 403 | Forbidden | Job does not belong to your team, or model group not allowed |
| 404 | Not Found | Job not found |
| 422 | Validation Error | Invalid request data |
| 500 | Internal Server Error | LLM call failed or server error |

**Example Error Response:**

```json
{
  "detail": "Team 'acme-corp' does not have access to model group 'GPT4Agent'"
}
```

---

### Streaming LLM Call

Make a streaming LLM call with real-time Server-Sent Events (SSE).

**Endpoint:** `POST /api/jobs/{job_id}/llm-call-stream`

**Authentication:** Required (virtual key)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string (UUID) | The job identifier |

**Request Body:**

```json
{
  "model_group": "ChatAgent",
  "messages": [
    {
      "role": "user",
      "content": "Tell me a story"
    }
  ],
  "purpose": "chat",
  "temperature": 0.8,
  "max_tokens": 500
}
```

**Request Fields:** (Same as non-streaming call)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_group` | string | Yes | Name of model group |
| `messages` | array | Yes | OpenAI-compatible messages array |
| `purpose` | string | No | Optional label for tracking |
| `temperature` | number | No | Sampling temperature (0.0-2.0, default: 0.7) |
| `max_tokens` | integer | No | Maximum tokens to generate |

**Response Headers:**

```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
Connection: keep-alive
```

**Response Format (Server-Sent Events):**

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1697896000,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant","content":"Once"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1697896000,"model":"gpt-4","choices":[{"index":0,"delta":{"content":" upon"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1697896000,"model":"gpt-4","choices":[{"index":0,"delta":{"content":" a"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1697896000,"model":"gpt-4","choices":[{"index":0,"delta":{"content":" time"},"finish_reason":null}]}

data: [DONE]
```

**SSE Chunk Format:**

Each chunk is a JSON object prefixed with `data: `:

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion.chunk",
  "created": 1697896000,
  "model": "gpt-4-turbo",
  "choices": [
    {
      "index": 0,
      "delta": {
        "role": "assistant",
        "content": "Hello"
      },
      "finish_reason": null
    }
  ]
}
```

**Chunk Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique completion ID |
| `object` | string | Always "chat.completion.chunk" for streaming |
| `created` | integer | Unix timestamp |
| `model` | string | Actual model used (resolved from model group) |
| `choices[].index` | integer | Choice index (always 0) |
| `choices[].delta.role` | string | Role (only present in first chunk: "assistant") |
| `choices[].delta.content` | string | Incremental text content |
| `choices[].finish_reason` | string | null during streaming, "stop"/"length" at end |

**Final Chunk:**

The last chunk includes usage metadata:

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion.chunk",
  "created": 1697896000,
  "model": "gpt-4-turbo",
  "choices": [
    {
      "index": 0,
      "delta": {},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 125,
    "completion_tokens": 450,
    "total_tokens": 575
  }
}
```

**Stream Termination:**

The stream ends with:

```
data: [DONE]
```

**Example Request:**

=== "Python (Raw)"

    ```python
    import requests
    import json

    API_URL = "http://localhost:8003/api"
    VIRTUAL_KEY = "sk-your-virtual-key"

    headers = {
        "Authorization": f"Bearer {VIRTUAL_KEY}",
        "Content-Type": "application/json"
    }

    # Make streaming request
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call-stream",
        headers=headers,
        json={
            "model_group": "ChatAgent",
            "messages": [
                {"role": "user", "content": "Tell me a story"}
            ],
            "temperature": 0.8
        },
        stream=True  # Important: enable streaming
    )

    # Process Server-Sent Events
    accumulated = ""
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix

                if data_str == '[DONE]':
                    print("\n\nStream complete!")
                    break

                try:
                    chunk = json.loads(data_str)
                    if chunk.get("choices"):
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            accumulated += content
                            print(content, end="", flush=True)
                except json.JSONDecodeError:
                    continue

    print(f"\n\nFull response: {accumulated}")
    ```

=== "Python (Typed Client)"

    ```python
    from examples.typed_client import SaaSLLMClient

    async def streaming_example():
        async with SaaSLLMClient(
            base_url="http://localhost:8003",
            team_id="acme-corp",
            virtual_key="sk-your-virtual-key"
        ) as client:
            # Create job
            job_id = await client.create_job("chat")

            # Stream response
            accumulated = ""
            async for chunk in client.chat_stream(
                job_id=job_id,
                messages=[
                    {"role": "user", "content": "Tell me a story"}
                ],
                temperature=0.8
            ):
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    content = delta.get("content", "")
                    if content:
                        accumulated += content
                        print(content, end="", flush=True)

            print(f"\n\nFull response: {accumulated}")

            # Complete job
            result = await client.complete_job(job_id, "completed")
            print(f"Credits remaining: {result.credits_remaining}")

    import asyncio
    asyncio.run(streaming_example())
    ```

=== "JavaScript"

    ```javascript
    async function streamChat(jobId, messages) {
      const response = await fetch(`${API_URL}/jobs/${jobId}/llm-call-stream`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${VIRTUAL_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model_group: 'ChatAgent',
          messages: messages,
          temperature: 0.8
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let accumulated = '';

      while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6);

            if (data === '[DONE]') {
              console.log('\nStream complete');
              return accumulated;
            }

            try {
              const chunk = JSON.parse(data);
              const content = chunk.choices?.[0]?.delta?.content || '';
              if (content) {
                accumulated += content;
                process.stdout.write(content);  // Node.js
                // Or: document.getElementById('output').textContent += content;  // Browser
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

      return accumulated;
    }
    ```

**Error Handling:**

Errors during streaming are sent as error chunks:

```json
{
  "error": {
    "message": "Model timeout exceeded",
    "type": "timeout_error",
    "code": "model_timeout"
  }
}
```

**Error Responses:**

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing virtual key |
| 403 | Forbidden | Job does not belong to your team, or model group not allowed |
| 404 | Not Found | Job not found |
| 422 | Validation Error | Invalid request data |
| 500 | Internal Server Error | Stream failed or server error |

---

## Model Parameters

### Temperature

Controls randomness in the output.

- **Range:** 0.0 to 2.0
- **Default:** 0.7
- **Lower values (0.0-0.5):** More deterministic, focused responses
- **Higher values (0.8-1.5):** More creative, varied responses

**Examples:**

```python
# Factual, precise response
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "model_group": "AnalysisAgent",
        "messages": [{"role": "user", "content": "What is photosynthesis?"}],
        "temperature": 0.2  # Low temperature for facts
    }
)

# Creative, varied response
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "model_group": "ChatAgent",
        "messages": [{"role": "user", "content": "Write a creative story"}],
        "temperature": 1.2  # High temperature for creativity
    }
)
```

### Max Tokens

Limits the maximum number of tokens to generate.

- **Type:** Integer
- **Default:** Varies by model (typically 1000-4000)
- **Use cases:** Limit response length, control costs

**Examples:**

```python
# Short summary
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "model_group": "SummaryAgent",
        "messages": [{"role": "user", "content": "Summarize this article..."}],
        "max_tokens": 150  # Limit to ~150 tokens
    }
)

# Long-form content
response = requests.post(
    f"{API_URL}/jobs/{job_id}/llm-call",
    headers=headers,
    json={
        "model_group": "WritingAgent",
        "messages": [{"role": "user", "content": "Write a detailed article..."}],
        "max_tokens": 2000  # Allow up to 2000 tokens
    }
)
```

### Messages Format

The `messages` array follows the OpenAI format:

**System Message:**

Sets the assistant's behavior and context.

```json
{
  "role": "system",
  "content": "You are a helpful assistant that specializes in resume analysis."
}
```

**User Message:**

User input or query.

```json
{
  "role": "user",
  "content": "Parse this resume and extract key skills."
}
```

**Assistant Message:**

Previous assistant responses (for multi-turn conversations).

```json
{
  "role": "assistant",
  "content": "I've identified the following skills: Python, SQL, Machine Learning..."
}
```

**Complete Multi-Turn Example:**

```python
messages = [
    {
        "role": "system",
        "content": "You are a Python tutor."
    },
    {
        "role": "user",
        "content": "What is a list comprehension?"
    },
    {
        "role": "assistant",
        "content": "A list comprehension is a concise way to create lists in Python..."
    },
    {
        "role": "user",
        "content": "Can you show me an example?"
    }
]
```

---

## Model Group Resolution

Model groups abstract the actual model selection, allowing you to:

- **Change models without code changes** - Update model group configuration
- **Control costs** - Use different models for different teams
- **Manage permissions** - Restrict which teams can use which models
- **Implement fallbacks** - Automatically fallback to alternative models

**Example:**

If "ResumeAgent" model group is configured with:
- Primary: `gpt-4-turbo`
- Fallbacks: `gpt-3.5-turbo`, `claude-3-sonnet`

Your call to "ResumeAgent" will:
1. Attempt `gpt-4-turbo` first
2. Fallback to `gpt-3.5-turbo` if primary fails
3. Fallback to `claude-3-sonnet` if both fail

See [Model Groups API](../admin-dashboard/model-access-groups.md) for configuration details.

---

## Complete Example: Multi-Step Job

```python
import requests

API_URL = "http://localhost:8003/api"
VIRTUAL_KEY = "sk-your-virtual-key"

headers = {
    "Authorization": f"Bearer {VIRTUAL_KEY}",
    "Content-Type": "application/json"
}

# 1. Create job
job = requests.post(
    f"{API_URL}/jobs/create",
    headers=headers,
    json={
        "team_id": "acme-corp",
        "job_type": "document_analysis"
    }
).json()

job_id = job["job_id"]
print(f"Created job: {job_id}")

# 2. Make multiple LLM calls
steps = [
    ("Parse document", "Extract key information from this document..."),
    ("Classify content", "Classify the content type..."),
    ("Generate summary", "Generate a concise summary...")
]

for purpose, prompt in steps:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={
            "model_group": "AnalysisAgent",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "purpose": purpose,
            "temperature": 0.3
        }
    ).json()

    print(f"{purpose}: {response['response']['content'][:50]}...")
    print(f"  Tokens: {response['metadata']['tokens_used']}")

# 3. Complete job
result = requests.post(
    f"{API_URL}/jobs/{job_id}/complete",
    headers=headers,
    json={"status": "completed"}
).json()

print(f"\nJob completed!")
print(f"Total calls: {result['costs']['total_calls']}")
print(f"Total tokens: {result['costs']['total_tokens']}")
print(f"Total cost: ${result['costs']['total_cost_usd']:.4f}")
print(f"Credit deducted: {result['costs']['credit_applied']}")
print(f"Credits remaining: {result['costs']['credits_remaining']}")
```

## Streaming vs Non-Streaming Comparison

| Feature | Non-Streaming | Streaming |
|---------|---------------|-----------|
| **Latency (perceived)** | High (~2000ms TTFT) | Low (~300-500ms TTFT) |
| **User Experience** | Wait for complete response | Progressive display |
| **Implementation** | Simpler | More complex |
| **Use Case** | Batch processing | Interactive apps |
| **Buffering** | Full response buffered | Zero buffering |
| **Credits** | 1 per completed job | 1 per completed job |
| **Cost** | Same | Same |

**When to use non-streaming:**
- Batch processing jobs
- Background tasks
- Simple integrations
- When full response is needed before processing

**When to use streaming:**
- Chat interfaces
- Real-time user interactions
- Long-form content generation
- Lower perceived latency requirement

## Rate Limiting

LLM calls are subject to rate limiting:

- **Requests per minute (RPM):** Configurable per team
- **Tokens per minute (TPM):** Configurable per team
- **Default:** 60 RPM, 60,000 TPM

When rate limited, you'll receive a `429 Too Many Requests` response.

## Best Practices

1. **Use appropriate model groups** - Select the right model group for your use case
2. **Set reasonable temperatures** - Lower for facts, higher for creativity
3. **Limit max_tokens** - Control response length and costs
4. **Add purpose labels** - Track different types of calls for analytics
5. **Handle errors gracefully** - Implement retry logic with exponential backoff
6. **Use streaming for UX** - Provide better user experience with real-time feedback
7. **Always complete jobs** - Ensure jobs are completed to trigger proper billing

## See Also

- [Jobs API](jobs.md) - Create and manage jobs
- [Job Workflow Guide](../integration/job-workflow.md) - Complete workflow documentation
- [Streaming Guide](../integration/streaming.md) - Detailed streaming implementation
- [Non-Streaming Guide](../integration/non-streaming.md) - Standard call patterns
- [Model Groups](../admin-dashboard/model-access-groups.md) - Configure model groups

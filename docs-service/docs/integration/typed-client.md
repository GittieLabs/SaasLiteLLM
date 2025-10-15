# Type-Safe Python Client

The easiest way to integrate with SaaS LiteLLM is using our type-safe Python client with full async support and Pydantic validation.

!!! tip "Download the Client"
    [:octicons-download-24: Get the Typed Client](../downloads/typed-client.md){ .md-button .md-button--primary }

    Complete source code, installation guide, and usage examples.

## Why Use the Typed Client?

**Raw API:**
```python
# Complex, verbose, error-prone
import requests

response = requests.post(
    "http://localhost:8003/api/jobs/create",
    headers={"Authorization": f"Bearer {VIRTUAL_KEY}"},
    json={"team_id": "acme-corp", "job_type": "analysis"}
)
job = response.json()

llm_response = requests.post(
    f"http://localhost:8003/api/jobs/{job['job_id']}/llm-call",
    headers={"Authorization": f"Bearer {VIRTUAL_KEY}"},
    json={"messages": [{"role": "user", "content": "Hello"}]}
)
# ...
```

**Typed Client:**
```python
# Clean, typed, easy
from examples.typed_client import SaaSLLMClient

async with SaaSLLMClient(
    base_url="http://localhost:8003",
    team_id="acme-corp",
    virtual_key="sk-your-key"
) as client:
    job_id = await client.create_job("analysis")
    response = await client.chat(job_id, [
        {"role": "user", "content": "Hello"}
    ])
    await client.complete_job(job_id, "completed")
```

✅ Type hints and autocomplete
✅ Automatic error handling
✅ Context manager support
✅ Pydantic validation
✅ Async/await support
✅ Cleaner code

## Installation

### Copy the Client

The typed client is in `examples/typed_client.py`:

```bash
# Copy to your project
cp examples/typed_client.py your_project/saas_litellm_client.py
```

### Install Dependencies

```bash
pip install httpx pydantic
```

## Quick Start

### Basic Usage

```python
import asyncio
from saas_litellm_client import SaaSLLMClient

async def main():
    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-virtual-key-here"
    ) as client:

        # Create job
        job_id = await client.create_job("my_first_job")
        print(f"Created job: {job_id}")

        # Make LLM call
        response = await client.chat(
            job_id=job_id,
            messages=[
                {"role": "user", "content": "What is Python?"}
            ]
        )

        print(f"Response: {response.choices[0].message['content']}")

        # Complete job
        result = await client.complete_job(job_id, "completed")
        print(f"Credits remaining: {result.credits_remaining}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Client Methods

### create_job()

Create a new job for tracking:

```python
job_id = await client.create_job(
    job_type="document_analysis",
    metadata={"document_id": "doc_123", "user": "john"}
)
```

**Parameters:**
- `job_type` (str): Type of job (e.g., "analysis", "chat", "extraction")
- `metadata` (dict, optional): Custom data

**Returns:** `str` - Job ID (UUID)

### chat()

Make a non-streaming LLM call:

```python
response = await client.chat(
    job_id=job_id,
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    temperature=0.7,
    max_tokens=500
)

content = response.choices[0].message["content"]
```

**Parameters:**
- `job_id` (str): Job ID from create_job()
- `messages` (list): Chat messages
- `temperature` (float, optional): 0.0-2.0, default 0.7
- `max_tokens` (int, optional): Max response length
- `top_p` (float, optional): Nucleus sampling
- `frequency_penalty` (float, optional): Reduce repetition
- `presence_penalty` (float, optional): Encourage new topics
- `stop` (str|list, optional): Stop sequences

**Returns:** `ChatCompletionResponse` - Pydantic model with response

### chat_stream()

Make a streaming LLM call:

```python
async for chunk in client.chat_stream(
    job_id=job_id,
    messages=[{"role": "user", "content": "Tell me a story"}]
):
    if chunk.choices:
        content = chunk.choices[0].delta.get("content", "")
        print(content, end="", flush=True)
```

**Parameters:** Same as `chat()`

**Yields:** `ChatCompletionChunk` - Streaming chunks

### structured_output()

Get type-safe structured responses with Pydantic models:

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    email: str

person = await client.structured_output(
    job_id=job_id,
    messages=[{
        "role": "user",
        "content": "Extract: John Smith, 35, john@example.com"
    }],
    response_model=Person
)

print(f"Name: {person.name}, Age: {person.age}")
```

**Parameters:**
- `job_id` (str): Job ID
- `messages` (list): Chat messages
- `response_model` (Type[BaseModel]): Pydantic model class
- Other chat parameters

**Returns:** Instance of your Pydantic model

### complete_job()

Mark job as completed:

```python
result = await client.complete_job(
    job_id=job_id,
    status="completed",
    metadata={"result": "success", "output_file": "result.json"}
)

print(f"Credits remaining: {result.credits_remaining}")
print(f"Total calls: {result.total_calls}")
```

**Parameters:**
- `job_id` (str): Job ID
- `status` (str): "completed" or "failed"
- `metadata` (dict, optional): Additional data

**Returns:** `JobCompletionResult` - Pydantic model with results

## Complete Example

### Document Analysis

```python
import asyncio
from saas_litellm_client import SaaSLLMClient

async def analyze_document(document_text: str):
    """Analyze a document: extract key points and summarize"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        # Create job
        job_id = await client.create_job(
            job_type="document_analysis",
            metadata={"document_length": len(document_text)}
        )

        try:
            # Extract key points
            key_points_response = await client.chat(
                job_id=job_id,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract key points as bullet points"
                    },
                    {
                        "role": "user",
                        "content": f"Extract key points from:\n\n{document_text}"
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )

            key_points = key_points_response.choices[0].message["content"]
            print(f"Key Points:\n{key_points}\n")

            # Generate summary
            summary_response = await client.chat(
                job_id=job_id,
                messages=[
                    {
                        "role": "system",
                        "content": "Create concise summaries"
                    },
                    {
                        "role": "user",
                        "content": f"Summarize in 2-3 sentences:\n\n{document_text}"
                    }
                ],
                temperature=0.5,
                max_tokens=200
            )

            summary = summary_response.choices[0].message["content"]
            print(f"Summary:\n{summary}\n")

            # Complete job
            result = await client.complete_job(job_id, "completed")
            print(f"Analysis complete! Credits remaining: {result.credits_remaining}")

            return {
                "key_points": key_points,
                "summary": summary
            }

        except Exception as e:
            # Mark job as failed
            await client.complete_job(job_id, "failed")
            raise

if __name__ == "__main__":
    document = """
    Artificial intelligence (AI) is transforming industries worldwide.
    Machine learning algorithms can process vast amounts of data and
    identify patterns. This technology is being applied in healthcare,
    finance, and transportation for various innovative solutions.
    """

    result = asyncio.run(analyze_document(document))
```

### Streaming Chat

```python
import asyncio
from saas_litellm_client import SaaSLLMClient

async def interactive_chat():
    """Interactive streaming chat session"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        # Create job for chat session
        job_id = await client.create_job("chat_session")
        messages = []

        while True:
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break

            # Add to conversation
            messages.append({"role": "user", "content": user_input})

            # Stream response
            print("Assistant: ", end="", flush=True)
            assistant_response = ""

            async for chunk in client.chat_stream(
                job_id=job_id,
                messages=messages,
                temperature=0.7
            ):
                if chunk.choices:
                    content = chunk.choices[0].delta.get("content", "")
                    assistant_response += content
                    print(content, end="", flush=True)

            # Add assistant response to conversation
            messages.append({"role": "assistant", "content": assistant_response})

        # Complete job
        result = await client.complete_job(job_id, "completed")
        print(f"\n\nChat ended. Credits remaining: {result.credits_remaining}")

if __name__ == "__main__":
    asyncio.run(interactive_chat())
```

### Structured Data Extraction

```python
import asyncio
from pydantic import BaseModel
from saas_litellm_client import SaaSLLMClient

class Resume(BaseModel):
    name: str
    email: str
    phone: str
    years_experience: int
    skills: list[str]
    education: str

async def parse_resume(resume_text: str):
    """Extract structured data from resume"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("resume_parsing")

        try:
            # Get structured output
            resume = await client.structured_output(
                job_id=job_id,
                messages=[{
                    "role": "user",
                    "content": f"Extract structured data from this resume:\n\n{resume_text}"
                }],
                response_model=Resume
            )

            # resume is now a fully typed Resume object!
            print(f"Name: {resume.name}")
            print(f"Email: {resume.email}")
            print(f"Experience: {resume.years_experience} years")
            print(f"Skills: {', '.join(resume.skills)}")

            await client.complete_job(job_id, "completed")
            return resume

        except Exception as e:
            await client.complete_job(job_id, "failed")
            raise

if __name__ == "__main__":
    resume_text = """
    John Doe
    Email: john@example.com
    Phone: (555) 123-4567

    EXPERIENCE: 5 years as a software engineer

    SKILLS: Python, JavaScript, React, Docker, Kubernetes

    EDUCATION: BS in Computer Science, MIT
    """

    result = asyncio.run(parse_resume(resume_text))
```

## Error Handling

### Basic Error Handling

```python
from httpx import HTTPStatusError

async with SaaSLLMClient(...) as client:
    try:
        job_id = await client.create_job("test")
        response = await client.chat(job_id, messages)
        await client.complete_job(job_id, "completed")

    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Authentication failed - check your virtual key")
        elif e.response.status_code == 403:
            print("Access denied - check credits or team status")
        elif e.response.status_code == 429:
            print("Rate limited - wait and retry")
        else:
            print(f"HTTP error: {e}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
```

### Retry Logic

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def make_llm_call_with_retry(client, job_id, messages):
    """Make LLM call with automatic retries"""
    return await client.chat(job_id, messages)

# Usage
async with SaaSLLMClient(...) as client:
    job_id = await client.create_job("test")

    try:
        response = await make_llm_call_with_retry(client, job_id, messages)
        await client.complete_job(job_id, "completed")
    except Exception as e:
        await client.complete_job(job_id, "failed")
        raise
```

## Configuration

### Environment Variables

```python
import os
from saas_litellm_client import SaaSLLMClient

# Load from environment
API_URL = os.environ.get("SAAS_LITELLM_API_URL", "http://localhost:8003")
TEAM_ID = os.environ["SAAS_LITELLM_TEAM_ID"]
VIRTUAL_KEY = os.environ["SAAS_LITELLM_VIRTUAL_KEY"]

async with SaaSLLMClient(
    base_url=API_URL,
    team_id=TEAM_ID,
    virtual_key=VIRTUAL_KEY
) as client:
    # Use client
    pass
```

**`.env` file:**
```bash
SAAS_LITELLM_API_URL=https://api.yourcompany.com
SAAS_LITELLM_TEAM_ID=acme-prod
SAAS_LITELLM_VIRTUAL_KEY=sk-your-actual-key-here
```

### Custom Timeout

```python
async with SaaSLLMClient(
    base_url="http://localhost:8003",
    team_id="acme-corp",
    virtual_key="sk-your-key",
    timeout=60.0  # 60 seconds
) as client:
    # Use client
    pass
```

## Advanced Usage

### Concurrent Jobs

Process multiple jobs concurrently:

```python
import asyncio

async def process_document(client, document):
    """Process one document"""
    job_id = await client.create_job("analysis")
    response = await client.chat(job_id, [
        {"role": "user", "content": f"Analyze: {document}"}
    ])
    await client.complete_job(job_id, "completed")
    return response

async def process_batch(documents):
    """Process multiple documents concurrently"""
    async with SaaSLLMClient(...) as client:
        tasks = [process_document(client, doc) for doc in documents]
        results = await asyncio.gather(*tasks)
        return results

# Process 10 documents at once
documents = ["doc1", "doc2", ..., "doc10"]
results = asyncio.run(process_batch(documents))
```

### Context Manager Options

```python
# Option 1: Context manager (recommended)
async with SaaSLLMClient(...) as client:
    # Automatic cleanup
    pass

# Option 2: Manual lifecycle
client = SaaSLLMClient(...)
try:
    job_id = await client.create_job("test")
    # ...
finally:
    await client.close()
```

## Best Practices

1. **Always use context manager** (`async with`) for automatic cleanup
2. **Handle errors properly** - Always complete jobs, even on failure
3. **Use structured outputs** for type safety when extracting data
4. **Set timeouts** - Don't let requests hang forever
5. **Monitor credits** - Check balance periodically
6. **Reuse client** - Don't create new client for each request
7. **Environment variables** - Never hardcode credentials

## Troubleshooting

### Import Error

**Problem:** `ImportError: No module named 'httpx'`

**Solution:**
```bash
pip install httpx pydantic
```

### Authentication Error

**Problem:** 401 Unauthorized

**Solutions:**
1. Check virtual key is correct
2. Verify `Authorization: Bearer sk-...` format
3. Check team is active (not suspended)

### Timeout Error

**Problem:** Request times out

**Solutions:**
1. Increase timeout: `SaaSLLMClient(..., timeout=120)`
2. Check API is running and accessible
3. For long responses, use streaming instead

## Next Steps

Now that you understand the typed client:

1. **[See More Examples](../examples/basic-usage.md)** - Additional code examples
2. **[Learn About Streaming](streaming.md)** - Real-time responses
3. **[Structured Outputs](structured-outputs.md)** - Type-safe data extraction
4. **[Error Handling](error-handling.md)** - Comprehensive error handling
5. **[Best Practices](best-practices.md)** - Production-ready patterns

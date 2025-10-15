# Streaming Examples

Real-world examples of using Server-Sent Events (SSE) streaming for real-time LLM responses.

!!! info "Built on LiteLLM"
    Streaming works by forwarding chunks directly from [LiteLLM](https://docs.litellm.ai) through the SaaS API layer to your application with zero buffering for minimal latency.

## Prerequisites

```bash
# Install required packages
pip install httpx pydantic
```

## Example 1: Basic Streaming

The simplest streaming example - print response as it arrives:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def basic_streaming():
    """Stream a response and print it in real-time"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        # Create job
        job_id = await client.create_job("streaming_demo")

        # Stream response
        print("Assistant: ", end="", flush=True)

        async for chunk in client.chat_stream(
            job_id=job_id,
            messages=[
                {"role": "user", "content": "Write a short poem about Python"}
            ]
        ):
            if chunk.choices:
                content = chunk.choices[0].delta.get("content", "")
                if content:
                    print(content, end="", flush=True)

        print()  # New line after stream completes

        # Complete job
        result = await client.complete_job(job_id, "completed")
        print(f"\nCredits remaining: {result.credits_remaining}")

if __name__ == "__main__":
    asyncio.run(basic_streaming())
```

**Output:**
```
Assistant: In Python's realm where code takes flight,
With syntax clean and clear as light,
We build and dream, create with ease,
A language that's designed to please.

Credits remaining: 999
```

## Example 2: Accumulating Stream

Collect the full response while displaying chunks:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def accumulating_stream():
    """Stream response while accumulating full text"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("chat")

        # Accumulate full response
        full_response = ""

        async for chunk in client.chat_stream(
            job_id=job_id,
            messages=[
                {"role": "user", "content": "Explain quantum computing in 2 sentences"}
            ],
            temperature=0.7
        ):
            if chunk.choices:
                content = chunk.choices[0].delta.get("content", "")
                if content:
                    full_response += content
                    print(content, end="", flush=True)

        print(f"\n\nFull response length: {len(full_response)} characters")

        # You can now use full_response for further processing
        await client.complete_job(job_id, "completed")

if __name__ == "__main__":
    asyncio.run(accumulating_stream())
```

## Example 3: Interactive Chat

Build an interactive chat interface with streaming:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def interactive_chat():
    """Interactive chat with streaming responses"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        # Create job for chat session
        job_id = await client.create_job("chat_session")
        messages = []

        print("Interactive Chat (type 'quit' to exit)")
        print("-" * 50)

        while True:
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break

            # Add to conversation
            messages.append({"role": "user", "content": user_input})

            # Stream response
            print("Assistant: ", end="", flush=True)
            assistant_response = ""

            try:
                async for chunk in client.chat_stream(
                    job_id=job_id,
                    messages=messages,
                    temperature=0.7
                ):
                    if chunk.choices:
                        content = chunk.choices[0].delta.get("content", "")
                        if content:
                            assistant_response += content
                            print(content, end="", flush=True)

                # Add assistant response to conversation
                messages.append({"role": "assistant", "content": assistant_response})

            except Exception as e:
                print(f"\nError: {e}")
                break

        # Complete job
        result = await client.complete_job(job_id, "completed")
        print(f"\n\nChat ended. Total messages: {len(messages)}")
        print(f"Credits remaining: {result.credits_remaining}")

if __name__ == "__main__":
    asyncio.run(interactive_chat())
```

**Sample Session:**
```
Interactive Chat (type 'quit' to exit)
--------------------------------------------------

You: What is FastAPI?
Assistant: FastAPI is a modern, fast web framework for building APIs with Python...

You: How does it compare to Flask?
Assistant: FastAPI has several advantages over Flask...

You: quit
Goodbye!

Chat ended. Total messages: 4
Credits remaining: 998
```

## Example 4: Streaming with System Prompt

Use a system prompt to control response style:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def streaming_with_system_prompt():
    """Stream with custom system prompt"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("tutoring")

        async for chunk in client.chat_stream(
            job_id=job_id,
            messages=[
                {
                    "role": "system",
                    "content": "You are a patient Python tutor. "
                               "Explain concepts simply with code examples."
                },
                {
                    "role": "user",
                    "content": "How do I read a CSV file in Python?"
                }
            ],
            temperature=0.7
        ):
            if chunk.choices:
                content = chunk.choices[0].delta.get("content", "")
                if content:
                    print(content, end="", flush=True)

        print()
        await client.complete_job(job_id, "completed")

if __name__ == "__main__":
    asyncio.run(streaming_with_system_prompt())
```

## Example 5: Multi-Document Analysis

Stream analysis of multiple documents:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def analyze_documents_streaming(documents: list[str]):
    """Analyze multiple documents with streaming"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("batch_analysis")

        for i, document in enumerate(documents, 1):
            print(f"\n{'='*60}")
            print(f"Document {i}/{len(documents)}")
            print(f"{'='*60}")
            print("Analysis: ", end="", flush=True)

            async for chunk in client.chat_stream(
                job_id=job_id,
                messages=[
                    {
                        "role": "system",
                        "content": "Provide concise analysis of documents"
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this text:\n\n{document}"
                    }
                ],
                temperature=0.5,
                max_tokens=200
            ):
                if chunk.choices:
                    content = chunk.choices[0].delta.get("content", "")
                    if content:
                        print(content, end="", flush=True)

        print(f"\n\n{'='*60}")
        result = await client.complete_job(job_id, "completed")
        print(f"Analysis complete! Analyzed {len(documents)} documents")
        print(f"Credits remaining: {result.credits_remaining}")

if __name__ == "__main__":
    documents = [
        "AI is transforming healthcare with predictive diagnostics...",
        "Renewable energy sources are becoming more cost-effective...",
        "Remote work has changed how companies operate globally..."
    ]

    asyncio.run(analyze_documents_streaming(documents))
```

## Example 6: Streaming with Progress Indicators

Add progress indicators for better UX:

```python
import asyncio
import time
from examples.typed_client import SaaSLLMClient

async def streaming_with_progress():
    """Stream with visual progress indicators"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("story_generation")

        print("Generating story...\n")
        print("-" * 60)

        start_time = time.time()
        char_count = 0
        chunk_count = 0

        async for chunk in client.chat_stream(
            job_id=job_id,
            messages=[
                {"role": "user", "content": "Write a short sci-fi story (3 paragraphs)"}
            ],
            temperature=1.0
        ):
            if chunk.choices:
                content = chunk.choices[0].delta.get("content", "")
                if content:
                    char_count += len(content)
                    chunk_count += 1
                    print(content, end="", flush=True)

        elapsed = time.time() - start_time

        print("\n" + "-" * 60)
        print(f"\nStatistics:")
        print(f"  Chunks received: {chunk_count}")
        print(f"  Characters: {char_count}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Speed: {char_count/elapsed:.1f} chars/sec")

        await client.complete_job(job_id, "completed")

if __name__ == "__main__":
    asyncio.run(streaming_with_progress())
```

## Example 7: Error Handling in Streams

Handle errors gracefully during streaming:

```python
import asyncio
from examples.typed_client import SaaSLLMClient
from httpx import HTTPStatusError

async def robust_streaming():
    """Stream with comprehensive error handling"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("resilient_chat")

        try:
            accumulated = ""
            chunk_count = 0

            async for chunk in client.chat_stream(
                job_id=job_id,
                messages=[
                    {"role": "user", "content": "Explain Docker containers"}
                ],
                temperature=0.7
            ):
                if chunk.choices:
                    content = chunk.choices[0].delta.get("content", "")
                    if content:
                        accumulated += content
                        chunk_count += 1
                        print(content, end="", flush=True)

            print(f"\n\nStream completed successfully ({chunk_count} chunks)")
            await client.complete_job(job_id, "completed")

        except HTTPStatusError as e:
            print(f"\n\nHTTP Error: {e.response.status_code}")
            if e.response.status_code == 403:
                print("Insufficient credits or access denied")
            elif e.response.status_code == 429:
                print("Rate limited - please wait and retry")
            await client.complete_job(job_id, "failed")

        except asyncio.TimeoutError:
            print("\n\nStream timed out")
            await client.complete_job(job_id, "failed")

        except Exception as e:
            print(f"\n\nUnexpected error: {e}")
            await client.complete_job(job_id, "failed")

if __name__ == "__main__":
    asyncio.run(robust_streaming())
```

## Example 8: Concurrent Streaming

Stream multiple requests concurrently:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def stream_question(client, job_id, question):
    """Stream answer to one question"""
    print(f"\nQuestion: {question}")
    print("Answer: ", end="", flush=True)

    async for chunk in client.chat_stream(
        job_id=job_id,
        messages=[{"role": "user", "content": question}],
        temperature=0.7
    ):
        if chunk.choices:
            content = chunk.choices[0].delta.get("content", "")
            if content:
                print(content, end="", flush=True)

    print()  # New line

async def concurrent_streaming():
    """Stream answers to multiple questions concurrently"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("faq_batch")

        questions = [
            "What is machine learning?",
            "What is deep learning?",
            "What is neural network?"
        ]

        # Stream all questions concurrently
        tasks = [stream_question(client, job_id, q) for q in questions]
        await asyncio.gather(*tasks)

        result = await client.complete_job(job_id, "completed")
        print(f"\nAll questions answered! Credits: {result.credits_remaining}")

if __name__ == "__main__":
    asyncio.run(concurrent_streaming())
```

## Example 9: Streaming to File

Save streamed response to a file:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def stream_to_file(output_file: str):
    """Stream LLM response directly to file"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("content_generation")

        with open(output_file, 'w') as f:
            async for chunk in client.chat_stream(
                job_id=job_id,
                messages=[
                    {
                        "role": "user",
                        "content": "Write a technical blog post about microservices (500 words)"
                    }
                ],
                temperature=0.8
            ):
                if chunk.choices:
                    content = chunk.choices[0].delta.get("content", "")
                    if content:
                        f.write(content)
                        f.flush()  # Write to disk immediately
                        print(content, end="", flush=True)

        print(f"\n\nContent saved to: {output_file}")
        await client.complete_job(job_id, "completed")

if __name__ == "__main__":
    asyncio.run(stream_to_file("blog_post.txt"))
```

## Example 10: Streaming with Timeout

Set timeouts for long-running streams:

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def streaming_with_timeout(timeout_seconds=30):
    """Stream with timeout protection"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("timeout_demo")

        try:
            # Set timeout for the entire stream
            async with asyncio.timeout(timeout_seconds):
                async for chunk in client.chat_stream(
                    job_id=job_id,
                    messages=[
                        {"role": "user", "content": "Explain blockchain technology"}
                    ]
                ):
                    if chunk.choices:
                        content = chunk.choices[0].delta.get("content", "")
                        if content:
                            print(content, end="", flush=True)

            print(f"\n\nStream completed within {timeout_seconds}s")
            await client.complete_job(job_id, "completed")

        except asyncio.TimeoutError:
            print(f"\n\nStream exceeded {timeout_seconds}s timeout")
            await client.complete_job(job_id, "failed")

if __name__ == "__main__":
    asyncio.run(streaming_with_timeout(30))
```

## Streaming Performance Tips

### 1. Use Async Properly

```python
# ✅ Good - Fully async
async with SaaSLLMClient(...) as client:
    async for chunk in client.chat_stream(...):
        # Process chunk
        pass

# ❌ Bad - Blocking sync call
import requests
response = requests.post(..., stream=True)
for line in response.iter_lines():
    # Blocks entire thread
    pass
```

### 2. Flush Output Immediately

```python
# ✅ Good - Real-time display
print(content, end="", flush=True)

# ❌ Bad - Buffered output
print(content, end="")  # May not display immediately
```

### 3. Handle Empty Chunks

```python
# ✅ Good - Check for content
async for chunk in client.chat_stream(...):
    if chunk.choices:
        content = chunk.choices[0].delta.get("content", "")
        if content:  # Only process non-empty
            print(content, end="", flush=True)

# ❌ Bad - May crash on empty chunks
async for chunk in client.chat_stream(...):
    content = chunk.choices[0].delta["content"]  # KeyError if missing
    print(content, end="", flush=True)
```

### 4. Set Reasonable Timeouts

```python
# ✅ Good - Timeout based on expected length
async with asyncio.timeout(60):  # 60s for long responses
    async for chunk in client.chat_stream(...):
        pass

# ❌ Bad - No timeout (can hang forever)
async for chunk in client.chat_stream(...):
    pass
```

## Common Use Cases

### Use Case 1: Chat Applications

Real-time responses for better UX - users see responses appear character-by-character like ChatGPT.

### Use Case 2: Content Generation

Generate blog posts, articles, or documentation with live preview as it's being written.

### Use Case 3: Code Generation

Stream code as it's generated so developers can start reviewing early.

### Use Case 4: Long-Form Responses

For responses that take >5 seconds, streaming provides much better perceived performance.

## Next Steps

Now that you've seen streaming examples:

1. **[Learn More About Streaming](../integration/streaming.md)** - Detailed streaming guide
2. **[See Basic Examples](basic-usage.md)** - Non-streaming examples
3. **[Try Structured Outputs](structured-outputs.md)** - Type-safe responses
4. **[Review Best Practices](../integration/best-practices.md)** - Production tips

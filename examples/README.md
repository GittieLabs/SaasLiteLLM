# SaaS LiteLLM Client Examples

This directory contains comprehensive examples demonstrating type-safe usage of the SaaS LiteLLM API with full streaming support and Instructor-compatible structured outputs.

## Overview

The examples show how to use the SaaS API with:
- ✅ **Full type safety** using Pydantic models
- ✅ **Streaming support** with Server-Sent Events (SSE)
- ✅ **Instructor-compatible** structured outputs
- ✅ **Low latency** zero-buffering streaming
- ✅ **Complete streaming chain** from UI to LLM provider

## Files

### Core Library

- **`typed_client.py`** - Type-safe Python client for the SaaS API
  - Fully typed request/response models
  - Streaming and non-streaming support
  - Instructor-compatible structured outputs
  - Job lifecycle management

### Basic Examples

- **`example_basic_usage.py`** - Simple chat completion example
  - Creating jobs
  - Making non-streaming calls
  - Completing jobs

- **`example_streaming.py`** - Streaming chat example
  - Real-time response streaming
  - Processing chunks as they arrive
  - Usage tracking

### Structured Output Examples

- **`example_structured_outputs.py`** - Instructor-style typed responses
  - Define Pydantic models for responses
  - Extract structured data (Person, Resume, Sentiment)
  - Type-safe parsing
  - Both streaming and non-streaming structured outputs

### Full Streaming Chain

- **`example_streaming_chain_server.py`** - Client server (middle tier)
  - FastAPI server between UI and SaaS API
  - Forwards streaming responses in real-time
  - Manages authentication and job lifecycle
  - Demonstrates zero-buffering forwarding

- **`example_streaming_chain_ui.html`** - Interactive browser UI
  - Real-time chat interface
  - Connects to client server
  - Shows full streaming chain in action
  - Both streaming and non-streaming modes

## Architecture

The examples demonstrate this architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Streaming Chain                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Browser UI ←─SSE─← Client Server ←─SSE─← SaaS API ←─SSE─← LLM  │
│  (HTML/JS)          (FastAPI:8001)        (FastAPI:8003)         │
│                                                                   │
│  Each hop forwards chunks immediately with zero buffering!       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Setup

### Prerequisites

```bash
# Install dependencies
pip install httpx pydantic fastapi uvicorn

# Ensure SaaS API is running
# (Should already be running on port 8003)
```

### Configuration

Update the virtual key and team ID in the examples:

```python
# In each example file
SAAS_API_URL = "http://localhost:8003"
SAAS_VIRTUAL_KEY = "sk-1234"  # Replace with your actual virtual key
SAAS_TEAM_ID = "team-alpha"   # Replace with your team ID
```

## Running the Examples

### 1. Basic Usage

```bash
cd examples
python example_basic_usage.py
```

**Output:**
```
Creating job...
Job created: 123e4567-e89b-12d3-a456-426614174000

Making chat completion...
Assistant: The capital of France is Paris.

Usage: {'prompt_tokens': 23, 'completion_tokens': 8, 'total_tokens': 31}

Completing job...
Job completed!
```

### 2. Streaming

```bash
python example_streaming.py
```

**Output:**
```
Creating job...
Job created: 456e7890-e89b-12d3-a456-426614174001

Streaming response:
------------------------------------------------------------
Beneath the waves, the ocean roars,
A dance of depths on distant shores...(streams in real-time character by character)
------------------------------------------------------------
Usage: {'prompt_tokens': 25, 'completion_tokens': 156, 'total_tokens': 181}

Full response length: 624 characters

Completing job...
Job completed!
```

### 3. Structured Outputs (Instructor-style)

```bash
python example_structured_outputs.py
```

**Output:**
```
============================================================
Example 1: Simple Person Extraction
============================================================

Extracted Person:
  Name: John Smith
  Age: 35
  Occupation: software engineer

Type: <class '__main__.Person'>

============================================================
Example 2: Resume Parsing
============================================================

Parsed Resume:
  Name: Jane Doe
  Email: jane.doe@email.com
  Phone: (555) 123-4567
  Skills: Python, FastAPI, PostgreSQL, Docker, React, TypeScript
  Experience: 5 years
  Education:
    - BS Computer Science, MIT, 2018
    - MS Artificial Intelligence, Stanford, 2020

(... more examples ...)
```

### 4. Full Streaming Chain (UI → Client Server → SaaS API)

**Step 1: Start the client server**

```bash
python example_streaming_chain_server.py
```

Output:
```
============================================================
Starting Client Server
============================================================
Server will run at: http://localhost:8001
SaaS API: http://localhost:8003
Team: team-alpha

Open example_streaming_chain_ui.html in a browser to test
============================================================

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Step 2: Open the UI in your browser**

```bash
open example_streaming_chain_ui.html
# Or just open the file in any browser
```

**Step 3: Try it out!**

- Type a message in the chat interface
- Toggle between streaming and non-streaming modes
- Watch the response stream in real-time
- See the full chain in action with minimal latency

## Key Features Demonstrated

### 1. Type Safety with Pydantic

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

# Get typed response
person = await client.structured_output(
    model_group="chat-fast",
    messages=[...],
    response_model=Person
)

# Now you have a fully typed Person object!
print(person.name)  # Type-safe access
```

### 2. Zero-Buffering Streaming

```python
# Client Server code
async def stream_to_ui():
    async for chunk in saas_client.chat_stream(...):
        if chunk.choices:
            delta = chunk.choices[0].delta
            if "content" in delta:
                # Forward IMMEDIATELY - no buffering!
                yield f"data: {delta['content']}\n\n"
```

### 3. Instructor Compatibility

The `structured_output()` method works just like Instructor:

```python
# Traditional Instructor pattern
instructor_client = instructor.patch(openai_client)
person = instructor_client.chat.completions.create(
    model="gpt-4",
    response_model=Person,
    messages=[...]
)

# SaaS API equivalent
person = await saas_client.structured_output(
    model_group="chat-fast",
    response_model=Person,
    messages=[...]
)

# Both return fully typed Pydantic models!
```

### 4. Full OpenAI API Compatibility

All OpenAI parameters are supported:

```python
response = await client.chat(
    model_group="chat-fast",
    messages=[...],
    temperature=0.7,
    max_tokens=1000,
    top_p=0.9,
    frequency_penalty=0.5,
    presence_penalty=0.5,
    stop=["END"],
    response_format={"type": "json_object"},  # Structured outputs
    tools=[...],  # Function calling
    tool_choice="auto"
)
```

## Benefits

### For Developers

- ✅ **Type Safety**: Full Pydantic type checking
- ✅ **Familiar Patterns**: Works like Instructor/OpenAI SDK
- ✅ **Streaming**: Real-time responses with low latency
- ✅ **Job Tracking**: All calls tracked in database
- ✅ **Cost Tracking**: Automatic cost calculation

### For System Architecture

- ✅ **Security**: LiteLLM stays internal (not exposed)
- ✅ **Centralized Auth**: Virtual keys managed by SaaS API
- ✅ **Credit System**: Per-team credit allocation
- ✅ **Model Aliases**: Abstract model names from providers
- ✅ **Fallback Support**: Automatic model fallback

## Latency Optimization

The streaming implementation minimizes latency through:

1. **Zero Buffering**: Chunks forwarded immediately at each hop
2. **X-Accel-Buffering Header**: Prevents nginx buffering
3. **Async Streaming**: Non-blocking async generators
4. **Direct Forwarding**: No intermediate processing/parsing

**Result**: Near-identical latency to direct LiteLLM access!

## Use Cases

### 1. Chat Applications
Use the full streaming chain for real-time chat UIs

### 2. Agent Systems
Use the typed client for Pydantic AI agents with structured outputs

### 3. Data Extraction
Use structured outputs to extract typed data from unstructured text

### 4. Multi-Modal Apps
Use the client server pattern to support web, mobile, and desktop clients

## Troubleshooting

### Client server can't connect to SaaS API

Make sure the SaaS API is running on port 8003:
```bash
# Check if port 8003 is in use
lsof -i :8003
```

### Virtual key authentication fails

Make sure you've created the team and have the correct virtual key:
```bash
# Check team credentials
curl http://localhost:8003/api/teams \
  -H "Authorization: Bearer your-virtual-key"
```

### Streaming not working

Check the client server logs and ensure:
- No buffering proxies between components
- `X-Accel-Buffering: no` header is set
- Using async generators (not sync)

## Next Steps

1. **Modify the examples** to use your actual model groups and teams
2. **Integrate into your application** using the typed client
3. **Build your own client server** for your specific use case
4. **Create custom Pydantic models** for your domain

## Additional Resources

- **SaaS API Documentation**: `STREAMING_IMPLEMENTATION_PLAN.md`
- **Suspend Feature Guide**: `SUSPEND_FEATURE_GUIDE.md`
- **Main README**: `../README.md`

---

**Happy coding with type-safe, streaming LLM calls!**

# Best Practices

Learn best practices for building robust, secure, and cost-effective applications with SaaS LiteLLM.

## Overview

This guide covers:
- **Workflow Selection** - Choose the right endpoint for your use case
- **Performance Optimization** - Reduce latency and improve throughput
- **Security Best Practices** - Protect your application and data
- **Cost Optimization** - Minimize LLM costs
- **Development Practices** - Write maintainable code
- **Production Readiness** - Deploy with confidence

## Workflow Selection

### Choose the Right Endpoint

SaaS LiteLLM offers two workflow patterns optimized for different use cases:

#### 1. Single-Call Workflow (`/api/jobs/create-and-call`)

**✅ Use When:**
- Your workflow requires only ONE LLM call
- You need minimal latency (chat apps, real-time responses)
- Simplicity is important
- You want automatic error handling

**Example Use Cases:**
```python
# Chat applications
response = requests.post(f"{API}/jobs/create-and-call", json={
    "team_id": "acme-corp",
    "job_type": "chat",
    "model": "gpt-4",
    "messages": [{"role": "user", "content": user_message}]
})

# Simple classification
response = requests.post(f"{API}/jobs/create-and-call", json={
    "team_id": "acme-corp",
    "job_type": "sentiment_analysis",
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": f"Classify sentiment: {text}"}]
})

# Single-turn text generation
response = requests.post(f"{API}/jobs/create-and-call", json={
    "team_id": "acme-corp",
    "job_type": "summarization",
    "model": "gpt-4",
    "messages": [{"role": "user", "content": f"Summarize: {document}"}]
})
```

**Performance:** 1 API call ~1.5s

#### 2. Multi-Step Workflow (Create → Call → Complete)

**✅ Use When:**
- Your workflow requires MULTIPLE LLM calls
- You need granular control over each step
- You want to track intermediate results
- Building complex agentic workflows

**Example Use Cases:**
```python
# Multi-step document analysis
job_id = create_job("document_analysis")
extract_text(job_id)      # Call 1
classify_content(job_id)  # Call 2
generate_summary(job_id)  # Call 3
complete_job(job_id)

# Agentic workflow with decisions
job_id = create_job("research_agent")
initial_response = llm_call(job_id, "Research topic X")
if needs_more_info(initial_response):
    deep_dive = llm_call(job_id, "Deep dive into...")
final_report = llm_call(job_id, "Compile report from...")
complete_job(job_id)

# Batch processing with retry logic
job_id = create_job("batch_processing")
for item in items:
    try:
        llm_call(job_id, process_prompt(item))
    except:
        retry_with_fallback(job_id, item)
complete_job(job_id)
```

**Performance:** 3+ API calls ~4.5s+

### Decision Tree

```
Does your workflow require multiple LLM calls?
├─ NO  → Use /api/jobs/create-and-call (faster, simpler)
└─ YES → Use Create → Call → Complete (more control)
   ├─ Sequential processing needed? → Multi-step
   ├─ Need to track intermediate results? → Multi-step
   └─ Complex agent logic? → Multi-step
```

### Performance Comparison

| Metric | Single-Call | Multi-Step |
|--------|------------|------------|
| API Calls | 1 | 3+ |
| Latency | ~1.5s | ~4.5s+ |
| Code Complexity | Low | Medium |
| Error Handling | Automatic | Manual |
| Best For | Chat, simple tasks | Agents, complex workflows |

## Performance Optimization

### 1. Use Streaming for Interactive Applications

**❌ Non-Streaming (Perceived Latency: ~2000ms)**
```python
response = await client.chat(job_id, messages)
print(response.choices[0].message["content"])
```

**✅ Streaming (Perceived Latency: ~300-500ms)**
```python
async for chunk in client.chat_stream(job_id, messages):
    if chunk.choices:
        content = chunk.choices[0].delta.get("content", "")
        print(content, end="", flush=True)
```

**When to use each:**
- **Streaming**: Chat apps, real-time generation, long responses
- **Non-streaming**: Batch processing, structured outputs, simple tasks

### 2. Reuse Jobs for Related Calls

Group related LLM calls into a single job:

**✅ Good - One job, multiple calls**
```python
job_id = await client.create_job("document_analysis")

# All related calls in one job
extract_text(job_id)
classify_content(job_id)
generate_summary(job_id)

await client.complete_job(job_id, "completed")
# Cost: 1 credit
```

**❌ Bad - Separate jobs**
```python
# Creates unnecessary overhead
job1 = await client.create_job("extract")
extract_text(job1)
await client.complete_job(job1, "completed")

job2 = await client.create_job("classify")
classify_content(job2)
await client.complete_job(job2, "completed")
# Cost: 2 credits
```

### 3. Set Reasonable Timeouts

```python
# ✅ Good - Set appropriate timeout
response = requests.post(
    url,
    json=data,
    timeout=30  # 30 seconds
)

# ❌ Bad - No timeout (can hang forever)
response = requests.post(url, json=data)
```

**Recommended Timeouts:**
- Non-streaming calls: 30-60 seconds
- Streaming calls: 60-120 seconds
- Simple requests: 10-30 seconds

### 4. Use Async for Concurrency

**✅ Good - Async allows concurrent operations**
```python
import asyncio

async def process_batch(documents):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("batch_processing")

        # Process documents concurrently
        tasks = [
            analyze_document(client, job_id, doc)
            for doc in documents
        ]
        results = await asyncio.gather(*tasks)

        await client.complete_job(job_id, "completed")
        return results
```

**❌ Bad - Sequential processing**
```python
def process_batch_sync(documents):
    results = []
    for doc in documents:
        result = analyze_document_sync(doc)
        results.append(result)
    return results
```

### 5. Cache Common Requests

Implement application-level caching for frequently repeated requests:

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(prompt: str):
    """Cache responses for identical prompts"""
    # Make LLM call
    response = make_llm_call(prompt)
    return response

# Usage
response = get_cached_response("What is Python?")  # First call
response = get_cached_response("What is Python?")  # Cached!
```

!!! note "Redis Caching"
    SaaS LiteLLM automatically caches responses in Redis. Application-level caching is an additional optimization.

### 6. Batch Similar Requests

When possible, batch similar requests together:

```python
async def batch_classify(texts):
    """Classify multiple texts in one call"""
    job_id = await client.create_job("batch_classification")

    # Combine into single prompt
    prompt = "Classify each of these texts as positive/negative/neutral:\n\n"
    for i, text in enumerate(texts, 1):
        prompt += f"{i}. {text}\n"

    response = await client.chat(job_id, [
        {"role": "user", "content": prompt}
    ])

    await client.complete_job(job_id, "completed")
    # Parse response for individual classifications
    return parse_batch_response(response)
```

### 7. Use Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session():
    """Create session with connection pooling and retries"""
    session = requests.Session()

    # Connection pooling
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# Reuse session across requests
session = create_session()
response = session.post(url, json=data, headers=headers)
```

## Security Best Practices

### 1. Never Hardcode API Keys

**❌ Bad - Hardcoded keys**
```python
VIRTUAL_KEY = "sk-1234567890abcdef"  # DON'T DO THIS!
```

**✅ Good - Environment variables**
```python
import os

VIRTUAL_KEY = os.environ.get("SAAS_LITELLM_VIRTUAL_KEY")
if not VIRTUAL_KEY:
    raise ValueError("SAAS_LITELLM_VIRTUAL_KEY not set")
```

### 2. Use HTTPS in Production

**❌ Development only**
```python
API_URL = "http://localhost:8003/api"
```

**✅ Production**
```python
API_URL = os.environ.get(
    "SAAS_API_URL",
    "https://api.your-saas.com/api"  # Always HTTPS
)
```

### 3. Rotate Keys Regularly

```python
# Implement key rotation
def rotate_virtual_key():
    """Rotate virtual key every 30 days"""
    # 1. Create new team or regenerate key
    # 2. Update environment variables
    # 3. Test new key
    # 4. Deactivate old key
    pass
```

**Rotation Schedule:**
- Development: Every 90 days
- Production: Every 30-60 days
- After security incidents: Immediately

### 4. Separate Keys Per Environment

```bash
# .env.development
SAAS_LITELLM_VIRTUAL_KEY=sk-dev-key-here
SAAS_API_URL=http://localhost:8003/api

# .env.production
SAAS_LITELLM_VIRTUAL_KEY=sk-prod-key-here
SAAS_API_URL=https://api.your-saas.com/api
```

### 5. Validate and Sanitize User Input

```python
def sanitize_user_input(text: str) -> str:
    """Sanitize user input before sending to LLM"""
    # Remove excessive whitespace
    text = " ".join(text.split())

    # Limit length
    MAX_LENGTH = 10000
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH]

    # Remove potentially harmful content
    # (implement based on your use case)

    return text

# Usage
user_message = sanitize_user_input(request.data["message"])
```

### 6. Implement Rate Limiting

Protect your application from abuse:

```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    """Simple rate limiter"""

    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def allow_request(self, user_id: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Remove old requests
        self.requests[user_id] = [
            ts for ts in self.requests[user_id]
            if ts > cutoff
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Allow request
        self.requests[user_id].append(now)
        return True

# Usage
limiter = RateLimiter(max_requests=10, window_seconds=60)

if not limiter.allow_request(user_id):
    raise Exception("Rate limit exceeded")
```

### 7. Log Security Events

```python
import logging

logger = logging.getLogger(__name__)

def log_security_event(event_type: str, details: dict):
    """Log security-relevant events"""
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            **details
        }
    )

# Usage
if response.status_code == 401:
    log_security_event("authentication_failed", {
        "team_id": team_id,
        "ip_address": request.client.host
    })
```

## Cost Optimization

### 1. Use Lower-Cost Models When Possible

```python
# Use cheaper models for simple tasks
TASK_MODELS = {
    "simple_classification": "gpt-3.5-turbo",  # Cheaper
    "complex_analysis": "gpt-4",               # More expensive
    "code_generation": "gpt-4",                # More expensive
}

model = TASK_MODELS.get(task_type, "gpt-3.5-turbo")
```

### 2. Set Max Tokens to Avoid Runaway Costs

```python
# ✅ Good - Limit response length
response = await client.chat(
    job_id,
    messages,
    max_tokens=500  # Limit response
)

# ❌ Bad - Unlimited response
response = await client.chat(job_id, messages)
```

### 3. Monitor and Alert on High Usage

```python
def check_credit_balance(team_id: str):
    """Alert when credits are low"""
    response = requests.get(
        f"{API_URL}/teams/{team_id}",
        headers=headers
    )
    team = response.json()

    credits_remaining = team["credits_remaining"]
    credits_allocated = team["credits_allocated"]

    # Alert at 20% remaining
    if credits_remaining < credits_allocated * 0.2:
        send_low_credit_alert(team_id, credits_remaining)

    # Alert at 10% remaining
    if credits_remaining < credits_allocated * 0.1:
        send_critical_credit_alert(team_id, credits_remaining)
```

### 4. Use Caching Strategically

Leverage Redis caching for repeated queries:

```python
# Identical requests are automatically cached
response1 = await client.chat(job_id, messages)  # Cache miss
response2 = await client.chat(job_id, messages)  # Cache hit (no cost!)
```

### 5. Optimize Prompts for Efficiency

**❌ Inefficient - Verbose prompt**
```python
prompt = """
Please analyze the following text and provide a comprehensive summary
including all the key points, important details, and main conclusions.
Make sure to cover every aspect thoroughly and provide deep insights
into the content...

[long text]
"""
```

**✅ Efficient - Concise prompt**
```python
prompt = """
Summarize the key points:

[long text]
"""
```

### 6. Track Costs Per Feature

```python
def track_feature_cost(feature: str, actual_cost: float):
    """Track costs per feature for optimization"""
    # Log to analytics/metrics system
    metrics.record("feature_cost", actual_cost, tags={"feature": feature})

# Usage
result = await client.complete_job(job_id, "completed")
actual_cost = result.costs.get("total_cost_usd", 0)
track_feature_cost("document_analysis", actual_cost)
```

### 7. Implement Job Timeouts

Prevent jobs from running indefinitely:

```python
async def process_with_timeout(job_id, max_duration_seconds=300):
    """Process job with timeout"""
    try:
        async with asyncio.timeout(max_duration_seconds):
            # Process job
            result = await process_job(job_id)
            await client.complete_job(job_id, "completed")
            return result
    except asyncio.TimeoutError:
        # Mark as failed to avoid credit charge
        await client.complete_job(job_id, "failed")
        raise
```

## Development Practices

### 1. Use Type Hints

```python
from typing import List, Dict, Optional

async def analyze_documents(
    documents: List[str],
    team_id: str,
    options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Analyze multiple documents"""
    # Implementation with clear types
    pass
```

### 2. Write Comprehensive Tests

```python
import pytest

@pytest.mark.asyncio
async def test_document_analysis():
    """Test document analysis workflow"""
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("test_analysis")

        response = await client.chat(
            job_id,
            [{"role": "user", "content": "Test input"}]
        )

        assert response.choices[0].message["content"]

        result = await client.complete_job(job_id, "completed")
        assert result.costs.credits_remaining >= 0
```

### 3. Use Context Managers

```python
# ✅ Good - Automatic cleanup
async with SaaSLLMClient(...) as client:
    # Client is automatically closed

# ❌ Bad - Manual cleanup
client = SaaSLLMClient(...)
try:
    # Use client
    pass
finally:
    await client.close()
```

### 4. Handle Partial Failures

```python
async def process_batch_with_partial_failure(documents):
    """Process batch even if some fail"""
    results = []
    failures = []

    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("batch_processing")

        for doc in documents:
            try:
                result = await process_document(client, job_id, doc)
                results.append(result)
            except Exception as e:
                failures.append({"document": doc, "error": str(e)})
                logger.error(f"Failed to process document: {e}")

        # Complete job even with partial failures
        status = "completed" if len(results) > 0 else "failed"
        await client.complete_job(job_id, status)

    return {
        "results": results,
        "failures": failures,
        "success_rate": len(results) / len(documents)
    }
```

### 5. Use Structured Logging

```python
import logging
import json

logger = logging.getLogger(__name__)

def log_api_call(job_id: str, endpoint: str, latency_ms: float, success: bool):
    """Log API calls with structured data"""
    logger.info(
        "API call completed",
        extra={
            "job_id": job_id,
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
    )
```

### 6. Implement Health Checks

```python
async def check_api_health() -> bool:
    """Check if SaaS API is healthy"""
    try:
        response = requests.get(
            f"{API_URL.replace('/api', '')}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

# Run health checks periodically
if not await check_api_health():
    alert_ops_team("SaaS API is unhealthy")
```

## Production Readiness

### 1. Use Environment-Specific Configuration

```python
import os

class Config:
    """Environment-specific configuration"""

    def __init__(self):
        self.env = os.environ.get("ENVIRONMENT", "development")

        if self.env == "production":
            self.api_url = os.environ["SAAS_API_URL"]
            self.virtual_key = os.environ["SAAS_LITELLM_VIRTUAL_KEY"]
            self.timeout = 60
            self.max_retries = 3
        else:
            self.api_url = "http://localhost:8003/api"
            self.virtual_key = os.environ.get("SAAS_LITELLM_VIRTUAL_KEY", "dev-key")
            self.timeout = 30
            self.max_retries = 1

config = Config()
```

### 2. Implement Circuit Breakers

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """Prevent cascading failures"""

    def __init__(self, failure_threshold=5, timeout_seconds=60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker"""
        if self.state == "open":
            # Check if timeout has passed
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            # Success - reset
            self.failure_count = 0
            self.state = "closed"
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise
```

### 3. Monitor Key Metrics

```python
import prometheus_client as prom

# Define metrics
request_count = prom.Counter(
    'saas_llm_requests_total',
    'Total number of requests',
    ['endpoint', 'status']
)

request_latency = prom.Histogram(
    'saas_llm_request_duration_seconds',
    'Request latency',
    ['endpoint']
)

credits_remaining = prom.Gauge(
    'saas_llm_credits_remaining',
    'Credits remaining',
    ['team_id']
)

# Use metrics
request_count.labels(endpoint='/llm-call', status='success').inc()
```

### 4. Implement Graceful Degradation

```python
async def get_response_with_fallback(prompt: str) -> str:
    """Get LLM response with fallback"""
    try:
        # Try primary model
        response = await client.chat(job_id, messages)
        return response.choices[0].message["content"]

    except Exception as e:
        logger.warning(f"Primary model failed: {e}")

        try:
            # Fallback to cached response
            cached = get_cached_response(prompt)
            if cached:
                return cached
        except:
            pass

        # Final fallback to default response
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
```

## Summary Checklist

### Performance
- [ ] Use streaming for interactive applications
- [ ] Reuse jobs for related calls
- [ ] Set reasonable timeouts
- [ ] Use async for concurrency
- [ ] Implement caching
- [ ] Batch similar requests
- [ ] Use connection pooling

### Security
- [ ] Never hardcode API keys
- [ ] Use HTTPS in production
- [ ] Rotate keys regularly
- [ ] Separate keys per environment
- [ ] Validate user input
- [ ] Implement rate limiting
- [ ] Log security events

### Cost
- [ ] Use appropriate models
- [ ] Set max_tokens limits
- [ ] Monitor credit usage
- [ ] Leverage caching
- [ ] Optimize prompts
- [ ] Track costs per feature
- [ ] Implement job timeouts

### Development
- [ ] Use type hints
- [ ] Write comprehensive tests
- [ ] Use context managers
- [ ] Handle partial failures
- [ ] Use structured logging
- [ ] Implement health checks

### Production
- [ ] Environment-specific config
- [ ] Circuit breakers
- [ ] Monitor metrics
- [ ] Graceful degradation
- [ ] Error tracking
- [ ] Alerting system

## Next Steps

Now that you understand best practices:

1. **[Try the Examples](../examples/basic-usage.md)** - See best practices in action
2. **[Review Error Handling](error-handling.md)** - Comprehensive error handling
3. **[Deploy to Production](../deployment/railway.md)** - Production deployment guide
4. **[Monitor Your Application](../testing/overview.md)** - Testing and monitoring

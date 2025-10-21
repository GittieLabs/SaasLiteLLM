# Error Handling

Learn how to handle errors gracefully when integrating with the SaaS LiteLLM API.

## Overview

Proper error handling is critical for building robust applications. This guide covers all possible errors, their causes, and how to handle them.

**Error Categories:**
- Authentication errors (401, 403)
- Client errors (400, 404, 422)
- Rate limiting (429)
- Server errors (500, 503)
- Network errors (timeouts, connection failures)
- Streaming errors (interrupted streams)

## HTTP Status Codes

### 400 Bad Request

**Cause:** Invalid request format or parameters

**Example:**
```json
{
  "detail": "Invalid message format"
}
```

**Common Causes:**
- Missing required fields
- Invalid message structure
- Unsupported parameters
- Invalid JSON format

**Solution:**
```python
try:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        error_detail = e.response.json()
        print(f"Bad request: {error_detail['detail']}")
        # Fix the request format
        # Log the issue for debugging
```

### 401 Unauthorized

**Cause:** Invalid or missing virtual key

**Example:**
```json
{
  "detail": "Invalid or missing API key"
}
```

**Common Causes:**
- Missing `Authorization` header
- Invalid virtual key format
- Virtual key doesn't exist
- Expired or revoked key

**Solution:**
```python
try:
    response = requests.post(
        f"{API_URL}/jobs/create",
        headers={"Authorization": f"Bearer {VIRTUAL_KEY}"},
        json={"team_id": "acme-corp", "job_type": "test"}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed. Check your virtual key.")
        # Attempt to refresh the key
        # Notify admin
        # Fall back to cached data if possible
```

[:octicons-arrow-right-24: Learn more about authentication](authentication.md)

### 403 Forbidden

**Cause:** Team suspended, insufficient credits, or access denied

**Example:**
```json
{
  "detail": "Team suspended or insufficient credits"
}
```

**Common Causes:**
- Team has been suspended by admin
- Team has run out of credits
- Team doesn't have access to the requested model
- Team is in "pause" mode

**Solution:**
```python
try:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        error_detail = e.response.json()
        print(f"Access denied: {error_detail['detail']}")

        # Check team status
        team_response = requests.get(
            f"{API_URL}/teams/{team_id}",
            headers=headers
        )
        team_info = team_response.json()

        if team_info['status'] == 'suspended':
            print("Team is suspended. Contact administrator.")
        elif team_info['credits_remaining'] <= 0:
            print("Out of credits. Please add credits to continue.")
        else:
            print("Model access denied. Check access groups.")
```

### 404 Not Found

**Cause:** Job, team, or resource doesn't exist

**Example:**
```json
{
  "detail": "Job not found"
}
```

**Common Causes:**
- Invalid job_id
- Job was deleted
- Wrong team_id
- Typo in endpoint URL

**Solution:**
```python
try:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print(f"Job {job_id} not found")
        # Create a new job
        job = create_new_job()
        # Retry with the new job_id
```

### 422 Unprocessable Entity

**Cause:** Request validation failed

**Example:**
```json
{
  "detail": [
    {
      "loc": ["body", "messages"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Common Causes:**
- Missing required fields
- Invalid field types
- Validation errors on request data

**Solution:**
```python
try:
    response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={"team_id": "acme-corp"}  # Missing job_type
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 422:
        errors = e.response.json()['detail']
        for error in errors:
            field = '.'.join(str(x) for x in error['loc'])
            print(f"Validation error on {field}: {error['msg']}")
```

### 429 Too Many Requests

**Cause:** Rate limit exceeded

**Example:**
```json
{
  "detail": "Rate limit exceeded"
}
```

**Common Causes:**
- Too many requests per minute (RPM limit)
- Too many tokens per minute (TPM limit)
- Burst limit exceeded

**Solution:**
```python
import time

def make_request_with_retry(url, headers, data, max_retries=3):
    """Make request with exponential backoff for rate limits"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print("Rate limit exceeded after all retries")
                    raise
            else:
                raise
```

### 500 Internal Server Error

**Cause:** Server-side error

**Example:**
```json
{
  "detail": "Internal server error"
}
```

**Common Causes:**
- Unexpected server-side error
- Database connection issue
- LiteLLM proxy unavailable

**Solution:**
```python
try:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 500:
        print("Server error. Retrying...")
        # Retry with exponential backoff
        time.sleep(5)
        # Retry the request
```

### 503 Service Unavailable

**Cause:** Service temporarily unavailable

**Example:**
```json
{
  "detail": "Service temporarily unavailable"
}
```

**Common Causes:**
- Service maintenance
- Server overload
- Dependency unavailable

**Solution:**
```python
try:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages}
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 503:
        print("Service unavailable. Please try again later.")
        # Implement retry with longer delays
```

## Network Errors

### Connection Errors

```python
import requests
from requests.exceptions import ConnectionError, Timeout

try:
    response = requests.post(
        f"{API_URL}/jobs/create",
        headers=headers,
        json={"team_id": "acme-corp", "job_type": "test"},
        timeout=30  # 30 second timeout
    )
except ConnectionError as e:
    print(f"Connection error: {e}")
    # Check network connectivity
    # Retry with different endpoint if available
except Timeout as e:
    print(f"Request timed out: {e}")
    # Retry with longer timeout
```

### Timeout Errors

```python
try:
    response = requests.post(
        f"{API_URL}/jobs/{job_id}/llm-call",
        headers=headers,
        json={"messages": messages},
        timeout=30
    )
except Timeout:
    print("Request timed out after 30 seconds")
    # Increase timeout
    # Or switch to streaming for long responses
```

## Streaming Errors

### Interrupted Streams

```python
import asyncio

async def robust_streaming():
    async with SaaSLLMClient(base_url, team_id, virtual_key) as client:
        job_id = await client.create_job("chat")

        try:
            accumulated = ""
            chunk_count = 0

            async for chunk in client.chat_stream(
                job_id=job_id,
                messages=[{"role": "user", "content": "Tell me a story"}]
            ):
                chunk_count += 1
                if chunk.choices:
                    content = chunk.choices[0].delta.get("content", "")
                    accumulated += content
                    print(content, end="", flush=True)

            print(f"\n\nStream completed successfully ({chunk_count} chunks)")
            await client.complete_job(job_id, "completed")

        except asyncio.TimeoutError:
            print("\n\nStream timed out")
            await client.complete_job(job_id, "failed")

        except Exception as e:
            print(f"\n\nStream error: {e}")
            await client.complete_job(job_id, "failed")

            # Log the partial response
            if accumulated:
                print(f"Partial response received: {accumulated[:100]}...")
```

### Stream Timeout

```python
import asyncio

async def streaming_with_timeout():
    async with SaaSLLMClient(base_url, team_id, virtual_key) as client:
        job_id = await client.create_job("chat")

        try:
            # Set overall timeout for the stream
            async with asyncio.timeout(60):  # 60 seconds
                async for chunk in client.chat_stream(
                    job_id=job_id,
                    messages=[{"role": "user", "content": "Write a long essay"}]
                ):
                    # Process chunks
                    pass

        except asyncio.TimeoutError:
            print("Stream exceeded 60 second timeout")
            await client.complete_job(job_id, "failed")
```

## Comprehensive Error Handler

Here's a complete error handling utility:

```python
import requests
import time
from typing import Optional, Dict, Any

class APIError(Exception):
    """Base exception for API errors"""
    pass

class AuthenticationError(APIError):
    """Authentication failed"""
    pass

class InsufficientCreditsError(APIError):
    """Team out of credits"""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded"""
    pass

class ServerError(APIError):
    """Server-side error"""
    pass

def make_api_request(
    url: str,
    headers: Dict[str, str],
    data: Dict[str, Any],
    max_retries: int = 3,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make API request with comprehensive error handling and retries.

    Args:
        url: API endpoint URL
        headers: Request headers
        data: Request body
        max_retries: Maximum number of retries
        timeout: Request timeout in seconds

    Returns:
        API response data

    Raises:
        AuthenticationError: If authentication fails
        InsufficientCreditsError: If team is out of credits
        RateLimitError: If rate limit exceeded after retries
        ServerError: If server error after retries
        APIError: For other API errors
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            print(f"Request timed out (attempt {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                raise APIError("Request timed out after all retries")
            time.sleep(2 ** attempt)

        except requests.exceptions.ConnectionError as e:
            print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise APIError(f"Connection failed after all retries: {e}")
            time.sleep(2 ** attempt)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            detail = e.response.json().get("detail", "Unknown error")

            # 401: Authentication error (don't retry)
            if status_code == 401:
                raise AuthenticationError(f"Authentication failed: {detail}")

            # 403: Forbidden (don't retry)
            elif status_code == 403:
                if "credit" in detail.lower():
                    raise InsufficientCreditsError(f"Insufficient credits: {detail}")
                else:
                    raise APIError(f"Access denied: {detail}")

            # 404: Not found (don't retry)
            elif status_code == 404:
                raise APIError(f"Resource not found: {detail}")

            # 422: Validation error (don't retry)
            elif status_code == 422:
                raise APIError(f"Validation error: {detail}")

            # 429: Rate limit (retry with backoff)
            elif status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise RateLimitError(f"Rate limit exceeded after all retries: {detail}")

            # 500/503: Server errors (retry with backoff)
            elif status_code in [500, 503]:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Server error. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise ServerError(f"Server error after all retries: {detail}")

            # Other errors
            else:
                raise APIError(f"HTTP {status_code}: {detail}")

    raise APIError("Request failed after all retries")

# Usage
try:
    result = make_api_request(
        url=f"{API_URL}/jobs/create",
        headers={"Authorization": f"Bearer {VIRTUAL_KEY}"},
        data={"team_id": "acme-corp", "job_type": "test"}
    )
    print(f"Job created: {result['job_id']}")

except AuthenticationError as e:
    print(f"Auth error: {e}")
    # Refresh virtual key or notify admin

except InsufficientCreditsError as e:
    print(f"Credits error: {e}")
    # Notify user to add credits

except RateLimitError as e:
    print(f"Rate limit error: {e}")
    # Queue request for later

except ServerError as e:
    print(f"Server error: {e}")
    # Log error and notify ops team

except APIError as e:
    print(f"API error: {e}")
    # Generic error handling
```

## Logging and Monitoring

### Structured Logging

```python
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def make_logged_request(url, headers, data):
    """Make request with detailed logging"""
    request_id = str(uuid.uuid4())

    logger.info(f"Request {request_id}: POST {url}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        logger.info(f"Request {request_id}: Success (status={response.status_code})")
        return response.json()

    except requests.exceptions.HTTPError as e:
        logger.error(
            f"Request {request_id}: HTTP error",
            extra={
                "status_code": e.response.status_code,
                "detail": e.response.json().get("detail", "Unknown"),
                "url": url
            }
        )
        raise

    except Exception as e:
        logger.error(
            f"Request {request_id}: Failed",
            extra={"error": str(e), "url": url}
        )
        raise
```

### Metrics Tracking

```python
import time
from collections import defaultdict

class APIMetrics:
    """Track API metrics"""

    def __init__(self):
        self.requests = defaultdict(int)
        self.errors = defaultdict(int)
        self.latencies = []

    def record_request(self, endpoint: str, latency_ms: float, success: bool):
        """Record a request"""
        self.requests[endpoint] += 1
        self.latencies.append(latency_ms)

        if not success:
            self.errors[endpoint] += 1

    def get_stats(self):
        """Get aggregated stats"""
        total_requests = sum(self.requests.values())
        total_errors = sum(self.errors.values())
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": sorted(self.latencies)[int(len(self.latencies) * 0.95)] if self.latencies else 0
        }

# Usage
metrics = APIMetrics()

def make_tracked_request(url, headers, data):
    """Make request with metrics tracking"""
    start_time = time.time()
    success = False

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        success = True
        return response.json()

    finally:
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_request(url, latency_ms, success)

# Later, check metrics
stats = metrics.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Error rate: {stats['error_rate']:.2%}")
print(f"Avg latency: {stats['avg_latency_ms']:.0f}ms")
```

## Response Type Definitions

Understanding the structure of API responses helps with proper error handling and data extraction.

### Success Response Structure

```typescript
// Jobs API - Create Job
{
  "job_id": string,           // UUID
  "status": "pending",
  "created_at": string        // ISO 8601 timestamp
}

// Jobs API - Complete Job
{
  "job_id": string,
  "status": "completed" | "failed",
  "completed_at": string,
  "costs": {
    "total_calls": number,
    "successful_calls": number,
    "failed_calls": number,
    "total_tokens": number,
    "total_cost_usd": number,
    "avg_latency_ms": number,
    "credit_applied": boolean,
    "credits_remaining": number
  },
  "calls": Array<{
    "call_id": string,
    "purpose": string,
    "model_group": string,
    "tokens": number,
    "latency_ms": number,
    "error": string | null
  }>
}

// Jobs API - Single-Call Job
{
  "job_id": string,
  "status": "completed",
  "response": {
    "content": string,
    "finish_reason": "stop" | "length" | "content_filter"
  },
  "metadata": {
    "tokens_used": number,
    "latency_ms": number,
    "model": string
  },
  "costs": { /* same as Complete Job */ },
  "completed_at": string
}

// LLM Calls API
{
  "call_id": string,
  "response": {
    "content": string,
    "finish_reason": string
  },
  "metadata": {
    "tokens_used": number,
    "latency_ms": number,
    "model_group": string
  }
}
```

### Error Response Structure

All error responses follow this format:

```typescript
{
  "detail": string | Array<ValidationError>
}

// Validation errors (422 status)
{
  "detail": [
    {
      "loc": Array<string | number>,  // Field path
      "msg": string,                   // Error message
      "type": string                   // Error type
    }
  ]
}
```

**Examples:**

```json
// 401 Unauthorized
{
  "detail": "Invalid or missing API key"
}

// 403 Forbidden
{
  "detail": "Team suspended or insufficient credits"
}

// 404 Not Found
{
  "detail": "Job not found"
}

// 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "messages"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

// 429 Rate Limit
{
  "detail": "Rate limit exceeded"
}

// 500 Server Error
{
  "detail": "Internal server error"
}
```

## Retry Best Practices

### When to Retry

**Retry these errors:**
- ✅ 429 (Rate Limit) - Always retry with exponential backoff
- ✅ 500 (Internal Server Error) - Retry up to 3 times
- ✅ 503 (Service Unavailable) - Retry with longer delays
- ✅ Network timeouts - Retry with increased timeout
- ✅ Connection errors - Retry with exponential backoff

**Do NOT retry these errors:**
- ❌ 400 (Bad Request) - Fix the request format
- ❌ 401 (Unauthorized) - Check authentication
- ❌ 403 (Forbidden) - Check permissions/credits
- ❌ 404 (Not Found) - Resource doesn't exist
- ❌ 422 (Validation Error) - Fix validation issues

### Exponential Backoff Strategy

**Recommended Configuration:**

| Attempt | Wait Time | Total Time Elapsed |
|---------|-----------|-------------------|
| 1 | 0s (immediate) | 0s |
| 2 | 1s | 1s |
| 3 | 2s | 3s |
| 4 | 4s | 7s |
| 5 | 8s | 15s |

**Implementation:**

```python
import time
import random

def exponential_backoff_with_jitter(attempt: int, base_delay: float = 1.0, max_delay: float = 32.0) -> float:
    """
    Calculate exponential backoff with jitter.

    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds with random jitter
    """
    # Exponential: base_delay * 2^attempt
    delay = min(base_delay * (2 ** attempt), max_delay)

    # Add jitter (±25% random variation)
    jitter = delay * 0.25 * (2 * random.random() - 1)

    return delay + jitter

def make_request_with_smart_retry(
    url: str,
    headers: dict,
    data: dict,
    max_retries: int = 3,
    timeout: int = 30
) -> dict:
    """
    Make API request with intelligent retry logic.

    Retries:
    - 429 (Rate Limit): Up to max_retries with exponential backoff
    - 500/503 (Server errors): Up to max_retries with exponential backoff
    - Timeouts/Connection errors: Up to max_retries with exponential backoff

    Does NOT retry:
    - 400, 401, 403, 404, 422: Client errors that won't be fixed by retrying
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                delay = exponential_backoff_with_jitter(attempt)
                print(f"Timeout. Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise APIError("Request timed out after all retries")

        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                delay = exponential_backoff_with_jitter(attempt)
                print(f"Connection error. Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise APIError("Connection failed after all retries")

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            detail = e.response.json().get("detail", "Unknown error")

            # Don't retry client errors (4xx except 429)
            if 400 <= status_code < 500 and status_code != 429:
                if status_code == 401:
                    raise AuthenticationError(f"Authentication failed: {detail}")
                elif status_code == 403:
                    raise APIError(f"Forbidden: {detail}")
                elif status_code == 404:
                    raise APIError(f"Not found: {detail}")
                elif status_code == 422:
                    raise APIError(f"Validation error: {detail}")
                else:
                    raise APIError(f"Client error {status_code}: {detail}")

            # Retry 429 and 5xx errors
            if attempt < max_retries - 1:
                delay = exponential_backoff_with_jitter(attempt)
                print(f"HTTP {status_code}. Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                if status_code == 429:
                    raise RateLimitError(f"Rate limit exceeded: {detail}")
                else:
                    raise ServerError(f"Server error {status_code}: {detail}")

    raise APIError("Request failed after all retries")
```

### Timeout Configuration

**Recommended Timeouts by Endpoint:**

| Endpoint | Recommended Timeout | Notes |
|----------|-------------------|-------|
| `/api/jobs/create` | 10s | Fast operation |
| `/api/jobs/{id}` (GET) | 10s | Fast operation |
| `/api/jobs/{id}/llm-call` | 60s | LLM calls can be slow |
| `/api/jobs/{id}/complete` | 30s | Aggregation + DB writes |
| `/api/jobs/create-and-call` | 60s | Includes LLM call |
| Streaming endpoints | 120s | Long-running operations |

**Example with endpoint-specific timeouts:**

```python
ENDPOINT_TIMEOUTS = {
    "/api/jobs/create": 10,
    "/api/jobs/": 10,  # GET job
    "/api/jobs/.*llm-call": 60,
    "/api/jobs/.*complete": 30,
    "/api/jobs/create-and-call": 60,
}

def get_timeout_for_endpoint(url: str) -> int:
    """Get recommended timeout for endpoint"""
    for pattern, timeout in ENDPOINT_TIMEOUTS.items():
        if pattern in url:
            return timeout
    return 30  # Default

# Usage
timeout = get_timeout_for_endpoint(url)
response = requests.post(url, json=data, timeout=timeout)
```

## Best Practices

### 1. Always Use Timeouts

```python
# ✅ Good - With appropriate timeout
response = requests.post(url, json=data, timeout=30)

# ✅ Better - With endpoint-specific timeout
timeout = get_timeout_for_endpoint(url)
response = requests.post(url, json=data, timeout=timeout)

# ❌ Bad - Can hang forever
response = requests.post(url, json=data)
```

### 2. Implement Smart Retry Logic

```python
# ✅ Good - Exponential backoff with jitter
for attempt in range(3):
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        break
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [429, 500, 503] and attempt < 2:
            delay = (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(delay)
        else:
            raise

# ❌ Bad - Fixed delay, retries everything
for attempt in range(3):
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        break
    except:
        time.sleep(1)  # Always 1 second, no distinction between errors
```

### 3. Handle Specific Errors

```python
# ✅ Good - Handle specific errors differently
try:
    response = make_request()
except AuthenticationError:
    # Refresh key
    pass
except InsufficientCreditsError:
    # Notify user
    pass
except RateLimitError:
    # Queue for later
    pass

# ❌ Bad - Catch-all error handling
try:
    response = make_request()
except Exception:
    # What went wrong?
    pass
```

### 4. Log Errors with Context

```python
try:
    response = make_request()
except Exception as e:
    logger.error(
        "API request failed",
        extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "team_id": team_id,
            "job_id": job_id,
            "url": url,
            "attempt": attempt,
            "status_code": getattr(e.response, 'status_code', None)
        }
    )
```

### 5. Complete Jobs on Failure

```python
try:
    # Make LLM call
    response = llm_call(job_id, messages)
    # Complete successfully
    complete_job(job_id, "completed")
except Exception as e:
    # Mark job as failed (important for credit tracking!)
    complete_job(job_id, "failed", error_message=str(e))
    raise
```

### 6. Use Circuit Breaker Pattern

For high-volume applications, implement circuit breaker to prevent cascading failures:

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """Simple circuit breaker implementation"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func, *args, **kwargs):
        """Call function with circuit breaker"""

        # If circuit is open, check if timeout expired
        if self.state == "open":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half_open"
                self.failures = 0
            else:
                raise APIError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)

            # Success - reset failures
            if self.state == "half_open":
                self.state = "closed"
            self.failures = 0

            return result

        except (ServerError, RateLimitError) as e:
            # Track failures
            self.failures += 1
            self.last_failure_time = datetime.now()

            # Open circuit if threshold exceeded
            if self.failures >= self.failure_threshold:
                self.state = "open"

            raise

# Usage
circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

try:
    result = circuit_breaker.call(
        make_api_request,
        url=url,
        headers=headers,
        data=data
    )
except APIError as e:
    print(f"Request failed: {e}")
```

## Next Steps

Now that you understand error handling:

1. **[Learn Best Practices](best-practices.md)** - Optimization and performance tips
2. **[See Examples](../examples/basic-usage.md)** - Working code with error handling
3. **[Review API Reference](../api-reference/overview.md)** - All error codes documented
4. **[Troubleshooting Guide](../testing/troubleshooting.md)** - Common issues and solutions

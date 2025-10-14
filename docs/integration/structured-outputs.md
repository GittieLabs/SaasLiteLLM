# Structured Outputs

Get type-safe, validated responses from LLMs using Pydantic models instead of raw text.

## Why Structured Outputs?

**Traditional Approach (Unreliable):**
```python
# Ask LLM to return JSON
response = await client.chat(job_id, [{
    "role": "user",
    "content": "Extract name and email from: John Doe, john@example.com. Return as JSON."
}])

# Hope the response is valid JSON
text = response.choices[0].message["content"]
data = json.loads(text)  # ❌ Might fail if LLM returns invalid JSON
name = data["name"]       # ❌ Might fail if field missing
```

**Structured Outputs (Reliable):**
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    email: str

# Get validated Pydantic model
person = await client.structured_output(
    job_id=job_id,
    messages=[{
        "role": "user",
        "content": "Extract: John Doe, john@example.com"
    }],
    response_model=Person
)

print(person.name)   # ✅ Guaranteed to exist
print(person.email)  # ✅ Guaranteed to be a string
```

**Benefits:**
- ✅ **Type Safety**: IDE autocomplete and type checking
- ✅ **Validation**: Automatic data validation via Pydantic
- ✅ **Reliability**: LLM is forced to match your schema
- ✅ **No Parsing**: No need to parse JSON manually
- ✅ **Error Handling**: Clear validation errors if data is malformed

## How It Works

```
1. You define Pydantic model
   ↓
2. Client converts model to JSON schema
   ↓
3. Schema sent to LLM as response_format
   ↓
4. LLM generates JSON matching schema
   ↓
5. Client validates and returns Pydantic instance
```

!!! info "Built on LiteLLM"
    Structured outputs leverage [LiteLLM](https://docs.litellm.ai)'s function calling capabilities, which work across OpenAI, Anthropic, Google, and other providers that support structured generation.

## Basic Example

### Define Your Model

```python
from pydantic import BaseModel, Field

class MovieReview(BaseModel):
    title: str = Field(description="Movie title")
    rating: int = Field(ge=1, le=5, description="Rating from 1-5 stars")
    summary: str = Field(description="Brief review summary")
    recommended: bool = Field(description="Whether you recommend this movie")
```

### Extract Structured Data

```python
import asyncio
from examples.typed_client import SaaSLLMClient

async def extract_review():
    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("review_extraction")

        review_text = """
        I watched Inception last night. Amazing movie!
        The plot was complex but engaging. Christopher Nolan
        is a genius. I'd give it 5 stars and recommend it
        to everyone who likes mind-bending thrillers.
        """

        review = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Extract structured review from: {review_text}"
            }],
            response_model=MovieReview
        )

        print(f"Title: {review.title}")              # Inception
        print(f"Rating: {review.rating}/5")           # 5/5
        print(f"Summary: {review.summary}")           # Complex but engaging...
        print(f"Recommended: {review.recommended}")   # True

        await client.complete_job(job_id, "completed")

asyncio.run(extract_review())
```

## Pydantic Model Features

### Basic Types

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str                    # String
    age: int                     # Integer
    height: float                # Float
    is_active: bool              # Boolean
    tags: list[str]              # List of strings
    metadata: dict[str, str]     # Dictionary
```

### Optional Fields

```python
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str                      # Required
    email: str                         # Required
    phone: Optional[str] = None        # Optional, defaults to None
    middle_name: str | None = None     # Alternative syntax (Python 3.10+)
```

### Field Validation

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price must be positive")
    quantity: int = Field(ge=0, le=10000)
    sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$")  # Regex validation
```

### Default Values

```python
from pydantic import BaseModel, Field

class Settings(BaseModel):
    theme: str = "dark"                              # Simple default
    notifications: bool = Field(default=True)        # Field with default
    max_retries: int = 3
```

### Field Descriptions

Descriptions help the LLM understand what to extract:

```python
class Address(BaseModel):
    street: str = Field(description="Street address including number")
    city: str = Field(description="City name")
    state: str = Field(description="2-letter state code (e.g., CA, NY)")
    zip_code: str = Field(description="5-digit ZIP code")
    country: str = Field(default="USA", description="Country name")
```

### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

class Company(BaseModel):
    name: str
    industry: str

class Employee(BaseModel):
    name: str
    email: str
    address: Address           # Nested model
    employer: Company          # Nested model
    skills: list[str]
```

### Enums

```python
from enum import Enum
from pydantic import BaseModel

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(BaseModel):
    title: str
    priority: Priority         # Must be one of the enum values
    assignee: str
```

### Lists and Complex Types

```python
from pydantic import BaseModel

class Tag(BaseModel):
    name: str
    color: str

class BlogPost(BaseModel):
    title: str
    author: str
    tags: list[Tag]                    # List of nested models
    word_count: int
    published: bool
```

## Common Use Cases

### Use Case 1: Contact Information Extraction

```python
from pydantic import BaseModel, EmailStr, Field

class Contact(BaseModel):
    name: str
    email: EmailStr                     # Validates email format
    phone: str = Field(pattern=r"^\+?1?\d{10,15}$")
    company: str
    job_title: str

async def extract_contact(text: str):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("contact_extraction")

        contact = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Extract contact information: {text}"
            }],
            response_model=Contact
        )

        await client.complete_job(job_id, "completed")
        return contact

# Usage
text = "John Smith, CTO at TechCorp, john.smith@techcorp.com, +1-555-123-4567"
contact = await extract_contact(text)
```

### Use Case 2: Resume Parsing

```python
from pydantic import BaseModel

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: int

class WorkExperience(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: str
    responsibilities: list[str]

class Resume(BaseModel):
    name: str
    email: str
    phone: str
    summary: str
    education: list[Education]
    experience: list[WorkExperience]
    skills: list[str]

async def parse_resume(resume_text: str):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("resume_parsing")

        resume = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Parse this resume:\n\n{resume_text}"
            }],
            response_model=Resume
        )

        await client.complete_job(job_id, "completed")
        return resume
```

### Use Case 3: Sentiment Analysis

```python
from enum import Enum
from pydantic import BaseModel, Field

class Sentiment(str, Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"

class SentimentAnalysis(BaseModel):
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    key_phrases: list[str] = Field(description="Key phrases that influenced sentiment")
    summary: str = Field(description="Brief explanation of the sentiment")

async def analyze_sentiment(text: str):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("sentiment_analysis")

        analysis = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Analyze sentiment: {text}"
            }],
            response_model=SentimentAnalysis
        )

        await client.complete_job(job_id, "completed")
        return analysis
```

### Use Case 4: Data Classification

```python
from enum import Enum
from pydantic import BaseModel

class Category(str, Enum):
    SPAM = "spam"
    SUPPORT = "support"
    SALES = "sales"
    BILLING = "billing"
    FEEDBACK = "feedback"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class EmailClassification(BaseModel):
    category: Category
    priority: Priority
    requires_response: bool
    suggested_department: str
    key_topics: list[str]

async def classify_email(email_text: str):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("email_classification")

        classification = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Classify this email:\n\n{email_text}"
            }],
            response_model=EmailClassification
        )

        await client.complete_job(job_id, "completed")
        return classification
```

### Use Case 5: Invoice Extraction

```python
from pydantic import BaseModel, Field
from datetime import date

class LineItem(BaseModel):
    description: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(gt=0)
    total: float = Field(gt=0)

class Invoice(BaseModel):
    invoice_number: str
    invoice_date: str
    due_date: str
    vendor_name: str
    vendor_address: str
    customer_name: str
    customer_address: str
    line_items: list[LineItem]
    subtotal: float
    tax: float
    total: float

async def extract_invoice(invoice_text: str):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("invoice_extraction")

        invoice = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Extract invoice data:\n\n{invoice_text}"
            }],
            response_model=Invoice
        )

        await client.complete_job(job_id, "completed")
        return invoice
```

## Error Handling

### Validation Errors

```python
from pydantic import ValidationError

async def safe_extraction():
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("extraction")

        try:
            person = await client.structured_output(
                job_id=job_id,
                messages=[{"role": "user", "content": "..."}],
                response_model=Person
            )

            await client.complete_job(job_id, "completed")
            return person

        except ValidationError as e:
            # Pydantic validation failed
            print(f"Validation error: {e}")
            await client.complete_job(job_id, "failed")
            raise

        except Exception as e:
            # Other errors (API, network, etc.)
            print(f"Error: {e}")
            await client.complete_job(job_id, "failed")
            raise
```

### Handling Missing Data

Use optional fields for data that might not exist:

```python
from pydantic import BaseModel
from typing import Optional

class PersonWithOptionals(BaseModel):
    name: str                           # Required
    email: str                          # Required
    phone: Optional[str] = None         # Optional
    address: Optional[str] = None       # Optional
    company: Optional[str] = None       # Optional
```

## Advanced Patterns

### Retry on Validation Failure

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def extract_with_retry(text: str):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("extraction_with_retry")

        try:
            result = await client.structured_output(
                job_id=job_id,
                messages=[{
                    "role": "user",
                    "content": f"Extract data: {text}"
                }],
                response_model=Person
            )

            await client.complete_job(job_id, "completed")
            return result

        except Exception as e:
            await client.complete_job(job_id, "failed")
            raise
```

### Batch Processing

```python
async def process_batch(documents: list[str]):
    """Process multiple documents concurrently"""

    async with SaaSLLMClient(...) as client:

        async def process_one(doc: str):
            job_id = await client.create_job("batch_extraction")

            try:
                result = await client.structured_output(
                    job_id=job_id,
                    messages=[{"role": "user", "content": f"Extract: {doc}"}],
                    response_model=Person
                )
                await client.complete_job(job_id, "completed")
                return result

            except Exception as e:
                await client.complete_job(job_id, "failed")
                raise

        # Process all documents concurrently
        tasks = [process_one(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successes and failures
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        return successes, failures
```

### Multiple Extraction Passes

```python
class InitialExtraction(BaseModel):
    raw_text: str
    detected_entities: list[str]

class DetailedExtraction(BaseModel):
    name: str
    email: str
    phone: str
    company: str

async def two_pass_extraction(text: str):
    async with SaaSLLMClient(...) as client:
        job_id = await client.create_job("two_pass_extraction")

        # Pass 1: Identify what's in the text
        initial = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Identify entities in: {text}"
            }],
            response_model=InitialExtraction
        )

        # Pass 2: Extract detailed information
        detailed = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Extract contact details from: {text}"
            }],
            response_model=DetailedExtraction
        )

        await client.complete_job(job_id, "completed")
        return detailed
```

## Model Compatibility

Structured outputs work with models that support function calling:

**✅ Supported:**
- OpenAI: GPT-4, GPT-4-turbo, GPT-3.5-turbo
- Anthropic: Claude 3 Opus, Sonnet, Haiku
- Google: Gemini Pro, Gemini 1.5 Pro
- Azure OpenAI: All GPT-4 and GPT-3.5-turbo variants

**❌ Not Supported:**
- Legacy models (GPT-3, older models)
- Some open-source models without function calling

## Best Practices

### 1. Use Descriptive Field Names

```python
# ❌ Bad: Unclear field names
class Data(BaseModel):
    f1: str
    f2: int
    f3: bool

# ✅ Good: Clear, descriptive names
class UserProfile(BaseModel):
    full_name: str
    age_years: int
    is_verified: bool
```

### 2. Add Field Descriptions

```python
# ✅ Good: Descriptions help the LLM understand
class Product(BaseModel):
    name: str = Field(description="Product name as it appears on packaging")
    price: float = Field(description="Price in USD, without currency symbol")
    sku: str = Field(description="Stock keeping unit, format: ABC-1234")
```

### 3. Use Validation

```python
# ✅ Good: Validate data types and ranges
class Rating(BaseModel):
    score: int = Field(ge=1, le=5, description="Rating from 1-5")
    reviewer: str = Field(min_length=1, max_length=100)
    verified: bool
```

### 4. Make Fields Optional When Appropriate

```python
# ✅ Good: Optional for data that might not exist
class Article(BaseModel):
    title: str                           # Always required
    author: str                          # Always required
    subtitle: Optional[str] = None       # Might not exist
    published_date: Optional[str] = None # Might not be found
```

### 5. Use Enums for Fixed Options

```python
# ✅ Good: Constrain to specific values
class Status(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Article(BaseModel):
    title: str
    status: Status  # Can only be one of the enum values
```

## Troubleshooting

### LLM Returns Invalid Data

**Problem:** Validation errors even with clear schema

**Solutions:**
1. Add more detailed field descriptions
2. Provide an example in the prompt
3. Use a more capable model (GPT-4 vs GPT-3.5)
4. Make fields optional if data might not exist

```python
# Better prompt with example
messages=[{
    "role": "user",
    "content": f"""
    Extract person data from: {text}

    Example output format:
    {{
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-555-1234"
    }}
    """
}]
```

### Model Doesn't Support Structured Outputs

**Problem:** "Model does not support function calling"

**Solution:** Use a compatible model (GPT-4, Claude 3, Gemini Pro)

### Performance Issues

**Problem:** Structured outputs are slower than regular chat

**This is expected:**
- LLM must generate valid JSON matching schema
- More processing overhead than free-form text
- Trade-off for reliability and type safety

**Optimize:**
- Use faster models (GPT-3.5-turbo vs GPT-4) for simple extractions
- Process documents in batches concurrently
- Cache results when possible

## Next Steps

Now that you understand structured outputs:

1. **[See Examples](../examples/structured-outputs.md)** - Working code examples
2. **[Learn Streaming](streaming.md)** - Real-time responses
3. **[Error Handling](error-handling.md)** - Handle failures gracefully
4. **[Best Practices](best-practices.md)** - Production patterns

## Quick Reference

### Basic Structured Output

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    email: str

person = await client.structured_output(
    job_id=job_id,
    messages=[{"role": "user", "content": "Extract: John, john@example.com"}],
    response_model=Person
)
```

### With Validation

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0)

product = await client.structured_output(
    job_id=job_id,
    messages=[{"role": "user", "content": "..."}],
    response_model=Product
)
```

### With Optional Fields

```python
from typing import Optional

class User(BaseModel):
    username: str
    email: str
    phone: Optional[str] = None

user = await client.structured_output(
    job_id=job_id,
    messages=[{"role": "user", "content": "..."}],
    response_model=User
)
```

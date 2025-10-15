# Structured Output Examples

Working examples of extracting type-safe, validated data using Pydantic models.

!!! tip "Prerequisites"
    - Have your virtual key from team creation
    - SaaS API running on http://localhost:8003
    - Typed client installed (`pip install httpx pydantic`)

[:octicons-arrow-right-24: Learn about structured outputs](../integration/structured-outputs.md)

## Example 1: Contact Information Extraction

Extract contact details from unstructured text:

```python
import asyncio
from pydantic import BaseModel, EmailStr, Field
from examples.typed_client import SaaSLLMClient

class Contact(BaseModel):
    """Contact information extracted from text"""
    name: str = Field(description="Full name")
    email: EmailStr = Field(description="Email address")
    phone: str = Field(description="Phone number")
    company: str = Field(description="Company name")
    job_title: str = Field(description="Job title/position")

async def extract_contact_info():
    """Extract contact information from business card text"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-virtual-key-here"
    ) as client:

        job_id = await client.create_job("contact_extraction")

        business_card = """
        Sarah Johnson
        Chief Technology Officer
        TechVentures Inc.
        sarah.johnson@techventures.com
        Mobile: +1 (555) 987-6543
        """

        contact = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Extract contact information from this business card:\n\n{business_card}"
            }],
            response_model=Contact
        )

        # Now you have a fully typed, validated Contact object
        print(f"Name: {contact.name}")
        print(f"Title: {contact.job_title}")
        print(f"Company: {contact.company}")
        print(f"Email: {contact.email}")
        print(f"Phone: {contact.phone}")

        await client.complete_job(job_id, "completed")
        return contact

if __name__ == "__main__":
    contact = asyncio.run(extract_contact_info())
```

**Output:**
```
Name: Sarah Johnson
Title: Chief Technology Officer
Company: TechVentures Inc.
Email: sarah.johnson@techventures.com
Phone: +1 (555) 987-6543
```

## Example 2: Resume Parser

Parse resumes into structured data:

```python
import asyncio
from pydantic import BaseModel, EmailStr, Field
from examples.typed_client import SaaSLLMClient

class Education(BaseModel):
    degree: str = Field(description="Degree name (e.g., BS, MS, PhD)")
    field: str = Field(description="Field of study")
    institution: str = Field(description="School/university name")
    graduation_year: int = Field(description="Year graduated")

class Experience(BaseModel):
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    start_date: str = Field(description="Start date (YYYY-MM or YYYY)")
    end_date: str = Field(description="End date or 'Present'")
    responsibilities: list[str] = Field(description="Key responsibilities")

class Resume(BaseModel):
    name: str
    email: EmailStr
    phone: str
    summary: str = Field(description="Professional summary")
    education: list[Education]
    experience: list[Experience]
    skills: list[str]

async def parse_resume():
    """Parse a resume into structured format"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("resume_parsing")

        resume_text = """
        Michael Chen
        michael.chen@email.com | (555) 123-4567

        PROFESSIONAL SUMMARY
        Senior Software Engineer with 8 years of experience in full-stack development,
        specializing in Python, React, and cloud infrastructure.

        EDUCATION
        Master of Science in Computer Science
        Stanford University, 2015

        Bachelor of Science in Computer Engineering
        UC Berkeley, 2013

        EXPERIENCE
        Senior Software Engineer | TechCorp Inc | 2018 - Present
        - Led development of microservices architecture handling 10M+ requests/day
        - Mentored team of 5 junior engineers
        - Reduced API latency by 40% through optimization

        Software Engineer | StartupXYZ | 2015 - 2018
        - Built real-time analytics dashboard using React and WebSockets
        - Implemented CI/CD pipeline reducing deployment time by 60%
        - Developed RESTful APIs serving 100K+ daily users

        SKILLS
        Python, JavaScript, React, Node.js, PostgreSQL, Docker, Kubernetes, AWS
        """

        resume = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Parse this resume into structured format:\n\n{resume_text}"
            }],
            response_model=Resume
        )

        print(f"\n=== RESUME: {resume.name} ===\n")
        print(f"Email: {resume.email}")
        print(f"Phone: {resume.phone}")
        print(f"\nSummary: {resume.summary}\n")

        print("Education:")
        for edu in resume.education:
            print(f"  - {edu.degree} in {edu.field}, {edu.institution} ({edu.graduation_year})")

        print("\nExperience:")
        for exp in resume.experience:
            print(f"  - {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date})")
            for resp in exp.responsibilities[:2]:  # Show first 2
                print(f"    • {resp}")

        print(f"\nSkills: {', '.join(resume.skills)}")

        await client.complete_job(job_id, "completed")
        return resume

if __name__ == "__main__":
    resume = asyncio.run(parse_resume())
```

## Example 3: Sentiment Analysis

Analyze sentiment with structured results:

```python
import asyncio
from enum import Enum
from pydantic import BaseModel, Field
from examples.typed_client import SaaSLLMClient

class Sentiment(str, Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"

class SentimentAnalysis(BaseModel):
    sentiment: Sentiment = Field(description="Overall sentiment")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    key_phrases: list[str] = Field(description="Phrases that influenced sentiment")
    reasoning: str = Field(description="Brief explanation of sentiment")

async def analyze_sentiment():
    """Analyze sentiment of product reviews"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        reviews = [
            "This product is absolutely amazing! Best purchase I've made all year. Highly recommend!",
            "Terrible quality. Broke after one week. Total waste of money. Very disappointed.",
            "It's okay. Does what it's supposed to do. Nothing special but not bad either."
        ]

        for i, review_text in enumerate(reviews, 1):
            job_id = await client.create_job(f"sentiment_analysis_{i}")

            analysis = await client.structured_output(
                job_id=job_id,
                messages=[{
                    "role": "user",
                    "content": f"Analyze the sentiment of this review:\n\n{review_text}"
                }],
                response_model=SentimentAnalysis
            )

            print(f"\n--- Review {i} ---")
            print(f"Text: {review_text}")
            print(f"Sentiment: {analysis.sentiment.value.upper()}")
            print(f"Confidence: {analysis.confidence:.2%}")
            print(f"Key phrases: {', '.join(analysis.key_phrases)}")
            print(f"Reasoning: {analysis.reasoning}")

            await client.complete_job(job_id, "completed")

if __name__ == "__main__":
    asyncio.run(analyze_sentiment())
```

**Output:**
```
--- Review 1 ---
Text: This product is absolutely amazing! Best purchase I've made all year. Highly recommend!
Sentiment: VERY_POSITIVE
Confidence: 95.00%
Key phrases: absolutely amazing, Best purchase, Highly recommend
Reasoning: Strong positive language with superlatives and explicit recommendation

--- Review 2 ---
Text: Terrible quality. Broke after one week. Total waste of money. Very disappointed.
Sentiment: VERY_NEGATIVE
Confidence: 98.00%
Key phrases: Terrible quality, waste of money, Very disappointed
Reasoning: Multiple negative descriptors and product failure mentioned

--- Review 3 ---
Text: It's okay. Does what it's supposed to do. Nothing special but not bad either.
Sentiment: NEUTRAL
Confidence: 90.00%
Key phrases: It's okay, Nothing special, not bad
Reasoning: Balanced statements without strong positive or negative indicators
```

## Example 4: Invoice Data Extraction

Extract structured data from invoices:

```python
import asyncio
from pydantic import BaseModel, Field
from examples.typed_client import SaaSLLMClient

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

async def extract_invoice():
    """Extract structured data from invoice text"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("invoice_extraction")

        invoice_text = """
        INVOICE

        Invoice #: INV-2024-00123
        Date: October 14, 2024
        Due Date: November 14, 2024

        From:
        TechSupplies Inc.
        123 Supplier Street
        San Francisco, CA 94105

        To:
        ACME Corporation
        456 Business Ave
        New York, NY 10001

        ITEMS:
        1. Laptop Computer - Model XPS 15
           Qty: 5 @ $1,299.00 each = $6,495.00

        2. Wireless Mouse - Model MX Master
           Qty: 10 @ $99.00 each = $990.00

        3. USB-C Hub - 7-in-1
           Qty: 5 @ $49.99 each = $249.95

        Subtotal: $7,734.95
        Tax (8.5%): $657.47
        TOTAL: $8,392.42
        """

        invoice = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Extract invoice data:\n\n{invoice_text}"
            }],
            response_model=Invoice
        )

        print(f"\n=== INVOICE {invoice.invoice_number} ===\n")
        print(f"Date: {invoice.invoice_date}")
        print(f"Due: {invoice.due_date}")
        print(f"\nVendor: {invoice.vendor_name}")
        print(f"Customer: {invoice.customer_name}")
        print(f"\nLine Items:")

        for item in invoice.line_items:
            print(f"  - {item.description}")
            print(f"    {item.quantity} × ${item.unit_price:.2f} = ${item.total:.2f}")

        print(f"\nSubtotal: ${invoice.subtotal:.2f}")
        print(f"Tax: ${invoice.tax:.2f}")
        print(f"TOTAL: ${invoice.total:.2f}")

        await client.complete_job(job_id, "completed")
        return invoice

if __name__ == "__main__":
    invoice = asyncio.run(extract_invoice())
```

## Example 5: Email Classification

Classify and route emails automatically:

```python
import asyncio
from enum import Enum
from pydantic import BaseModel, Field
from examples.typed_client import SaaSLLMClient

class Category(str, Enum):
    SPAM = "spam"
    SUPPORT = "support"
    SALES = "sales"
    BILLING = "billing"
    FEEDBACK = "feedback"
    OTHER = "other"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class EmailClassification(BaseModel):
    category: Category = Field(description="Email category")
    priority: Priority = Field(description="Priority level")
    requires_response: bool = Field(description="Whether email needs a response")
    suggested_department: str = Field(description="Department that should handle this")
    key_topics: list[str] = Field(description="Main topics discussed")
    summary: str = Field(description="Brief summary of email content")

async def classify_email():
    """Classify incoming emails for routing"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        emails = [
            """
            Subject: URGENT: Production server down

            Hi team,

            Our production API server has been down for 15 minutes. Customers
            are reporting errors when trying to access their accounts. This is
            causing significant business impact. Please investigate immediately.

            Thanks,
            John from Operations
            """,
            """
            Subject: Question about pricing plans

            Hello,

            I'm interested in your Enterprise plan but have some questions:
            1. What's the difference between Pro and Enterprise?
            2. Do you offer annual billing discounts?
            3. Can we get a demo of the admin dashboard?

            Looking forward to hearing from you.

            Best,
            Sarah Mitchell
            CTO, TechStartup Inc.
            """,
            """
            Subject: Feature request: Dark mode

            Hey there!

            Love your product! One suggestion - it would be great to have a
            dark mode option. I work late at night and the bright interface
            can be harsh on the eyes. Many of our team members would appreciate
            this feature.

            Keep up the great work!

            Mike
            """
        ]

        for i, email_text in enumerate(emails, 1):
            job_id = await client.create_job(f"email_classification_{i}")

            classification = await client.structured_output(
                job_id=job_id,
                messages=[{
                    "role": "user",
                    "content": f"Classify this email:\n\n{email_text}"
                }],
                response_model=EmailClassification
            )

            print(f"\n{'='*60}")
            print(f"EMAIL {i}")
            print(f"{'='*60}")
            print(f"Category: {classification.category.value.upper()}")
            print(f"Priority: {classification.priority.value.upper()}")
            print(f"Requires Response: {'YES' if classification.requires_response else 'NO'}")
            print(f"Route To: {classification.suggested_department}")
            print(f"Topics: {', '.join(classification.key_topics)}")
            print(f"Summary: {classification.summary}")

            await client.complete_job(job_id, "completed")

if __name__ == "__main__":
    asyncio.run(classify_email())
```

**Output:**
```
============================================================
EMAIL 1
============================================================
Category: SUPPORT
Priority: URGENT
Requires Response: YES
Route To: Engineering/DevOps
Topics: production server, downtime, API errors
Summary: Critical production server outage affecting customers

============================================================
EMAIL 2
============================================================
Category: SALES
Priority: MEDIUM
Requires Response: YES
Route To: Sales
Topics: pricing, enterprise plan, demo request
Summary: Prospective customer inquiring about enterprise pricing and demo

============================================================
EMAIL 3
============================================================
Category: FEEDBACK
Priority: LOW
Requires Response: NO
Route To: Product Management
Topics: feature request, dark mode, UI improvement
Summary: User suggesting dark mode feature for better night-time usability
```

## Example 6: Product Data Normalization

Normalize product listings from different sources:

```python
import asyncio
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from examples.typed_client import SaaSLLMClient

class Category(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    SPORTS = "sports"
    OTHER = "other"

class Condition(str, Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class NormalizedProduct(BaseModel):
    title: str = Field(description="Clean product title")
    category: Category = Field(description="Product category")
    brand: str = Field(description="Brand/manufacturer name")
    price: float = Field(gt=0, description="Price in USD")
    condition: Condition = Field(description="Product condition")
    description: str = Field(description="Clean description")
    features: list[str] = Field(description="Key product features")
    sku: Optional[str] = Field(default=None, description="SKU if available")

async def normalize_products():
    """Normalize product listings from various sources"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        # Messy product listings from different sources
        raw_listings = [
            """
            Apple MacBook Pro 16" M3 Max - BRAND NEW SEALED!!!
            Price: $3499.99 USD
            This is a BRAND NEW, factory sealed MacBook Pro with M3 Max chip.
            Specs: 16GB RAM, 512GB SSD, Space Gray
            Perfect for professionals! Fast shipping available.
            SKU: MBP-M3-16-SG
            """,
            """
            nike air zoom pegasus 40 mens running shoes sz 10.5 like new condition
            worn only twice | $89 | retail $140
            Features: responsive cushioning, breathable mesh upper, rubber outsole
            Color: Black/White
            """
        ]

        for i, listing in enumerate(raw_listings, 1):
            job_id = await client.create_job(f"product_normalization_{i}")

            product = await client.structured_output(
                job_id=job_id,
                messages=[{
                    "role": "user",
                    "content": f"Normalize this product listing:\n\n{listing}"
                }],
                response_model=NormalizedProduct
            )

            print(f"\n{'='*60}")
            print(f"PRODUCT {i}")
            print(f"{'='*60}")
            print(f"Title: {product.title}")
            print(f"Brand: {product.brand}")
            print(f"Category: {product.category.value}")
            print(f"Price: ${product.price:.2f}")
            print(f"Condition: {product.condition.value.replace('_', ' ').title()}")
            print(f"SKU: {product.sku or 'N/A'}")
            print(f"\nDescription: {product.description}")
            print(f"\nFeatures:")
            for feature in product.features:
                print(f"  • {feature}")

            await client.complete_job(job_id, "completed")

if __name__ == "__main__":
    asyncio.run(normalize_products())
```

## Example 7: Meeting Notes Structuring

Convert meeting transcripts into structured action items:

```python
import asyncio
from pydantic import BaseModel, Field
from examples.typed_client import SaaSLLMClient

class ActionItem(BaseModel):
    task: str = Field(description="What needs to be done")
    assignee: str = Field(description="Who is responsible")
    due_date: str = Field(description="When it's due")
    priority: str = Field(description="Priority level")

class Decision(BaseModel):
    topic: str = Field(description="What was decided about")
    decision: str = Field(description="The decision made")
    rationale: str = Field(description="Why this decision was made")

class MeetingNotes(BaseModel):
    meeting_title: str
    date: str
    attendees: list[str]
    summary: str = Field(description="Brief meeting summary")
    key_points: list[str] = Field(description="Main discussion points")
    decisions: list[Decision]
    action_items: list[ActionItem]
    next_meeting: str = Field(description="When to meet again")

async def structure_meeting_notes():
    """Convert meeting transcript into structured notes"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        job_id = await client.create_job("meeting_notes_structuring")

        transcript = """
        Product Planning Meeting - October 14, 2024

        Attendees: Sarah (PM), Mike (Eng), Lisa (Design), John (Marketing)

        Sarah: Let's discuss the Q4 roadmap. Our main priorities are the mobile app
        and dark mode feature.

        Mike: The mobile app will take about 8 weeks. I can start next week if we
        finalize the requirements.

        Lisa: I'll have the mobile designs ready by end of this week. Also working
        on dark mode mockups.

        Sarah: Great. Let's decide on launch date. What about December 15th for
        the mobile app beta?

        Everyone agrees.

        John: I'll need at least 2 weeks before launch to prepare marketing materials.
        So designs and copy by December 1st?

        Sarah: Sounds good. Action items:
        - Lisa: Finalize mobile designs by October 18th
        - Mike: Start mobile development by October 21st
        - John: Prepare marketing materials by December 1st
        - Sarah: Set up beta testing program by November 15th

        Next meeting: October 28th to review mobile app progress.
        """

        notes = await client.structured_output(
            job_id=job_id,
            messages=[{
                "role": "user",
                "content": f"Structure these meeting notes:\n\n{transcript}"
            }],
            response_model=MeetingNotes
        )

        print(f"\n{'='*60}")
        print(f"{notes.meeting_title}")
        print(f"{'='*60}")
        print(f"Date: {notes.date}")
        print(f"Attendees: {', '.join(notes.attendees)}\n")
        print(f"Summary: {notes.summary}\n")

        print("Key Points:")
        for point in notes.key_points:
            print(f"  • {point}")

        print(f"\nDecisions Made:")
        for decision in notes.decisions:
            print(f"  • {decision.topic}")
            print(f"    Decision: {decision.decision}")
            print(f"    Rationale: {decision.rationale}\n")

        print("Action Items:")
        for item in notes.action_items:
            print(f"  • {item.task}")
            print(f"    Assignee: {item.assignee} | Due: {item.due_date} | Priority: {item.priority}\n")

        print(f"Next Meeting: {notes.next_meeting}")

        await client.complete_job(job_id, "completed")
        return notes

if __name__ == "__main__":
    notes = asyncio.run(structure_meeting_notes())
```

## Example 8: Batch Processing with Error Handling

Process multiple documents with proper error handling:

```python
import asyncio
from pydantic import BaseModel, ValidationError
from typing import Optional
from examples.typed_client import SaaSLLMClient

class Person(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None

async def process_with_error_handling():
    """Process multiple contacts with proper error handling"""

    async with SaaSLLMClient(
        base_url="http://localhost:8003",
        team_id="acme-corp",
        virtual_key="sk-your-key"
    ) as client:

        contacts_text = [
            "John Doe, john@example.com, TechCorp",
            "Jane Smith, jane.smith@company.com, +1-555-1234",
            "Invalid data here",  # Will fail
            "Bob Wilson, bob@example.com, (555) 999-8888, Wilson Industries"
        ]

        results = []
        errors = []

        for i, text in enumerate(contacts_text, 1):
            job_id = await client.create_job(f"batch_contact_{i}")

            try:
                person = await client.structured_output(
                    job_id=job_id,
                    messages=[{
                        "role": "user",
                        "content": f"Extract contact info: {text}"
                    }],
                    response_model=Person
                )

                results.append(person)
                await client.complete_job(job_id, "completed")
                print(f"✅ Processed: {person.name}")

            except ValidationError as e:
                errors.append({"text": text, "error": str(e)})
                await client.complete_job(job_id, "failed")
                print(f"❌ Validation failed for: {text}")

            except Exception as e:
                errors.append({"text": text, "error": str(e)})
                await client.complete_job(job_id, "failed")
                print(f"❌ Error processing: {text}")

        print(f"\n{'='*60}")
        print(f"Processed: {len(results)} successful, {len(errors)} failed")
        print(f"{'='*60}\n")

        print("Successful extractions:")
        for person in results:
            print(f"  • {person.name} - {person.email}")

        if errors:
            print(f"\nFailed extractions:")
            for err in errors:
                print(f"  • {err['text'][:50]}...")

        return results, errors

if __name__ == "__main__":
    results, errors = asyncio.run(process_with_error_handling())
```

## Best Practices from Examples

### 1. Always Use Descriptive Models

```python
# ✅ Good: Clear, descriptive model
class ProductReview(BaseModel):
    product_name: str
    rating: int = Field(ge=1, le=5)
    review_text: str
    would_recommend: bool
```

### 2. Add Field Descriptions

```python
# ✅ Good: Helps LLM understand what to extract
class Invoice(BaseModel):
    invoice_number: str = Field(description="Invoice ID, format INV-YYYY-NNNNN")
    total: float = Field(gt=0, description="Total amount in USD")
```

### 3. Use Enums for Fixed Options

```python
# ✅ Good: Constrains to valid values
class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

### 4. Handle Errors Gracefully

```python
# ✅ Good: Proper error handling
try:
    result = await client.structured_output(...)
    await client.complete_job(job_id, "completed")
except ValidationError as e:
    await client.complete_job(job_id, "failed")
    # Handle validation error
```

### 5. Make Optional Fields Optional

```python
# ✅ Good: Not all data might be present
class Contact(BaseModel):
    name: str                      # Required
    email: str                     # Required
    phone: Optional[str] = None    # Optional
```

## Next Steps

Now that you've seen structured output examples:

1. **[Learn More Concepts](../integration/structured-outputs.md)** - Deep dive into structured outputs
2. **[See Streaming Examples](streaming-examples.md)** - Real-time streaming
3. **[Error Handling](../integration/error-handling.md)** - Handle failures
4. **[Best Practices](../integration/best-practices.md)** - Production patterns

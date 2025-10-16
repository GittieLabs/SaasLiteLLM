"""
Example: Instructor-style structured outputs with Pydantic models

This example shows:
1. Defining Pydantic models for structured responses
2. Getting type-safe responses from the API
3. Both non-streaming and streaming structured outputs
"""
import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from typed_client import SaaSLLMClient


# ============================================================================
# Define your Pydantic models (like Instructor)
# ============================================================================

class Person(BaseModel):
    """A person extracted from text"""
    name: str = Field(..., description="Full name of the person")
    age: Optional[int] = Field(None, description="Age in years")
    occupation: Optional[str] = Field(None, description="Job or occupation")


class ResumeData(BaseModel):
    """Structured resume data"""
    full_name: str = Field(..., description="Candidate's full name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    experience_years: Optional[int] = Field(None, description="Years of experience")
    education: List[str] = Field(default_factory=list, description="Educational qualifications")


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    sentiment: str = Field(..., description="Overall sentiment: positive, negative, or neutral")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases from text")


# ============================================================================
# Examples
# ============================================================================

async def example_simple_extraction():
    """Example: Extract structured data from text"""
    print("=" * 60)
    print("Example 1: Simple Person Extraction")
    print("=" * 60)

    async with SaaSLLMClient(
        api_url="http://localhost:8003",
        virtual_key="sk-1234",  # Replace with your virtual key
        team_id="team-alpha"
    ) as client:
        # Create job
        job_id = await client.create_job(
            job_type="structured_extraction",
            metadata={"example": "person_extraction"}
        )

        # Get structured output
        person = await client.structured_output(
            model_group="chat-fast",
            messages=[
                {
                    "role": "system",
                    "content": "Extract person information from the text. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": "John Smith is a 35-year-old software engineer."
                }
            ],
            response_model=Person,
            temperature=0.3,
            purpose="extract_person"
        )

        # Now we have a fully typed Pydantic model!
        print(f"\nExtracted Person:")
        print(f"  Name: {person.name}")
        print(f"  Age: {person.age}")
        print(f"  Occupation: {person.occupation}")
        print(f"\nType: {type(person)}")  # <class '__main__.Person'>

        # Complete job
        await client.complete_job(
            status="completed",
            result=person.model_dump()
        )


async def example_resume_parsing():
    """Example: Parse resume into structured format"""
    print("\n" + "=" * 60)
    print("Example 2: Resume Parsing")
    print("=" * 60)

    resume_text = """
    Jane Doe
    jane.doe@email.com
    (555) 123-4567

    Skills: Python, FastAPI, PostgreSQL, Docker, React, TypeScript
    Experience: 5 years

    Education:
    - BS Computer Science, MIT, 2018
    - MS Artificial Intelligence, Stanford, 2020
    """

    async with SaaSLLMClient(
        api_url="http://localhost:8003",
        virtual_key="sk-1234",
        team_id="team-alpha"
    ) as client:
        # Create job
        job_id = await client.create_job(
            job_type="resume_parsing",
            metadata={"example": "resume_extraction"}
        )

        # Get structured resume data
        resume = await client.structured_output(
            model_group="chat-fast",
            messages=[
                {
                    "role": "system",
                    "content": "Parse the resume text into structured JSON format."
                },
                {
                    "role": "user",
                    "content": f"Parse this resume:\n\n{resume_text}"
                }
            ],
            response_model=ResumeData,
            temperature=0.1,  # Lower temp for more deterministic extraction
            purpose="parse_resume"
        )

        # Fully typed resume object
        print(f"\nParsed Resume:")
        print(f"  Name: {resume.full_name}")
        print(f"  Email: {resume.email}")
        print(f"  Phone: {resume.phone}")
        print(f"  Skills: {', '.join(resume.skills)}")
        print(f"  Experience: {resume.experience_years} years")
        print(f"  Education:")
        for edu in resume.education:
            print(f"    - {edu}")

        # Complete job
        await client.complete_job(
            status="completed",
            result=resume.model_dump()
        )


async def example_sentiment_analysis():
    """Example: Sentiment analysis with confidence"""
    print("\n" + "=" * 60)
    print("Example 3: Sentiment Analysis")
    print("=" * 60)

    async with SaaSLLMClient(
        api_url="http://localhost:8003",
        virtual_key="sk-1234",
        team_id="team-alpha"
    ) as client:
        # Create job
        job_id = await client.create_job(
            job_type="sentiment_analysis",
            metadata={"example": "sentiment"}
        )

        # Analyze sentiment
        text = "I absolutely love this product! It exceeded all my expectations and the customer service was fantastic."

        sentiment = await client.structured_output(
            model_group="chat-fast",
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the sentiment of the text and extract key phrases."
                },
                {
                    "role": "user",
                    "content": f"Analyze: {text}"
                }
            ],
            response_model=SentimentAnalysis,
            temperature=0.2,
            purpose="analyze_sentiment"
        )

        # Type-safe result
        print(f"\nSentiment Analysis:")
        print(f"  Sentiment: {sentiment.sentiment}")
        print(f"  Confidence: {sentiment.confidence:.2%}")
        print(f"  Key Phrases:")
        for phrase in sentiment.key_phrases:
            print(f"    - {phrase}")

        # Complete job
        await client.complete_job(
            status="completed",
            result=sentiment.model_dump()
        )


async def example_streaming_structured():
    """Example: Streaming structured output"""
    print("\n" + "=" * 60)
    print("Example 4: Streaming Structured Output")
    print("=" * 60)

    async with SaaSLLMClient(
        api_url="http://localhost:8003",
        virtual_key="sk-1234",
        team_id="team-alpha"
    ) as client:
        # Create job
        job_id = await client.create_job(
            job_type="streaming_structured",
            metadata={"example": "streaming_person"}
        )

        # Stream structured output
        print("\nStreaming JSON chunks:")
        print("-" * 60)

        accumulated_json = ""

        async for chunk in client.structured_output_stream(
            model_group="chat-fast",
            messages=[
                {
                    "role": "system",
                    "content": "Extract person information. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": "Dr. Sarah Johnson is a 42-year-old neuroscientist."
                }
            ],
            response_model=Person,
            temperature=0.3,
            purpose="stream_extract_person"
        ):
            accumulated_json += chunk
            print(chunk, end="", flush=True)

        print(f"\n{'-' * 60}")

        # Parse the full JSON into Pydantic model
        person = Person.model_validate_json(accumulated_json)
        print(f"\nParsed Person:")
        print(f"  Name: {person.name}")
        print(f"  Age: {person.age}")
        print(f"  Occupation: {person.occupation}")

        # Complete job
        await client.complete_job(
            status="completed",
            result=person.model_dump()
        )


# ============================================================================
# Run all examples
# ============================================================================

async def main():
    """Run all examples"""
    await example_simple_extraction()
    await example_resume_parsing()
    await example_sentiment_analysis()
    await example_streaming_structured()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

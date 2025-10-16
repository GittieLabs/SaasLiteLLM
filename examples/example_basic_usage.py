"""
Example: Basic usage of the type-safe SaaS LiteLLM client

This example shows:
1. Creating a job
2. Making a simple chat completion
3. Completing the job
"""
import asyncio
from typed_client import SaaSLLMClient


async def main():
    # Initialize client
    async with SaaSLLMClient(
        api_url="http://localhost:8003",
        virtual_key="sk-1234",  # Replace with your virtual key
        team_id="team-alpha"
    ) as client:
        # Create a job
        print("Creating job...")
        job_id = await client.create_job(
            job_type="chat_example",
            metadata={"example": "basic_usage"}
        )
        print(f"Job created: {job_id}")

        # Make a simple chat completion
        print("\nMaking chat completion...")
        response = await client.chat(
            model_group="chat-fast",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            temperature=0.7,
            purpose="example_query"
        )

        # Extract response
        message = response.choices[0].message
        print(f"\nAssistant: {message.get('content', '')}")
        print(f"\nUsage: {response.usage.model_dump() if response.usage else 'N/A'}")

        # Complete the job
        print("\nCompleting job...")
        await client.complete_job(
            status="completed",
            result={"response": message.get('content', '')}
        )
        print("Job completed!")


if __name__ == "__main__":
    asyncio.run(main())

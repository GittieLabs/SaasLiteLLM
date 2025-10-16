"""
Example: Streaming chat completions

This example shows:
1. Creating a streaming chat completion
2. Processing chunks as they arrive
3. Real-time printing of the response
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
            job_type="streaming_example",
            metadata={"example": "streaming"}
        )
        print(f"Job created: {job_id}\n")

        # Make a streaming chat completion
        print("Streaming response:\n")
        print("-" * 60)

        accumulated_content = ""

        async for chunk in client.chat_stream(
            model_group="chat-fast",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a short poem about the ocean."}
            ],
            temperature=0.8,
            purpose="streaming_example"
        ):
            # Extract content from chunk
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta and "content" in delta:
                    content = delta["content"]
                    accumulated_content += content
                    print(content, end="", flush=True)

                # Check for usage info (usually in last chunk)
                if chunk.usage:
                    print(f"\n\n{'-' * 60}")
                    print(f"Usage: {chunk.usage.model_dump()}")

        print(f"\n{'-' * 60}")
        print(f"\nFull response length: {len(accumulated_content)} characters")

        # Complete the job
        print("\nCompleting job...")
        await client.complete_job(
            status="completed",
            result={"response": accumulated_content}
        )
        print("Job completed!")


if __name__ == "__main__":
    asyncio.run(main())

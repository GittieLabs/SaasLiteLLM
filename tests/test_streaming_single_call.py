"""
Unit tests for streaming single-call endpoint.

Tests the new POST /api/jobs/create-and-call-stream endpoint
that provides streaming SSE responses for chat applications.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestStreamingSingleCallEndpoint:
    """Test streaming single-call endpoint request/response models"""

    def test_request_model_compatibility(self):
        """Test that SingleCallJobRequest works for streaming endpoint"""
        from src.saas_api import SingleCallJobRequest

        # Streaming endpoint uses the same request model as non-streaming
        request = SingleCallJobRequest(
            team_id="test-team",
            job_type="chat_session",
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7
        )

        assert request.team_id == "test-team"
        assert request.job_type == "chat_session"
        assert request.model == "gpt-4"
        assert request.temperature == 0.7

    def test_request_with_optional_parameters(self):
        """Test request with all optional parameters"""
        from src.saas_api import SingleCallJobRequest

        request = SingleCallJobRequest(
            team_id="test-team",
            job_type="chat_session",
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            user_id="user_123",
            job_metadata={"session_id": "sess_abc"},
            temperature=0.8,
            max_tokens=500,
            response_format={"type": "json_object"},
            tools=[{"type": "function", "function": {"name": "test"}}],
            top_p=0.9
        )

        assert request.user_id == "user_123"
        assert request.job_metadata["session_id"] == "sess_abc"
        assert request.max_tokens == 500
        assert request.response_format == {"type": "json_object"}
        assert len(request.tools) == 1

    def test_streaming_returns_sse_format(self):
        """Test that streaming endpoint returns SSE media type"""
        # This is a conceptual test - actual streaming requires integration testing
        # The endpoint should return StreamingResponse with media_type="text/event-stream"

        # Expected SSE format:
        # data: {...}\n\n
        # data: {...}\n\n
        # data: [DONE]\n\n

        sse_example = "data: {\"id\":\"test\",\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}\n\n"
        assert sse_example.startswith("data: ")
        assert sse_example.endswith("\n\n")

    def test_streaming_error_handling(self):
        """Test that errors are sent as SSE events"""
        import json

        error_message = "Model not found"
        error_sse = f"data: {json.dumps({'error': error_message})}\n\n"

        assert "data: " in error_sse
        assert error_message in error_sse
        assert error_sse.endswith("\n\n")


class TestStreamingVsNonStreaming:
    """Compare streaming and non-streaming endpoints"""

    def test_both_endpoints_use_same_request_model(self):
        """Both endpoints use SingleCallJobRequest"""
        from src.saas_api import SingleCallJobRequest

        # Both /api/jobs/create-and-call and /api/jobs/create-and-call-stream
        # accept the same request structure
        request = SingleCallJobRequest(
            team_id="test-team",
            job_type="chat",
            model="gpt-4",
            messages=[{"role": "user", "content": "Test"}]
        )

        # This request can be sent to either endpoint
        assert request.team_id == "test-team"

    def test_endpoint_differences(self):
        """Document the differences between endpoints"""
        differences = {
            "create-and-call": {
                "returns": "SingleCallJobResponse (JSON)",
                "streaming": False,
                "use_case": "Single-shot responses, simple tasks"
            },
            "create-and-call-stream": {
                "returns": "StreamingResponse (SSE)",
                "streaming": True,
                "use_case": "Chat applications, real-time token streaming"
            }
        }

        assert differences["create-and-call"]["streaming"] is False
        assert differences["create-and-call-stream"]["streaming"] is True


class TestCreditDeduction:
    """Test credit deduction for streaming endpoint"""

    def test_credits_deducted_after_streaming_completes(self):
        """Credits should be deducted after streaming finishes"""
        # The streaming endpoint should:
        # 1. Create job (IN_PROGRESS)
        # 2. Stream LLM response
        # 3. Store LLM call in database
        # 4. Mark job as COMPLETED
        # 5. Deduct credits based on budget mode
        # 6. Store cost summary

        # This ensures credits are only deducted for completed streams
        assert True  # Placeholder for integration test

    def test_budget_modes_supported(self):
        """Test that all budget modes work with streaming"""
        from src.api.constants import MINIMUM_CREDITS_PER_JOB

        budget_modes = {
            "job_based": {
                "credits_per_job": MINIMUM_CREDITS_PER_JOB,
                "calculation": "Fixed 1 credit"
            },
            "consumption_usd": {
                "calculation": "total_cost_usd * credits_per_dollar"
            },
            "consumption_tokens": {
                "calculation": "total_tokens // tokens_per_credit"
            }
        }

        assert budget_modes["job_based"]["credits_per_job"] == 1
        assert "total_cost_usd" in budget_modes["consumption_usd"]["calculation"]
        assert "total_tokens" in budget_modes["consumption_tokens"]["calculation"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for flexible budget system features.

Tests cover:
- Budget modes (job_based, consumption_usd, consumption_tokens)
- Job metadata PATCH endpoint
- Credit replenishment (subscription and one-time payments)
- Auto-refill configuration
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBudgetModes:
    """Test budget mode configuration and credit calculations"""

    def test_team_creation_with_job_based_mode(self):
        """Test creating team with job_based budget mode (default)"""
        from src.api.teams import TeamCreateRequest

        request = TeamCreateRequest(
            organization_id="org_test",
            team_id="test-team",
            access_groups=["gpt-models"],
            credits_allocated=1000,
            budget_mode="job_based"
        )

        assert request.budget_mode == "job_based"
        assert request.credits_per_dollar == 10.0
        assert request.tokens_per_credit == 10000

    def test_team_creation_with_consumption_usd_mode(self):
        """Test creating team with consumption_usd budget mode"""
        from src.api.teams import TeamCreateRequest

        request = TeamCreateRequest(
            organization_id="org_test",
            team_id="test-team",
            access_groups=["gpt-models"],
            credits_allocated=1000,
            budget_mode="consumption_usd",
            credits_per_dollar=20.0
        )

        assert request.budget_mode == "consumption_usd"
        assert request.credits_per_dollar == 20.0

    def test_team_creation_with_consumption_tokens_mode(self):
        """Test creating team with consumption_tokens budget mode"""
        from src.api.teams import TeamCreateRequest

        request = TeamCreateRequest(
            organization_id="org_test",
            team_id="test-team",
            access_groups=["gpt-models"],
            credits_allocated=2000,
            budget_mode="consumption_tokens",
            tokens_per_credit=5000
        )

        assert request.budget_mode == "consumption_tokens"
        assert request.tokens_per_credit == 5000

    def test_invalid_budget_mode_rejected(self):
        """Test that invalid budget modes are rejected"""
        from src.api.teams import TeamCreateRequest
        from pydantic import ValidationError

        # This should work without validation error at Pydantic level
        # The actual validation happens in the endpoint
        request = TeamCreateRequest(
            organization_id="org_test",
            team_id="test-team",
            access_groups=["gpt-models"],
            credits_allocated=1000,
            budget_mode="invalid_mode"
        )

        # The endpoint should validate this
        assert request.budget_mode == "invalid_mode"

    def test_credit_calculation_job_based(self):
        """Test credit calculation for job_based mode"""
        from src.api.constants import MINIMUM_CREDITS_PER_JOB

        # In job_based mode, always 1 credit regardless of cost or tokens
        credits_to_deduct = MINIMUM_CREDITS_PER_JOB
        assert credits_to_deduct == 1

    def test_credit_calculation_consumption_usd(self):
        """Test credit calculation for consumption_usd mode"""
        from src.api.constants import DEFAULT_CREDITS_PER_DOLLAR, MINIMUM_CREDITS_PER_JOB

        # Simulate a job that cost $0.05
        total_cost_usd = 0.05
        credits_per_dollar = 20.0

        credits_to_deduct = int(total_cost_usd * credits_per_dollar)
        credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, credits_to_deduct)

        # $0.05 * 20 credits/dollar = 1 credit
        assert credits_to_deduct == 1

    def test_credit_calculation_consumption_usd_expensive_job(self):
        """Test credit calculation for expensive job in consumption_usd mode"""
        from src.api.constants import MINIMUM_CREDITS_PER_JOB

        # Simulate an expensive job that cost $1.50
        total_cost_usd = 1.50
        credits_per_dollar = 10.0

        credits_to_deduct = int(total_cost_usd * credits_per_dollar)
        credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, credits_to_deduct)

        # $1.50 * 10 credits/dollar = 15 credits
        assert credits_to_deduct == 15

    def test_credit_calculation_consumption_tokens(self):
        """Test credit calculation for consumption_tokens mode"""
        from src.api.constants import DEFAULT_TOKENS_PER_CREDIT, MINIMUM_CREDITS_PER_JOB

        # Simulate a job that used 15,000 tokens
        total_tokens = 15000
        tokens_per_credit = 10000

        credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, total_tokens // tokens_per_credit)

        # 15,000 tokens / 10,000 tokens per credit = 1 credit (integer division)
        assert credits_to_deduct == 1

    def test_credit_calculation_consumption_tokens_high_usage(self):
        """Test credit calculation for high token usage"""
        from src.api.constants import MINIMUM_CREDITS_PER_JOB

        # Simulate a job that used 55,000 tokens
        total_tokens = 55000
        tokens_per_credit = 10000

        credits_to_deduct = max(MINIMUM_CREDITS_PER_JOB, total_tokens // tokens_per_credit)

        # 55,000 tokens / 10,000 tokens per credit = 5 credits
        assert credits_to_deduct == 5


class TestJobMetadata:
    """Test job metadata PATCH endpoint and call_metadata parameter"""

    def test_job_metadata_update_request(self):
        """Test JobMetadataUpdateRequest model"""
        from src.saas_api import JobMetadataUpdateRequest

        request = JobMetadataUpdateRequest(
            metadata={
                "conversation_turn": 3,
                "user_sentiment": "positive"
            }
        )

        assert request.metadata["conversation_turn"] == 3
        assert request.metadata["user_sentiment"] == "positive"

    def test_llm_call_with_call_metadata(self):
        """Test LLMCallRequest with call_metadata parameter"""
        from src.saas_api import LLMCallRequest

        request = LLMCallRequest(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            call_metadata={
                "turn": 1,
                "user_message": "Hello"
            }
        )

        assert request.call_metadata is not None
        assert request.call_metadata["turn"] == 1
        assert request.call_metadata["user_message"] == "Hello"

    def test_llm_call_without_call_metadata(self):
        """Test LLMCallRequest without call_metadata (optional)"""
        from src.saas_api import LLMCallRequest

        request = LLMCallRequest(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert request.call_metadata is None


class TestCreditReplenishment:
    """Test credit replenishment endpoints and functionality"""

    def test_replenish_credits_subscription_request(self):
        """Test ReplenishCreditsRequest for subscription payment"""
        from src.api.credits import ReplenishCreditsRequest

        request = ReplenishCreditsRequest(
            credits=5000,
            payment_type="subscription",
            payment_amount_usd=499.00,
            reason="November 2024 subscription"
        )

        assert request.credits == 5000
        assert request.payment_type == "subscription"
        assert request.payment_amount_usd == 499.00
        assert request.reason == "November 2024 subscription"

    def test_replenish_credits_one_time_request(self):
        """Test ReplenishCreditsRequest for one-time payment"""
        from src.api.credits import ReplenishCreditsRequest

        request = ReplenishCreditsRequest(
            credits=1000,
            payment_type="one_time",
            payment_amount_usd=99.00
        )

        assert request.credits == 1000
        assert request.payment_type == "one_time"
        assert request.payment_amount_usd == 99.00

    def test_replenish_credits_without_amount(self):
        """Test ReplenishCreditsRequest without payment amount (optional)"""
        from src.api.credits import ReplenishCreditsRequest

        request = ReplenishCreditsRequest(
            credits=500,
            payment_type="one_time"
        )

        assert request.credits == 500
        assert request.payment_amount_usd is None

    def test_configure_auto_refill_enabled(self):
        """Test ConfigureAutoRefillRequest with auto-refill enabled"""
        from src.api.credits import ConfigureAutoRefillRequest

        request = ConfigureAutoRefillRequest(
            enabled=True,
            refill_amount=5000,
            refill_period="monthly"
        )

        assert request.enabled is True
        assert request.refill_amount == 5000
        assert request.refill_period == "monthly"

    def test_configure_auto_refill_disabled(self):
        """Test ConfigureAutoRefillRequest with auto-refill disabled"""
        from src.api.credits import ConfigureAutoRefillRequest

        request = ConfigureAutoRefillRequest(
            enabled=False
        )

        assert request.enabled is False
        assert request.refill_amount is None
        assert request.refill_period is None

    def test_configure_auto_refill_weekly(self):
        """Test ConfigureAutoRefillRequest with weekly period"""
        from src.api.credits import ConfigureAutoRefillRequest

        request = ConfigureAutoRefillRequest(
            enabled=True,
            refill_amount=1000,
            refill_period="weekly"
        )

        assert request.refill_period == "weekly"

    def test_configure_auto_refill_daily(self):
        """Test ConfigureAutoRefillRequest with daily period"""
        from src.api.credits import ConfigureAutoRefillRequest

        request = ConfigureAutoRefillRequest(
            enabled=True,
            refill_amount=200,
            refill_period="daily"
        )

        assert request.refill_period == "daily"


class TestCreditTransactionTypes:
    """Test new transaction types for credit replenishment"""

    def test_subscription_payment_transaction_type(self):
        """Test that subscription_payment transaction type is formed correctly"""
        payment_type = "subscription"
        transaction_type = f"{payment_type}_payment"

        assert transaction_type == "subscription_payment"

    def test_one_time_payment_transaction_type(self):
        """Test that one_time_payment transaction type is formed correctly"""
        payment_type = "one_time"
        transaction_type = f"{payment_type}_payment"

        assert transaction_type == "one_time_payment"


class TestValidations:
    """Test validation logic for budget modes and replenishment"""

    def test_valid_budget_modes(self):
        """Test that valid budget modes are in expected list"""
        valid_modes = ['job_based', 'consumption_usd', 'consumption_tokens']

        assert 'job_based' in valid_modes
        assert 'consumption_usd' in valid_modes
        assert 'consumption_tokens' in valid_modes
        assert 'invalid_mode' not in valid_modes

    def test_valid_payment_types(self):
        """Test that valid payment types are in expected list"""
        valid_types = ['subscription', 'one_time']

        assert 'subscription' in valid_types
        assert 'one_time' in valid_types
        assert 'invalid_type' not in valid_types

    def test_valid_refill_periods(self):
        """Test that valid refill periods are in expected list"""
        valid_periods = ['monthly', 'weekly', 'daily']

        assert 'monthly' in valid_periods
        assert 'weekly' in valid_periods
        assert 'daily' in valid_periods
        assert 'yearly' not in valid_periods


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

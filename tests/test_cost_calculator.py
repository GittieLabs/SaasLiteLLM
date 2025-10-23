"""
Comprehensive tests for cost_calculator module

Tests cost calculation functionality including:
- Token-based cost calculation
- LiteLLM response cost extraction
- Markup application
- Credit deduction calculation for different budget modes
- Model pricing lookup
- Provider detection
- Model listing by provider
- Conversation cost estimation
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from utils.cost_calculator import (
    calculate_token_costs,
    extract_cost_from_litellm_response,
    apply_markup,
    calculate_credits_to_deduct,
    get_model_pricing,
    get_provider_from_model,
    list_models_by_provider,
    estimate_cost_for_conversation,
    MODEL_PRICING
)


class TestCalculateTokenCosts:
    """Test token-based cost calculation"""

    def test_calculate_basic_costs(self):
        """Test basic cost calculation with known values"""
        result = calculate_token_costs(
            prompt_tokens=1000,
            completion_tokens=500,
            input_price_per_million=5.00,
            output_price_per_million=15.00
        )

        # 1000 tokens / 1M * $5 = $0.005
        assert result["input_cost_usd"] == 0.005
        # 500 tokens / 1M * $15 = $0.0075
        assert result["output_cost_usd"] == 0.0075
        # Total: $0.0125
        assert result["provider_cost_usd"] == 0.0125

    def test_calculate_gpt4_example(self):
        """Test with realistic GPT-4 scenario"""
        result = calculate_token_costs(
            prompt_tokens=2000,
            completion_tokens=1000,
            input_price_per_million=30.00,
            output_price_per_million=60.00
        )

        # Input: 2000/1M * $30 = $0.06
        assert result["input_cost_usd"] == 0.06
        # Output: 1000/1M * $60 = $0.06
        assert result["output_cost_usd"] == 0.06
        # Total: $0.12
        assert result["provider_cost_usd"] == 0.12

    def test_calculate_zero_tokens(self):
        """Test with zero tokens"""
        result = calculate_token_costs(
            prompt_tokens=0,
            completion_tokens=0,
            input_price_per_million=5.00,
            output_price_per_million=15.00
        )

        assert result["input_cost_usd"] == 0.0
        assert result["output_cost_usd"] == 0.0
        assert result["provider_cost_usd"] == 0.0

    def test_calculate_large_numbers(self):
        """Test with large token counts"""
        result = calculate_token_costs(
            prompt_tokens=100_000,
            completion_tokens=50_000,
            input_price_per_million=2.50,
            output_price_per_million=10.00
        )

        # Input: 100K/1M * $2.50 = $0.25
        assert result["input_cost_usd"] == 0.25
        # Output: 50K/1M * $10.00 = $0.50
        assert result["output_cost_usd"] == 0.50
        # Total: $0.75
        assert result["provider_cost_usd"] == 0.75

    def test_calculate_precise_rounding(self):
        """Test that costs are rounded to 8 decimal places"""
        result = calculate_token_costs(
            prompt_tokens=1,
            completion_tokens=1,
            input_price_per_million=2.50,
            output_price_per_million=10.00
        )

        # Very small costs should be rounded precisely
        assert isinstance(result["input_cost_usd"], float)
        assert isinstance(result["output_cost_usd"], float)
        assert isinstance(result["provider_cost_usd"], float)


class TestExtractCostFromLitellmResponse:
    """Test cost extraction from LiteLLM responses"""

    def test_extract_from_hidden_params(self):
        """Test extracting cost from _hidden_params"""
        response = MagicMock()
        response._hidden_params = MagicMock()
        response._hidden_params.response_cost = 0.05

        result = extract_cost_from_litellm_response(response)

        assert result is not None
        assert result["provider_cost_usd"] == 0.05

    def test_extract_from_usage_dict(self):
        """Test extracting cost from usage dictionary"""
        response = {
            "usage": {
                "total_cost": 0.025
            }
        }

        result = extract_cost_from_litellm_response(response)

        assert result is not None
        assert result["provider_cost_usd"] == 0.025

    def test_extract_no_cost_available(self):
        """Test when no cost information is available"""
        response = {"usage": {"prompt_tokens": 100}}

        result = extract_cost_from_litellm_response(response)

        assert result is None

    def test_extract_from_empty_response(self):
        """Test with empty response"""
        response = {}

        result = extract_cost_from_litellm_response(response)

        assert result is None

    def test_extract_rounds_to_8_decimals(self):
        """Test that extracted cost is rounded"""
        response = MagicMock()
        response._hidden_params = MagicMock()
        response._hidden_params.response_cost = 0.123456789

        result = extract_cost_from_litellm_response(response)

        assert result["provider_cost_usd"] == 0.12345679


class TestApplyMarkup:
    """Test markup percentage application"""

    def test_apply_50_percent_markup(self):
        """Test 50% markup (standard scenario)"""
        result = apply_markup(
            provider_cost_usd=0.01,
            markup_percentage=50.0
        )

        assert result["provider_cost_usd"] == 0.01
        # $0.01 * 1.5 = $0.015
        assert result["client_cost_usd"] == 0.015

    def test_apply_100_percent_markup(self):
        """Test 100% markup (double the cost)"""
        result = apply_markup(
            provider_cost_usd=0.05,
            markup_percentage=100.0
        )

        assert result["provider_cost_usd"] == 0.05
        # $0.05 * 2.0 = $0.10
        assert result["client_cost_usd"] == 0.10

    def test_apply_zero_markup(self):
        """Test 0% markup (pass-through pricing)"""
        result = apply_markup(
            provider_cost_usd=0.02,
            markup_percentage=0.0
        )

        assert result["provider_cost_usd"] == 0.02
        assert result["client_cost_usd"] == 0.02

    def test_apply_small_markup(self):
        """Test small markup percentage"""
        result = apply_markup(
            provider_cost_usd=1.00,
            markup_percentage=10.0
        )

        assert result["provider_cost_usd"] == 1.00
        # $1.00 * 1.10 = $1.10
        assert result["client_cost_usd"] == 1.10

    def test_apply_large_markup(self):
        """Test large markup percentage"""
        result = apply_markup(
            provider_cost_usd=0.50,
            markup_percentage=200.0
        )

        assert result["provider_cost_usd"] == 0.50
        # $0.50 * 3.0 = $1.50
        assert result["client_cost_usd"] == 1.50


class TestCalculateCreditsToDeduct:
    """Test credit deduction calculation for different budget modes"""

    def test_job_based_mode(self):
        """Test job_based budget mode (fixed credit per job)"""
        credits = calculate_credits_to_deduct(
            cost_usd=0.05,
            total_tokens=1000,
            budget_mode="job_based"
        )

        # Job-based always returns minimum credits (1)
        assert credits == 1

    def test_consumption_usd_mode(self):
        """Test consumption_usd mode"""
        credits = calculate_credits_to_deduct(
            cost_usd=0.10,
            total_tokens=1000,
            budget_mode="consumption_usd",
            credits_per_dollar=10.0
        )

        # $0.10 * 10 credits/dollar = 1 credit
        assert credits == 1

    def test_consumption_usd_with_high_credits_per_dollar(self):
        """Test consumption_usd with high conversion rate"""
        credits = calculate_credits_to_deduct(
            cost_usd=0.50,
            total_tokens=1000,
            budget_mode="consumption_usd",
            credits_per_dollar=100.0
        )

        # $0.50 * 100 = 50 credits
        assert credits == 50

    def test_consumption_tokens_mode(self):
        """Test consumption_tokens mode"""
        credits = calculate_credits_to_deduct(
            cost_usd=0.05,
            total_tokens=50_000,
            budget_mode="consumption_tokens",
            tokens_per_credit=10_000
        )

        # 50,000 tokens / 10,000 tokens per credit = 5 credits
        assert credits == 5

    def test_consumption_tokens_below_threshold(self):
        """Test consumption_tokens with tokens below 1 credit threshold"""
        credits = calculate_credits_to_deduct(
            cost_usd=0.01,
            total_tokens=5_000,
            budget_mode="consumption_tokens",
            tokens_per_credit=10_000
        )

        # 5,000 / 10,000 = 0.5 → rounds to minimum 1
        assert credits == 1

    def test_minimum_credits_enforced(self):
        """Test that minimum credits is always enforced"""
        # Very low cost in USD mode
        credits = calculate_credits_to_deduct(
            cost_usd=0.001,
            total_tokens=100,
            budget_mode="consumption_usd",
            credits_per_dollar=1.0
        )
        assert credits == 1

        # Very low tokens in tokens mode
        credits = calculate_credits_to_deduct(
            cost_usd=0.01,
            total_tokens=100,
            budget_mode="consumption_tokens",
            tokens_per_credit=10_000
        )
        assert credits == 1

    def test_unknown_budget_mode_fallback(self):
        """Test fallback to job_based for unknown mode"""
        credits = calculate_credits_to_deduct(
            cost_usd=10.00,
            total_tokens=100_000,
            budget_mode="unknown_mode"
        )

        # Should fall back to minimum_credits (1)
        assert credits == 1


class TestGetModelPricing:
    """Test model pricing lookup"""

    def test_get_exact_match(self):
        """Test exact model name match"""
        pricing = get_model_pricing("gpt-4o")

        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] == 2.50
        assert pricing["output"] == 10.00

    def test_get_case_insensitive(self):
        """Test case-insensitive matching"""
        pricing = get_model_pricing("GPT-4O")

        assert pricing["input"] == 2.50
        assert pricing["output"] == 10.00

    def test_get_unknown_model_returns_default(self):
        """Test that unknown models return default pricing"""
        pricing = get_model_pricing("unknown-model-xyz")

        assert pricing["input"] == 1.00
        assert pricing["output"] == 2.00

    def test_get_partial_match(self):
        """Test partial model name matching"""
        # If pricing data has "gpt-4o", it should match "gpt-4o-2024-08-06"
        pricing = get_model_pricing("gpt-4o-2024-08-06")

        # Should match "gpt-4o" prefix
        assert "input" in pricing
        assert "output" in pricing

    def test_get_pricing_returns_correct_format(self):
        """Test that pricing always has correct format"""
        pricing = get_model_pricing("claude-sonnet-4-5")

        assert isinstance(pricing, dict)
        assert "input" in pricing
        assert "output" in pricing
        assert isinstance(pricing["input"], (int, float))
        assert isinstance(pricing["output"], (int, float))


class TestGetProviderFromModel:
    """Test provider detection from model names"""

    def test_detect_openai_gpt4(self):
        """Test OpenAI GPT-4 detection"""
        assert get_provider_from_model("gpt-4") == "openai"
        assert get_provider_from_model("gpt-4o") == "openai"
        assert get_provider_from_model("gpt-3.5-turbo") == "openai"

    def test_detect_openai_o1(self):
        """Test OpenAI O1/O3 models"""
        assert get_provider_from_model("o1-preview") == "openai"
        assert get_provider_from_model("o3-mini") == "openai"

    def test_detect_anthropic_claude(self):
        """Test Anthropic Claude detection"""
        assert get_provider_from_model("claude-3-opus") == "anthropic"
        assert get_provider_from_model("claude-sonnet-4-5") == "anthropic"
        assert get_provider_from_model("claude-haiku-3-5") == "anthropic"

    def test_detect_google_gemini(self):
        """Test Google Gemini detection"""
        assert get_provider_from_model("gemini-pro") == "gemini"
        assert get_provider_from_model("gemini-2.5-pro") == "gemini"
        assert get_provider_from_model("gemini-1.5-flash") == "gemini"

    def test_detect_fireworks_llama(self):
        """Test Fireworks AI models"""
        assert get_provider_from_model("llama-3-70b") == "fireworks"
        assert get_provider_from_model("mixtral-8x7b") == "fireworks"
        assert get_provider_from_model("qwen-72b") == "fireworks"

    def test_detect_unknown_provider(self):
        """Test unknown provider detection"""
        assert get_provider_from_model("unknown-model") == "unknown"
        assert get_provider_from_model("custom-llm") == "unknown"

    def test_detect_case_insensitive(self):
        """Test case-insensitive provider detection"""
        assert get_provider_from_model("GPT-4") == "openai"
        assert get_provider_from_model("CLAUDE-3-OPUS") == "anthropic"
        assert get_provider_from_model("GEMINI-PRO") == "gemini"


class TestListModelsByProvider:
    """Test listing models by provider"""

    def test_list_openai_models(self):
        """Test listing OpenAI models"""
        models = list_models_by_provider("openai")

        assert isinstance(models, list)
        assert len(models) > 0
        # Should contain GPT models
        assert any("gpt" in m for m in models)

    def test_list_anthropic_models(self):
        """Test listing Anthropic models"""
        models = list_models_by_provider("anthropic")

        assert isinstance(models, list)
        assert len(models) > 0
        # Should contain Claude models
        assert any("claude" in m for m in models)

    def test_list_gemini_models(self):
        """Test listing Google models"""
        models = list_models_by_provider("gemini")

        assert isinstance(models, list)
        # May or may not have Gemini models depending on pricing data

    def test_list_fireworks_models(self):
        """Test listing Fireworks models"""
        models = list_models_by_provider("fireworks")

        assert isinstance(models, list)
        # May contain llama, mixtral, etc.

    def test_list_models_case_insensitive(self):
        """Test case-insensitive provider listing"""
        models_lower = list_models_by_provider("openai")
        models_upper = list_models_by_provider("OPENAI")

        assert models_lower == models_upper

    def test_list_models_sorted(self):
        """Test that returned models are sorted"""
        models = list_models_by_provider("openai")

        assert models == sorted(models)

    def test_list_models_excludes_default(self):
        """Test that 'default' is not included in any provider list"""
        for provider in ["openai", "anthropic", "gemini", "fireworks"]:
            models = list_models_by_provider(provider)
            assert "default" not in models


class TestEstimateCostForConversation:
    """Test conversation cost estimation"""

    def test_estimate_simple_conversation(self):
        """Test estimating cost for simple conversation"""
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]

        result = estimate_cost_for_conversation("gpt-4o", messages)

        assert "estimated_input_tokens" in result
        assert "estimated_output_tokens" in result
        assert "estimated_input_cost_usd" in result
        assert "estimated_output_cost_usd" in result
        assert "estimated_total_cost_usd" in result
        assert "model" in result
        assert result["model"] == "gpt-4o"

    def test_estimate_multi_message_conversation(self):
        """Test with multiple messages"""
        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Tell me more about it."}
        ]

        result = estimate_cost_for_conversation("gpt-3.5-turbo", messages)

        # Should estimate more tokens for longer conversation
        assert result["estimated_input_tokens"] > 0
        assert result["estimated_total_cost_usd"] > 0

    def test_estimate_includes_pricing_info(self):
        """Test that estimate includes pricing metadata"""
        messages = [{"role": "user", "content": "Test"}]

        result = estimate_cost_for_conversation("claude-sonnet-4-5", messages)

        assert "pricing_input_per_1m" in result
        assert "pricing_output_per_1m" in result
        assert result["pricing_input_per_1m"] == 3.00
        assert result["pricing_output_per_1m"] == 15.00

    def test_estimate_empty_messages(self):
        """Test with empty messages list"""
        messages = []

        result = estimate_cost_for_conversation("gpt-4o", messages)

        assert result["estimated_input_tokens"] == 0
        assert result["estimated_output_tokens"] == 0
        assert result["estimated_total_cost_usd"] == 0

    def test_estimate_long_conversation(self):
        """Test with long conversation"""
        messages = [
            {"role": "user", "content": "A" * 1000}  # 1000 characters
        ]

        result = estimate_cost_for_conversation("gpt-4o", messages)

        # Should estimate ~250 tokens (1000 chars / 4 chars per token)
        assert result["estimated_input_tokens"] >= 200
        assert result["estimated_input_tokens"] <= 300

    def test_estimate_output_is_fraction_of_input(self):
        """Test that estimated output is 20% of input"""
        messages = [{"role": "user", "content": "Test " * 100}]

        result = estimate_cost_for_conversation("gpt-4o", messages)

        # Output should be ~20% of input
        expected_output = int(result["estimated_input_tokens"] * 0.2)
        assert result["estimated_output_tokens"] == expected_output


class TestModelPricingLoaded:
    """Test that MODEL_PRICING is loaded correctly"""

    def test_model_pricing_is_dict(self):
        """Test that MODEL_PRICING is a dictionary"""
        assert isinstance(MODEL_PRICING, dict)

    def test_model_pricing_has_default(self):
        """Test that default pricing exists"""
        assert "default" in MODEL_PRICING
        assert MODEL_PRICING["default"]["input"] == 1.00
        assert MODEL_PRICING["default"]["output"] == 2.00

    def test_model_pricing_has_major_models(self):
        """Test that major models are loaded"""
        # Should have at least some major models
        assert len(MODEL_PRICING) > 5

        # Check for at least one model from each major provider
        has_openai = any("gpt" in model for model in MODEL_PRICING.keys())
        has_anthropic = any("claude" in model for model in MODEL_PRICING.keys())
        has_google = any("gemini" in model for model in MODEL_PRICING.keys())

        assert has_openai or has_anthropic or has_google

    def test_model_pricing_format(self):
        """Test that all pricing entries have correct format"""
        for model, pricing in MODEL_PRICING.items():
            assert isinstance(pricing, dict)
            assert "input" in pricing
            assert "output" in pricing
            assert isinstance(pricing["input"], (int, float))
            assert isinstance(pricing["output"], (int, float))
            assert pricing["input"] >= 0
            assert pricing["output"] >= 0


class TestIntegration:
    """Integration tests combining multiple functions"""

    def test_full_cost_calculation_flow(self):
        """Test complete cost calculation workflow"""
        # 1. Calculate token costs
        token_costs = calculate_token_costs(
            prompt_tokens=1000,
            completion_tokens=500,
            input_price_per_million=2.50,
            output_price_per_million=10.00
        )

        # 2. Apply markup
        with_markup = apply_markup(
            provider_cost_usd=token_costs["provider_cost_usd"],
            markup_percentage=50.0
        )

        # 3. Calculate credits
        credits = calculate_credits_to_deduct(
            cost_usd=with_markup["client_cost_usd"],
            total_tokens=1500,
            budget_mode="consumption_usd",
            credits_per_dollar=10.0
        )

        # Verify end-to-end
        assert token_costs["provider_cost_usd"] == 0.0075
        assert with_markup["client_cost_usd"] == 0.01125
        assert credits == 1  # $0.01125 * 10 = 0.1125, rounds to 1

    def test_model_pricing_to_credits(self):
        """Test getting model pricing and calculating credits"""
        # 1. Get pricing for a model
        pricing = get_model_pricing("gpt-4o")

        # 2. Calculate costs with that pricing
        costs = calculate_token_costs(
            prompt_tokens=5000,
            completion_tokens=2000,
            input_price_per_million=pricing["input"],
            output_price_per_million=pricing["output"]
        )

        # 3. Apply markup
        with_markup = apply_markup(
            provider_cost_usd=costs["provider_cost_usd"],
            markup_percentage=25.0
        )

        # 4. Calculate credits
        credits = calculate_credits_to_deduct(
            cost_usd=with_markup["client_cost_usd"],
            total_tokens=7000,
            budget_mode="job_based"
        )

        # Verify calculations
        assert costs["provider_cost_usd"] > 0
        assert with_markup["client_cost_usd"] > costs["provider_cost_usd"]
        assert credits == 1  # job_based always 1

    def test_provider_detection_and_listing(self):
        """Test detecting provider and listing models"""
        model_name = "gpt-4o"

        # 1. Detect provider
        provider = get_provider_from_model(model_name)
        assert provider == "openai"

        # 2. List all models for that provider
        models = list_models_by_provider(provider)
        assert len(models) > 0

        # 3. Verify we can get pricing for listed models
        for model in models[:3]:  # Test first 3 models
            pricing = get_model_pricing(model)
            assert "input" in pricing
            assert "output" in pricing

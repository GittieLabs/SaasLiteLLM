"""
Unit tests for Phase 3 pricing helper functions in cost_calculator.py

Tests the new provider-specific pricing system and helper functions added
as part of LiteLLM proxy removal Phase 3.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.cost_calculator import (
    get_model_pricing,
    get_provider_from_model,
    list_models_by_provider,
    estimate_cost_for_conversation
)


class TestGetModelPricing:
    """Test the enhanced get_model_pricing function"""

    def test_exact_match_openai(self):
        """Test exact match for OpenAI models"""
        pricing = get_model_pricing("gpt-4o")
        assert pricing["input"] == 5.00
        assert pricing["output"] == 20.00

    def test_exact_match_anthropic(self):
        """Test exact match for Anthropic models"""
        pricing = get_model_pricing("claude-3-opus")
        assert pricing["input"] == 15.00
        assert pricing["output"] == 75.00

    def test_exact_match_gemini(self):
        """Test exact match for Gemini models"""
        pricing = get_model_pricing("gemini-1.5-flash")
        assert pricing["input"] == 0.15
        assert pricing["output"] == 0.60

    def test_partial_match_gpt4(self):
        """Test partial matching for GPT-4 variants"""
        # Should match "gpt-4" pricing
        pricing = get_model_pricing("gpt-4-0613")
        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] > 0

    def test_partial_match_claude(self):
        """Test partial matching for Claude variants"""
        pricing = get_model_pricing("claude-3-opus-20240229")
        assert "input" in pricing
        assert "output" in pricing

    def test_case_insensitive_matching(self):
        """Test that model name matching is case-insensitive"""
        pricing_lower = get_model_pricing("gpt-4o")
        pricing_upper = get_model_pricing("GPT-4O")
        pricing_mixed = get_model_pricing("Gpt-4o")

        assert pricing_lower == pricing_upper == pricing_mixed

    def test_whitespace_handling(self):
        """Test that whitespace is trimmed"""
        pricing_no_space = get_model_pricing("gpt-4o")
        pricing_with_space = get_model_pricing("  gpt-4o  ")

        assert pricing_no_space == pricing_with_space

    def test_unknown_model_returns_default(self):
        """Test that unknown models return default pricing"""
        pricing = get_model_pricing("completely-unknown-model-xyz")
        assert pricing["input"] == 1.00
        assert pricing["output"] == 2.00

    def test_longest_match_first(self):
        """Test that longer matches are preferred over shorter ones"""
        # "gpt-4o-mini" should match exactly, not just "gpt-4"
        pricing = get_model_pricing("gpt-4o-mini")
        assert pricing["input"] == 0.15  # gpt-4o-mini pricing, not gpt-4


class TestGetProviderFromModel:
    """Test provider detection from model names"""

    def test_detect_openai_gpt4(self):
        """Test detection of OpenAI GPT-4 models"""
        assert get_provider_from_model("gpt-4") == "openai"
        assert get_provider_from_model("gpt-4o") == "openai"
        assert get_provider_from_model("gpt-4-turbo") == "openai"

    def test_detect_openai_gpt35(self):
        """Test detection of OpenAI GPT-3.5 models"""
        assert get_provider_from_model("gpt-3.5-turbo") == "openai"

    def test_detect_openai_o1(self):
        """Test detection of OpenAI O1 models"""
        assert get_provider_from_model("o1-preview") == "openai"
        assert get_provider_from_model("o1-mini") == "openai"

    def test_detect_openai_o3(self):
        """Test detection of OpenAI O3 models"""
        assert get_provider_from_model("o3-mini") == "openai"

    def test_detect_anthropic_claude(self):
        """Test detection of Anthropic Claude models"""
        assert get_provider_from_model("claude-3-opus") == "anthropic"
        assert get_provider_from_model("claude-3-sonnet") == "anthropic"
        assert get_provider_from_model("claude-2") == "anthropic"
        assert get_provider_from_model("claude-4.5-sonnet") == "anthropic"

    def test_detect_gemini(self):
        """Test detection of Google Gemini models"""
        assert get_provider_from_model("gemini-pro") == "gemini"
        assert get_provider_from_model("gemini-1.5-pro") == "gemini"
        assert get_provider_from_model("gemini-2.5-pro") == "gemini"

    def test_detect_fireworks_llama(self):
        """Test detection of Fireworks Llama models"""
        assert get_provider_from_model("llama-v3-70b") == "fireworks"
        assert get_provider_from_model("llama-v3p1-8b") == "fireworks"

    def test_detect_fireworks_mixtral(self):
        """Test detection of Fireworks Mixtral models"""
        assert get_provider_from_model("mixtral-8x7b") == "fireworks"
        assert get_provider_from_model("mixtral-8x22b") == "fireworks"

    def test_detect_fireworks_qwen(self):
        """Test detection of Fireworks Qwen models"""
        assert get_provider_from_model("qwen-2.5-72b") == "fireworks"

    def test_detect_fireworks_yi(self):
        """Test detection of Fireworks Yi models"""
        assert get_provider_from_model("yi-large") == "fireworks"

    def test_case_insensitive_provider_detection(self):
        """Test that provider detection is case-insensitive"""
        assert get_provider_from_model("GPT-4") == "openai"
        assert get_provider_from_model("Claude-3-Opus") == "anthropic"
        assert get_provider_from_model("GEMINI-PRO") == "gemini"

    def test_unknown_model_returns_unknown(self):
        """Test that unknown models return 'unknown'"""
        assert get_provider_from_model("completely-unknown-xyz") == "unknown"


class TestListModelsByProvider:
    """Test listing models by provider"""

    def test_list_openai_models(self):
        """Test listing OpenAI models"""
        models = list_models_by_provider("openai")
        assert len(models) > 0
        assert "gpt-4o" in models
        assert "gpt-3.5-turbo" in models
        assert all(get_provider_from_model(m) == "openai" for m in models)

    def test_list_anthropic_models(self):
        """Test listing Anthropic models"""
        models = list_models_by_provider("anthropic")
        assert len(models) > 0
        assert "claude-3-opus" in models
        assert "claude-3-sonnet" in models
        assert all(get_provider_from_model(m) == "anthropic" for m in models)

    def test_list_gemini_models(self):
        """Test listing Gemini models"""
        models = list_models_by_provider("gemini")
        assert len(models) > 0
        assert "gemini-1.5-pro" in models
        assert all(get_provider_from_model(m) == "gemini" for m in models)

    def test_list_fireworks_models(self):
        """Test listing Fireworks models"""
        models = list_models_by_provider("fireworks")
        assert len(models) > 0
        assert any("llama" in m for m in models)
        assert any("mixtral" in m for m in models)
        assert all(get_provider_from_model(m) == "fireworks" for m in models)

    def test_case_insensitive_provider_name(self):
        """Test that provider name is case-insensitive"""
        models_lower = list_models_by_provider("openai")
        models_upper = list_models_by_provider("OPENAI")
        models_mixed = list_models_by_provider("OpenAI")

        assert models_lower == models_upper == models_mixed

    def test_models_are_sorted(self):
        """Test that returned models are sorted"""
        models = list_models_by_provider("openai")
        assert models == sorted(models)

    def test_no_default_model_in_list(self):
        """Test that 'default' is not included in model lists"""
        for provider in ["openai", "anthropic", "gemini", "fireworks"]:
            models = list_models_by_provider(provider)
            assert "default" not in models

    def test_unknown_provider_returns_empty_list(self):
        """Test that unknown providers return empty list"""
        models = list_models_by_provider("completely-unknown-provider")
        assert models == []


class TestEstimateCostForConversation:
    """Test cost estimation for conversations"""

    def test_estimate_simple_conversation(self):
        """Test cost estimation for a simple conversation"""
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ]

        estimate = estimate_cost_for_conversation("gpt-4o", messages)

        # Check all required fields are present
        assert "estimated_input_tokens" in estimate
        assert "estimated_output_tokens" in estimate
        assert "estimated_input_cost_usd" in estimate
        assert "estimated_output_cost_usd" in estimate
        assert "estimated_total_cost_usd" in estimate
        assert "model" in estimate
        assert "pricing_input_per_1m" in estimate
        assert "pricing_output_per_1m" in estimate

        # Check values are reasonable
        assert estimate["estimated_input_tokens"] > 0
        assert estimate["estimated_output_tokens"] > 0
        assert estimate["estimated_total_cost_usd"] > 0

    def test_estimate_with_different_models(self):
        """Test that different models produce different cost estimates"""
        messages = [{"role": "user", "content": "Test message"}]

        gpt4_estimate = estimate_cost_for_conversation("gpt-4", messages)
        gpt35_estimate = estimate_cost_for_conversation("gpt-3.5-turbo", messages)

        # GPT-4 should be more expensive than GPT-3.5
        assert gpt4_estimate["estimated_total_cost_usd"] > gpt35_estimate["estimated_total_cost_usd"]

    def test_estimate_scales_with_message_length(self):
        """Test that costs scale with message length"""
        short_messages = [{"role": "user", "content": "Hi"}]
        long_messages = [{"role": "user", "content": "This is a much longer message " * 100}]

        short_estimate = estimate_cost_for_conversation("gpt-4o", short_messages)
        long_estimate = estimate_cost_for_conversation("gpt-4o", long_messages)

        assert long_estimate["estimated_total_cost_usd"] > short_estimate["estimated_total_cost_usd"]
        assert long_estimate["estimated_input_tokens"] > short_estimate["estimated_input_tokens"]

    def test_estimate_includes_model_name(self):
        """Test that estimate includes the model name"""
        messages = [{"role": "user", "content": "Test"}]
        estimate = estimate_cost_for_conversation("claude-3-opus", messages)

        assert estimate["model"] == "claude-3-opus"

    def test_estimate_includes_pricing_info(self):
        """Test that estimate includes pricing per 1M tokens"""
        messages = [{"role": "user", "content": "Test"}]
        estimate = estimate_cost_for_conversation("gpt-4o", messages)

        assert estimate["pricing_input_per_1m"] == 5.00
        assert estimate["pricing_output_per_1m"] == 20.00

    def test_estimate_output_tokens_ratio(self):
        """Test that output tokens are estimated as 20% of input"""
        messages = [{"role": "user", "content": "Test message"}]
        estimate = estimate_cost_for_conversation("gpt-4o", messages)

        # Output tokens should be roughly 20% of input tokens
        expected_output = int(estimate["estimated_input_tokens"] * 0.2)
        assert estimate["estimated_output_tokens"] == expected_output

    def test_estimate_with_empty_messages(self):
        """Test cost estimation with empty messages"""
        messages = []
        estimate = estimate_cost_for_conversation("gpt-4o", messages)

        # Should still return a valid estimate structure, just with 0 tokens
        assert estimate["estimated_input_tokens"] == 0
        assert estimate["estimated_input_cost_usd"] == 0

    def test_estimate_cost_precision(self):
        """Test that costs are rounded to 6 decimal places"""
        messages = [{"role": "user", "content": "Test"}]
        estimate = estimate_cost_for_conversation("gpt-4o", messages)

        # Check that costs are rounded (have at most 6 decimal places)
        input_cost_str = str(estimate["estimated_input_cost_usd"])
        output_cost_str = str(estimate["estimated_output_cost_usd"])
        total_cost_str = str(estimate["estimated_total_cost_usd"])

        # If there's a decimal point, check precision
        if "." in input_cost_str:
            assert len(input_cost_str.split(".")[1]) <= 6
        if "." in output_cost_str:
            assert len(output_cost_str.split(".")[1]) <= 6
        if "." in total_cost_str:
            assert len(total_cost_str.split(".")[1]) <= 6


class TestPricingDataCompleteness:
    """Test that pricing data is comprehensive"""

    def test_all_providers_have_models(self):
        """Test that all providers have at least one model"""
        providers = ["openai", "anthropic", "gemini", "fireworks"]
        for provider in providers:
            models = list_models_by_provider(provider)
            assert len(models) > 0, f"Provider {provider} has no models"

    def test_all_models_have_valid_pricing(self):
        """Test that all models have valid pricing (positive values)"""
        providers = ["openai", "anthropic", "gemini", "fireworks"]
        for provider in providers:
            models = list_models_by_provider(provider)
            for model in models:
                pricing = get_model_pricing(model)
                assert pricing["input"] > 0, f"Model {model} has invalid input pricing"
                assert pricing["output"] > 0, f"Model {model} has invalid output pricing"

    def test_openai_flagship_models_present(self):
        """Test that key OpenAI models are in pricing table"""
        models = list_models_by_provider("openai")
        flagship_models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview"]
        for model in flagship_models:
            assert model in models, f"Flagship model {model} not found in pricing"

    def test_anthropic_flagship_models_present(self):
        """Test that key Anthropic models are in pricing table"""
        models = list_models_by_provider("anthropic")
        flagship_models = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        for model in flagship_models:
            assert model in models, f"Flagship model {model} not found in pricing"

    def test_gemini_flagship_models_present(self):
        """Test that key Gemini models are in pricing table"""
        models = list_models_by_provider("gemini")
        flagship_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
        for model in flagship_models:
            assert model in models, f"Flagship model {model} not found in pricing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

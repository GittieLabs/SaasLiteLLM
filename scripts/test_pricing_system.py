#!/usr/bin/env python3
"""
Local test script for pricing system validation

Tests:
1. JSON pricing file loads correctly
2. Pricing data is in correct format
3. All required models have pricing
4. Conversion math is accurate
5. Cost calculation works end-to-end

Run this BEFORE deploying to production to catch any pricing issues.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.pricing_loader import (
    load_pricing_from_json,
    get_pricing_metadata,
    reload_pricing,
    _get_pricing_file_path
)
from utils.cost_calculator import (
    calculate_token_costs,
    get_model_pricing,
    get_provider_from_model,
    apply_markup,
    calculate_credits_to_deduct,
    estimate_cost_for_conversation
)


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def test_pricing_file_exists():
    """Test 1: Verify pricing file exists"""
    print_header("Test 1: Pricing File Existence")

    pricing_file = _get_pricing_file_path()

    if pricing_file is None:
        print_error("Pricing file not found!")
        print_info("Expected location: <project_root>/llm_pricing_current.json")
        return False

    if not pricing_file.exists():
        print_error(f"Pricing file does not exist at: {pricing_file}")
        return False

    print_success(f"Pricing file found at: {pricing_file}")
    return True


def test_pricing_loads():
    """Test 2: Verify pricing data loads without errors"""
    print_header("Test 2: Pricing Data Loading")

    try:
        pricing = load_pricing_from_json()
        print_success(f"Pricing data loaded successfully ({len(pricing)} models)")

        # Check structure
        if not isinstance(pricing, dict):
            print_error("Pricing data is not a dictionary!")
            return False

        if len(pricing) == 0:
            print_error("Pricing data is empty!")
            return False

        print_success(f"Pricing data structure is valid")
        return True

    except Exception as e:
        print_error(f"Failed to load pricing: {e}")
        return False


def test_pricing_format():
    """Test 3: Verify all pricing entries have correct format"""
    print_header("Test 3: Pricing Format Validation")

    pricing = load_pricing_from_json()
    errors = []

    for model_name, prices in pricing.items():
        # Check it's a dict
        if not isinstance(prices, dict):
            errors.append(f"  {model_name}: not a dict (got {type(prices).__name__})")
            continue

        # Check required fields
        if "input" not in prices:
            errors.append(f"  {model_name}: missing 'input' field")
        if "output" not in prices:
            errors.append(f"  {model_name}: missing 'output' field")

        # Check values are numeric
        if "input" in prices and not isinstance(prices["input"], (int, float)):
            errors.append(f"  {model_name}: 'input' is not numeric")
        if "output" in prices and not isinstance(prices["output"], (int, float)):
            errors.append(f"  {model_name}: 'output' is not numeric")

        # Check values are non-negative
        if "input" in prices and prices["input"] < 0:
            errors.append(f"  {model_name}: 'input' is negative")
        if "output" in prices and prices["output"] < 0:
            errors.append(f"  {model_name}: 'output' is negative")

    if errors:
        print_error("Format validation failed:")
        for error in errors:
            print(error)
        return False

    print_success(f"All {len(pricing)} models have valid pricing format")
    return True


def test_required_models():
    """Test 4: Verify critical models have pricing"""
    print_header("Test 4: Critical Models Check")

    pricing = load_pricing_from_json()

    # Critical models that MUST have pricing
    critical_models = [
        "default",  # Fallback
        "gpt-4o",
        "gpt-4o-mini",
        "claude-sonnet-4-5",
    ]

    missing = []
    for model in critical_models:
        if model not in pricing:
            missing.append(model)

    if missing:
        print_error(f"Missing critical models: {', '.join(missing)}")
        return False

    print_success(f"All {len(critical_models)} critical models have pricing")

    # Show some example prices
    print_info("\nExample pricing (per 1M tokens):")
    for model in critical_models[:3]:
        prices = pricing[model]
        print(f"  {model}: ${prices['input']:.2f} in / ${prices['output']:.2f} out")

    return True


def test_conversion_accuracy():
    """Test 5: Verify per-token to per-million conversion is accurate"""
    print_header("Test 5: Pricing Conversion Accuracy")

    # Test with known values
    test_cases = [
        {
            "name": "gpt-4o",
            "expected_input": 2.50,
            "expected_output": 10.00,
        },
        {
            "name": "gpt-4o-mini",
            "expected_input": 0.15,
            "expected_output": 0.60,
        },
    ]

    pricing = load_pricing_from_json()

    all_passed = True
    for test in test_cases:
        model = test["name"]

        if model not in pricing:
            print_warning(f"{model}: Not in pricing data (may have been updated)")
            continue

        actual_input = pricing[model]["input"]
        actual_output = pricing[model]["output"]

        # Allow small floating point differences
        input_match = abs(actual_input - test["expected_input"]) < 0.01
        output_match = abs(actual_output - test["expected_output"]) < 0.01

        if input_match and output_match:
            print_success(f"{model}: Pricing correct (${actual_input:.2f}/${actual_output:.2f})")
        else:
            print_error(f"{model}: Pricing mismatch!")
            print(f"    Expected: ${test['expected_input']:.2f}/${test['expected_output']:.2f}")
            print(f"    Got:      ${actual_input:.2f}/${actual_output:.2f}")
            all_passed = False

    return all_passed


def test_cost_calculation():
    """Test 6: Verify cost calculation works end-to-end"""
    print_header("Test 6: Cost Calculation")

    try:
        # Test basic cost calculation
        costs = calculate_token_costs(
            prompt_tokens=1000,
            completion_tokens=500,
            input_price_per_million=2.50,
            output_price_per_million=10.00
        )

        expected_input = 0.0025  # 1000 / 1M * 2.50
        expected_output = 0.005  # 500 / 1M * 10.00
        expected_total = 0.0075

        if abs(costs["input_cost_usd"] - expected_input) < 0.0001:
            print_success(f"Input cost calculation correct: ${costs['input_cost_usd']:.6f}")
        else:
            print_error(f"Input cost wrong: expected ${expected_input:.6f}, got ${costs['input_cost_usd']:.6f}")
            return False

        if abs(costs["output_cost_usd"] - expected_output) < 0.0001:
            print_success(f"Output cost calculation correct: ${costs['output_cost_usd']:.6f}")
        else:
            print_error(f"Output cost wrong: expected ${expected_output:.6f}, got ${costs['output_cost_usd']:.6f}")
            return False

        if abs(costs["provider_cost_usd"] - expected_total) < 0.0001:
            print_success(f"Total cost calculation correct: ${costs['provider_cost_usd']:.6f}")
        else:
            print_error(f"Total cost wrong: expected ${expected_total:.6f}, got ${costs['provider_cost_usd']:.6f}")
            return False

        return True

    except Exception as e:
        print_error(f"Cost calculation failed: {e}")
        return False


def test_model_pricing_lookup():
    """Test 7: Verify model pricing lookup works"""
    print_header("Test 7: Model Pricing Lookup")

    try:
        # Test exact match
        pricing = get_model_pricing("gpt-4o")
        if pricing["input"] > 0 and pricing["output"] > 0:
            print_success(f"Exact match works: gpt-4o → ${pricing['input']:.2f}/${pricing['output']:.2f}")
        else:
            print_error("Exact match returned zero prices")
            return False

        # Test case insensitive
        pricing = get_model_pricing("GPT-4O")
        if pricing["input"] > 0 and pricing["output"] > 0:
            print_success(f"Case-insensitive match works: GPT-4O → ${pricing['input']:.2f}/${pricing['output']:.2f}")
        else:
            print_error("Case-insensitive match failed")
            return False

        # Test unknown model returns default
        pricing = get_model_pricing("unknown-model-xyz")
        if pricing["input"] == 1.00 and pricing["output"] == 2.00:
            print_success(f"Unknown model returns default: ${pricing['input']:.2f}/${pricing['output']:.2f}")
        else:
            print_error("Default pricing not returned for unknown model")
            return False

        return True

    except Exception as e:
        print_error(f"Model pricing lookup failed: {e}")
        return False


def test_provider_detection():
    """Test 8: Verify provider detection works"""
    print_header("Test 8: Provider Detection")

    test_cases = [
        ("gpt-4o", "openai"),
        ("claude-3-opus", "anthropic"),
        ("gemini-pro", "gemini"),
        ("llama-3-70b", "fireworks"),
        ("unknown-model", "unknown"),  # returns "unknown" for unrecognized models
    ]

    all_passed = True
    for model, expected_provider in test_cases:
        actual = get_provider_from_model(model)
        if actual == expected_provider:
            print_success(f"{model} → {actual}")
        else:
            print_error(f"{model}: expected {expected_provider}, got {actual}")
            all_passed = False

    return all_passed


def test_markup_application():
    """Test 9: Verify markup calculation works"""
    print_header("Test 9: Markup Application")

    try:
        # Test 50% markup
        result = apply_markup(provider_cost_usd=0.01, markup_percentage=50.0)
        expected = 0.015  # $0.01 * 1.5

        if abs(result["client_cost_usd"] - expected) < 0.0001:
            print_success(f"50% markup works: $0.01 → ${result['client_cost_usd']:.4f}")
        else:
            print_error(f"50% markup wrong: expected ${expected:.4f}, got ${result['client_cost_usd']:.4f}")
            return False

        # Test 0% markup
        result = apply_markup(provider_cost_usd=0.02, markup_percentage=0.0)
        if result["client_cost_usd"] == 0.02:
            print_success(f"0% markup works: $0.02 → ${result['client_cost_usd']:.4f}")
        else:
            print_error(f"0% markup wrong: expected $0.02, got ${result['client_cost_usd']:.4f}")
            return False

        return True

    except Exception as e:
        print_error(f"Markup calculation failed: {e}")
        return False


def test_credit_deduction():
    """Test 10: Verify credit deduction calculation"""
    print_header("Test 10: Credit Deduction Calculation")

    try:
        # Test job_based mode
        credits = calculate_credits_to_deduct(
            cost_usd=10.0,
            total_tokens=100000,
            budget_mode="job_based"
        )
        if credits == 1:
            print_success(f"job_based mode: always returns 1 credit")
        else:
            print_error(f"job_based mode wrong: expected 1, got {credits}")
            return False

        # Test consumption_usd mode
        credits = calculate_credits_to_deduct(
            cost_usd=0.10,
            total_tokens=1000,
            budget_mode="consumption_usd",
            credits_per_dollar=10.0
        )
        if credits == 1:
            print_success(f"consumption_usd mode: $0.10 * 10 = 1 credit")
        else:
            print_error(f"consumption_usd mode wrong: expected 1, got {credits}")
            return False

        # Test consumption_tokens mode
        credits = calculate_credits_to_deduct(
            cost_usd=0.01,
            total_tokens=50000,
            budget_mode="consumption_tokens",
            tokens_per_credit=10000
        )
        if credits == 5:
            print_success(f"consumption_tokens mode: 50K tokens / 10K = 5 credits")
        else:
            print_error(f"consumption_tokens mode wrong: expected 5, got {credits}")
            return False

        return True

    except Exception as e:
        print_error(f"Credit deduction calculation failed: {e}")
        return False


def test_end_to_end_scenario():
    """Test 11: Complete end-to-end pricing scenario"""
    print_header("Test 11: End-to-End Scenario")

    print_info("Simulating: User makes GPT-4o call with 1000 prompt + 500 completion tokens")

    try:
        # 1. Get model pricing
        pricing = get_model_pricing("gpt-4o")
        print_success(f"Step 1: Got pricing - ${pricing['input']:.2f}/${pricing['output']:.2f} per 1M tokens")

        # 2. Calculate token costs
        costs = calculate_token_costs(
            prompt_tokens=1000,
            completion_tokens=500,
            input_price_per_million=pricing["input"],
            output_price_per_million=pricing["output"]
        )
        print_success(f"Step 2: Calculated cost - ${costs['provider_cost_usd']:.6f}")

        # 3. Apply markup
        with_markup = apply_markup(
            provider_cost_usd=costs["provider_cost_usd"],
            markup_percentage=50.0
        )
        print_success(f"Step 3: Applied 50% markup - ${with_markup['client_cost_usd']:.6f}")

        # 4. Calculate credits to deduct
        credits = calculate_credits_to_deduct(
            cost_usd=with_markup["client_cost_usd"],
            total_tokens=1500,
            budget_mode="consumption_usd",
            credits_per_dollar=10.0
        )
        print_success(f"Step 4: Credits to deduct - {credits}")

        print_info("\n📊 Final Results:")
        print(f"  Provider Cost: ${costs['provider_cost_usd']:.6f}")
        print(f"  Client Cost:   ${with_markup['client_cost_usd']:.6f} (50% markup)")
        print(f"  Credits Used:  {credits}")

        return True

    except Exception as e:
        print_error(f"End-to-end scenario failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{'PRICING SYSTEM VALIDATION TEST SUITE'.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"\n{Colors.YELLOW}This test validates the pricing system before production deployment{Colors.END}\n")

    tests = [
        ("Pricing File Exists", test_pricing_file_exists),
        ("Pricing Data Loads", test_pricing_loads),
        ("Pricing Format Valid", test_pricing_format),
        ("Critical Models Present", test_required_models),
        ("Conversion Accuracy", test_conversion_accuracy),
        ("Cost Calculation", test_cost_calculation),
        ("Model Pricing Lookup", test_model_pricing_lookup),
        ("Provider Detection", test_provider_detection),
        ("Markup Application", test_markup_application),
        ("Credit Deduction", test_credit_deduction),
        ("End-to-End Scenario", test_end_to_end_scenario),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {status}  {name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED - Safe to deploy!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ TESTS FAILED - DO NOT DEPLOY!{Colors.END}")
        print(f"{Colors.RED}Fix the issues above before deploying to production{Colors.END}\n")
        return 1


if __name__ == "__main__":
    exit(main())

"""
Cost calculation utilities for LLM API calls

Handles:
- Extracting cost from LiteLLM responses
- Calculating per-token costs using pricing per 1M tokens
- Applying markup percentage for client billing
- Converting costs to credits based on team budget mode

Pricing data is loaded from llm_pricing_current.json at module import time.
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from .pricing_loader import load_pricing_from_json


def calculate_token_costs(
    prompt_tokens: int,
    completion_tokens: int,
    input_price_per_million: float,
    output_price_per_million: float
) -> Dict[str, float]:
    """
    Calculate costs based on token usage and model pricing.

    Args:
        prompt_tokens: Number of input/prompt tokens
        completion_tokens: Number of output/completion tokens
        input_price_per_million: Cost per 1M input tokens (e.g., $5.00 for $5 per 1M tokens)
        output_price_per_million: Cost per 1M output tokens

    Returns:
        Dictionary with input_cost, output_cost, and total_cost in USD

    Example:
        For gpt-4: input=$30/1M, output=$60/1M
        With 1000 prompt tokens and 500 completion tokens:
        - Input cost:  1000 / 1,000,000 * $30 = $0.03
        - Output cost: 500 / 1,000,000 * $60 = $0.03
        - Total: $0.06
    """
    # Calculate costs (pricing is per 1 MILLION tokens)
    input_cost = (prompt_tokens / 1_000_000) * input_price_per_million
    output_cost = (completion_tokens / 1_000_000) * output_price_per_million
    total_cost = input_cost + output_cost

    return {
        "input_cost_usd": round(input_cost, 8),
        "output_cost_usd": round(output_cost, 8),
        "provider_cost_usd": round(total_cost, 8)
    }


def extract_cost_from_litellm_response(response: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract cost information from LiteLLM API response.

    LiteLLM may return cost in various formats:
    - response._hidden_params.response_cost
    - response.usage.total_cost
    - Custom fields

    Args:
        response: LiteLLM API response dictionary

    Returns:
        Dictionary with cost fields or None if not available
    """
    # Try to extract from hidden params (LiteLLM internal)
    if hasattr(response, "_hidden_params"):
        if hasattr(response._hidden_params, "response_cost"):
            total_cost = float(response._hidden_params.response_cost)
            return {"provider_cost_usd": round(total_cost, 8)}

    # Try to extract from usage object
    if isinstance(response, dict) and "usage" in response:
        usage = response["usage"]
        if isinstance(usage, dict) and "total_cost" in usage:
            return {"provider_cost_usd": round(float(usage["total_cost"]), 8)}

    # If no cost found, return None
    # Caller should fall back to manual calculation
    return None


def apply_markup(
    provider_cost_usd: float,
    markup_percentage: float
) -> Dict[str, float]:
    """
    Apply markup percentage to provider cost.

    Args:
        provider_cost_usd: What LiteLLM charged us
        markup_percentage: Markup percentage (e.g., 50.0 = 50% markup, 100.0 = 2x cost)

    Returns:
        Dictionary with provider_cost_usd and client_cost_usd

    Example:
        Provider cost: $0.01
        Markup: 50%
        Client cost: $0.01 * (1 + 0.50) = $0.015
    """
    markup_multiplier = 1 + (markup_percentage / 100)
    client_cost = provider_cost_usd * markup_multiplier

    return {
        "provider_cost_usd": round(provider_cost_usd, 8),
        "client_cost_usd": round(client_cost, 8)
    }


def calculate_credits_to_deduct(
    cost_usd: float,
    total_tokens: int,
    budget_mode: str,
    credits_per_dollar: float = 1.0,
    tokens_per_credit: int = 10000,
    minimum_credits: int = 1
) -> int:
    """
    Calculate how many credits to deduct based on budget mode.

    Args:
        cost_usd: Total cost in USD (with markup applied)
        total_tokens: Total tokens used
        budget_mode: One of 'job_based', 'consumption_usd', 'consumption_tokens'
        credits_per_dollar: Conversion rate for consumption_usd mode
        tokens_per_credit: Conversion rate for consumption_tokens mode
        minimum_credits: Minimum credits to deduct (default 1)

    Returns:
        Number of credits to deduct

    Examples:
        job_based: Always returns minimum_credits (1)
        consumption_usd: cost=$0.05, credits_per_dollar=1 → 0.05 credits (rounded to 1 min)
        consumption_tokens: tokens=5000, tokens_per_credit=10000 → 0 credits (rounded to 1 min)
    """
    if budget_mode == "job_based":
        return minimum_credits
    elif budget_mode == "consumption_usd":
        credits = int(cost_usd * credits_per_dollar)
        return max(minimum_credits, credits)
    elif budget_mode == "consumption_tokens":
        credits = total_tokens // tokens_per_credit
        return max(minimum_credits, credits)
    else:
        # Unknown mode, fall back to job-based
        return minimum_credits


# Model pricing (per 1M tokens)
# Loaded from llm_pricing_current.json at module import time
# This replaces the previous hardcoded MODEL_PRICING dict
MODEL_PRICING = load_pricing_from_json()


def get_model_pricing(model_name: str) -> Dict[str, float]:
    """
    Get pricing for a specific model.

    Args:
        model_name: Name of the model (e.g., "gpt-4", "claude-3-opus")

    Returns:
        Dictionary with input and output prices per 1M tokens

    Examples:
        >>> get_model_pricing("gpt-4o")
        {'input': 5.00, 'output': 20.00}

        >>> get_model_pricing("claude-3-haiku")
        {'input': 0.25, 'output': 1.25}

        >>> get_model_pricing("unknown-model")
        {'input': 1.00, 'output': 2.00}
    """
    # Normalize model name
    model_name_lower = model_name.lower().strip()

    # Try exact match first
    if model_name_lower in MODEL_PRICING:
        return MODEL_PRICING[model_name_lower]

    # Try with original casing
    if model_name in MODEL_PRICING:
        return MODEL_PRICING[model_name]

    # Try partial match (e.g., "gpt-4-0613" matches "gpt-4")
    # Check longest matches first for better accuracy
    sorted_keys = sorted(MODEL_PRICING.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key == "default":
            continue
        if key in model_name_lower or model_name_lower.startswith(key):
            return MODEL_PRICING[key]

    # Fall back to default pricing
    return MODEL_PRICING["default"]


def get_provider_from_model(model_name: str) -> str:
    """
    Detect provider from model name.

    Args:
        model_name: Name of the model

    Returns:
        Provider name: "openai", "anthropic", "gemini", "fireworks", or "unknown"

    Examples:
        >>> get_provider_from_model("gpt-4")
        'openai'

        >>> get_provider_from_model("claude-3-opus")
        'anthropic'

        >>> get_provider_from_model("gemini-pro")
        'gemini'

        >>> get_provider_from_model("llama-3-70b")
        'fireworks'
    """
    model_lower = model_name.lower()

    # OpenAI models
    if any(prefix in model_lower for prefix in ["gpt-", "text-davinci", "o1-", "o3-"]):
        return "openai"

    # Anthropic models
    if "claude" in model_lower:
        return "anthropic"

    # Google Gemini models
    if "gemini" in model_lower:
        return "gemini"

    # Fireworks AI models
    if any(prefix in model_lower for prefix in ["llama", "mixtral", "qwen", "yi-"]):
        return "fireworks"

    return "unknown"


def list_models_by_provider(provider: str) -> list[str]:
    """
    List all models for a specific provider from our pricing table.

    Args:
        provider: Provider name ("openai", "anthropic", "gemini", "fireworks")

    Returns:
        List of model names for that provider

    Example:
        >>> models = list_models_by_provider("anthropic")
        >>> "claude-3-opus" in models
        True
    """
    provider_models = []

    for model_name in MODEL_PRICING.keys():
        if model_name == "default":
            continue
        detected_provider = get_provider_from_model(model_name)
        if detected_provider == provider.lower():
            provider_models.append(model_name)

    return sorted(provider_models)


def estimate_cost_for_conversation(
    model_name: str,
    messages: list,
    average_chars_per_token: int = 4
) -> Dict[str, float]:
    """
    Estimate the cost for a conversation before making the API call.

    This is an approximation based on character count. Actual token count
    may vary depending on the model's tokenizer.

    Args:
        model_name: Name of the model to use
        messages: List of message dictionaries with 'content' fields
        average_chars_per_token: Average characters per token (default: 4)

    Returns:
        Dictionary with estimated costs

    Example:
        >>> messages = [{"role": "user", "content": "Hello, how are you?"}]
        >>> cost = estimate_cost_for_conversation("gpt-4o", messages)
        >>> 'estimated_input_cost' in cost
        True
    """
    # Calculate total characters in messages
    total_chars = sum(len(msg.get("content", "")) for msg in messages)

    # Estimate tokens (rough approximation)
    estimated_tokens = total_chars // average_chars_per_token

    # Get model pricing
    pricing = get_model_pricing(model_name)

    # Calculate estimated input cost
    estimated_input_cost = (estimated_tokens / 1_000_000) * pricing["input"]

    # For output, estimate 20% of input length (conservative estimate)
    estimated_output_tokens = int(estimated_tokens * 0.2)
    estimated_output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]

    return {
        "estimated_input_tokens": estimated_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "estimated_input_cost_usd": round(estimated_input_cost, 6),
        "estimated_output_cost_usd": round(estimated_output_cost, 6),
        "estimated_total_cost_usd": round(estimated_input_cost + estimated_output_cost, 6),
        "model": model_name,
        "pricing_input_per_1m": pricing["input"],
        "pricing_output_per_1m": pricing["output"]
    }

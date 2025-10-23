"""
Pricing Loader - Loads LLM pricing from llm_pricing_current.json

This module provides a centralized way to load pricing data from the JSON file
and convert it to the format expected by cost_calculator.py
"""
import json
import os
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Cache pricing data to avoid repeated file reads
_PRICING_CACHE: Dict[str, Dict[str, float]] = None


def _get_pricing_file_path() -> Path:
    """
    Get the path to llm_pricing_current.json

    Looks for the file in the project root (parent of src/)
    """
    # Get the project root (parent of src/)
    current_file = Path(__file__)  # utils/pricing_loader.py
    src_dir = current_file.parent.parent  # src/
    project_root = src_dir.parent  # project root

    pricing_file = project_root / "llm_pricing_current.json"

    if not pricing_file.exists():
        logger.warning(f"Pricing file not found at {pricing_file}")
        return None

    return pricing_file


def _convert_json_pricing_to_model_pricing(json_data: dict) -> Dict[str, Dict[str, float]]:
    """
    Convert llm_pricing_current.json format to MODEL_PRICING format

    JSON format (per token):
        {
          "openai": {
            "gpt-4o": {
              "input_cost_per_token": 2.5e-06,
              "output_cost_per_token": 1e-05,
              ...
            }
          }
        }

    MODEL_PRICING format (per 1M tokens):
        {
          "gpt-4o": {"input": 2.50, "output": 10.00}
        }
    """
    model_pricing = {}

    # Process each provider
    for provider_name, models in json_data.items():
        # Skip metadata and pricing_notes
        if provider_name in ["metadata", "pricing_notes"]:
            continue

        # Process each model in the provider
        for model_name, model_data in models.items():
            if not isinstance(model_data, dict):
                continue

            # Get input and output costs per token
            input_cost = model_data.get("input_cost_per_token", 0)
            output_cost = model_data.get("output_cost_per_token", 0)

            # Convert from per-token to per-1M-tokens
            # $2.5e-06 per token = $2.50 per 1M tokens
            input_per_million = input_cost * 1_000_000
            output_per_million = output_cost * 1_000_000

            model_pricing[model_name] = {
                "input": round(input_per_million, 2),
                "output": round(output_per_million, 2)
            }

    # Add default pricing
    model_pricing["default"] = {"input": 1.00, "output": 2.00}

    return model_pricing


def load_pricing_from_json() -> Dict[str, Dict[str, float]]:
    """
    Load pricing data from llm_pricing_current.json

    Returns:
        Dictionary in MODEL_PRICING format with pricing per 1M tokens

    Example:
        >>> pricing = load_pricing_from_json()
        >>> pricing["gpt-4o"]
        {'input': 2.50, 'output': 10.00}
    """
    global _PRICING_CACHE

    # Return cached data if available
    if _PRICING_CACHE is not None:
        return _PRICING_CACHE

    # Get pricing file path
    pricing_file = _get_pricing_file_path()

    if pricing_file is None:
        logger.error("Could not find llm_pricing_current.json, using fallback pricing")
        return _get_fallback_pricing()

    try:
        # Load JSON file
        with open(pricing_file, 'r') as f:
            json_data = json.load(f)

        # Convert to MODEL_PRICING format
        pricing = _convert_json_pricing_to_model_pricing(json_data)

        # Cache the result
        _PRICING_CACHE = pricing

        logger.info(f"Loaded pricing for {len(pricing)} models from {pricing_file.name}")
        return pricing

    except Exception as e:
        logger.error(f"Failed to load pricing from {pricing_file}: {e}")
        return _get_fallback_pricing()


def _get_fallback_pricing() -> Dict[str, Dict[str, float]]:
    """
    Fallback pricing if JSON file cannot be loaded

    Uses conservative estimates for major models
    """
    return {
        # OpenAI
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},

        # Anthropic
        "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
        "claude-opus-4-1": {"input": 15.00, "output": 75.00},
        "claude-haiku-3-5": {"input": 0.80, "output": 4.00},

        # Google
        "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},

        # Fireworks
        "llama-v3p3-70b-instruct": {"input": 0.90, "output": 0.90},
        "llama-v3p1-8b-instruct": {"input": 0.20, "output": 0.20},

        # Default
        "default": {"input": 1.00, "output": 2.00}
    }


def reload_pricing() -> Dict[str, Dict[str, float]]:
    """
    Force reload pricing data from JSON file

    Useful after updating llm_pricing_current.json manually

    Returns:
        Updated pricing dictionary
    """
    global _PRICING_CACHE
    _PRICING_CACHE = None
    return load_pricing_from_json()


def get_pricing_metadata() -> dict:
    """
    Get metadata from llm_pricing_current.json

    Returns:
        Metadata dict with last_updated, sources, etc.
    """
    pricing_file = _get_pricing_file_path()

    if pricing_file is None:
        return {"error": "Pricing file not found"}

    try:
        with open(pricing_file, 'r') as f:
            json_data = json.load(f)

        return json_data.get("metadata", {})
    except Exception as e:
        logger.error(f"Failed to load metadata: {e}")
        return {"error": str(e)}

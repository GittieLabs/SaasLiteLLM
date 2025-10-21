"""
API Constants and Default Values

This module contains all hardcoded values and magic numbers used throughout the API.
Centralizing these values makes them easier to maintain, test, and configure.
"""

# Credit System Defaults
DEFAULT_TOKENS_PER_CREDIT = 10000
"""Default number of tokens equivalent to 1 credit in consumption_tokens mode"""

DEFAULT_CREDITS_PER_DOLLAR = 10.0
"""Default credits per dollar in consumption_usd mode (1 credit = $0.10)"""

# Minimum credit deduction
MINIMUM_CREDITS_PER_JOB = 1
"""Minimum credits to deduct for any successful job completion"""

# Timeout values (in seconds)
DEFAULT_REQUEST_TIMEOUT = 30
"""Default timeout for HTTP requests"""

LLM_CALL_TIMEOUT = 120
"""Timeout for LLM API calls (streaming and non-streaming)"""

# Token pricing fallback
DEFAULT_COST_PER_MILLION_INPUT_TOKENS = 0.0
"""Default cost per 1M input tokens when pricing unavailable"""

DEFAULT_COST_PER_MILLION_OUTPUT_TOKENS = 0.0
"""Default cost per 1M output tokens when pricing unavailable"""

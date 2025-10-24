"""
Direct Provider Service - Call LLM providers directly without LiteLLM proxy

This service implements direct API calls to:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude models)
- Google Gemini (Gemini Pro, Flash, etc.)
- Fireworks (Llama, Mixtral, etc.)

It provides a unified interface that replaces call_litellm() for direct provider access.
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
from enum import Enum
import logging

# Import official provider SDKs
import openai
from anthropic import AsyncAnthropic
import google.generativeai as genai

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    FIREWORKS = "fireworks"


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class RateLimitError(ProviderError):
    """Provider rate limit exceeded"""
    pass


class AuthenticationError(ProviderError):
    """Provider authentication failed"""
    pass


class DirectProviderService:
    """
    Service for making direct calls to LLM providers.

    Replaces call_litellm() with direct API calls, providing:
    - Lower latency (no proxy hop)
    - Better error handling
    - Provider-specific optimizations
    - Usage tracking (tokens, costs)
    """

    def __init__(self):
        """Initialize provider service"""
        self.max_retries = 3
        self.base_retry_delay = 1.0  # seconds

    async def chat_completion(
        self,
        provider: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a non-streaming chat completion call to any provider.

        Returns response dict with:
        - id: Request ID
        - model: Model used
        - choices: [{"message": {"content": "...", "role": "assistant"}, "finish_reason": "stop"}]
        - usage: {"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z}
        """
        provider_enum = Provider(provider.lower())

        if provider_enum == Provider.OPENAI:
            return await self._openai_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop
            )
        elif provider_enum == Provider.ANTHROPIC:
            return await self._anthropic_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice=tool_choice,
                top_p=top_p,
                stop=stop
            )
        elif provider_enum == Provider.GEMINI:
            return await self._gemini_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                top_p=top_p,
                stop=stop
            )
        elif provider_enum == Provider.FIREWORKS:
            return await self._fireworks_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop
            )
        else:
            raise ProviderError(f"Unsupported provider: {provider}")

    async def chat_completion_stream(
        self,
        provider: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> httpx.Response:
        """
        Make a streaming chat completion call to any provider.

        Returns httpx.Response object for streaming (similar to call_litellm streaming).
        Caller is responsible for iterating over response.aiter_lines().
        """
        provider_enum = Provider(provider.lower())

        if provider_enum == Provider.OPENAI:
            return await self._openai_chat_completion_stream(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop
            )
        elif provider_enum == Provider.ANTHROPIC:
            return await self._anthropic_chat_completion_stream(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice=tool_choice,
                top_p=top_p,
                stop=stop
            )
        elif provider_enum == Provider.GEMINI:
            return await self._gemini_chat_completion_stream(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                top_p=top_p,
                stop=stop
            )
        elif provider_enum == Provider.FIREWORKS:
            return await self._fireworks_chat_completion_stream(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop
            )
        else:
            raise ProviderError(f"Unsupported provider: {provider}")

    # ========== OpenAI Implementation ==========

    async def _openai_chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """OpenAI chat completion using official SDK"""
        client = openai.AsyncOpenAI(api_key=api_key)

        # Build request params
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            params["max_tokens"] = max_tokens
        if response_format:
            params["response_format"] = response_format
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if stop:
            params["stop"] = stop

        # Make request with retry logic
        for attempt in range(self.max_retries):
            try:
                response = await client.chat.completions.create(**params)

                # Convert to dict format matching LiteLLM response
                return {
                    "id": response.id,
                    "model": response.model,
                    "choices": [
                        {
                            "message": {
                                "role": choice.message.role,
                                "content": choice.message.content,
                                "tool_calls": [
                                    {
                                        "id": tc.id,
                                        "type": tc.type,
                                        "function": {
                                            "name": tc.function.name,
                                            "arguments": tc.function.arguments
                                        }
                                    }
                                    for tc in (choice.message.tool_calls or [])
                                ] if choice.message.tool_calls else None
                            },
                            "finish_reason": choice.finish_reason,
                            "index": choice.index
                        }
                        for choice in response.choices
                    ],
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "created": response.created,
                    "object": response.object
                }

            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"OpenAI rate limit hit, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise RateLimitError(f"OpenAI rate limit: {str(e)}")

            except openai.AuthenticationError as e:
                raise AuthenticationError(f"OpenAI authentication failed: {str(e)}")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"OpenAI error: {str(e)}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise ProviderError(f"OpenAI error: {str(e)}")

    async def _openai_chat_completion_stream(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> httpx.Response:
        """OpenAI streaming chat completion (returns httpx.Response for SSE)"""
        # Use raw HTTP client for streaming to match LiteLLM behavior
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=120.0
            )
            response.raise_for_status()
            return response

    # ========== Anthropic Implementation ==========

    async def _anthropic_chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Anthropic chat completion using official SDK"""
        client = AsyncAnthropic(api_key=api_key)

        # Convert OpenAI-style messages to Anthropic format
        # Anthropic expects system message separately
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Build request params
        params = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 4096,  # Anthropic requires max_tokens
            "temperature": temperature,
        }

        if system_message:
            params["system"] = system_message
        if tools:
            # Convert OpenAI tools to Anthropic format if needed
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        if top_p is not None:
            params["top_p"] = top_p
        if stop:
            params["stop_sequences"] = stop

        # Make request with retry logic
        for attempt in range(self.max_retries):
            try:
                response = await client.messages.create(**params)

                # Convert to OpenAI-compatible format
                content = ""
                if response.content:
                    for block in response.content:
                        if hasattr(block, 'text'):
                            content += block.text

                # Estimate token usage (Anthropic doesn't always provide exact counts)
                prompt_tokens = response.usage.input_tokens if hasattr(response.usage, 'input_tokens') else 0
                completion_tokens = response.usage.output_tokens if hasattr(response.usage, 'output_tokens') else 0

                return {
                    "id": response.id,
                    "model": response.model,
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": content
                            },
                            "finish_reason": response.stop_reason,
                            "index": 0
                        }
                    ],
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                }

            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Anthropic rate limit hit, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                elif "authentication" in str(e).lower():
                    raise AuthenticationError(f"Anthropic authentication failed: {str(e)}")
                elif attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Anthropic error: {str(e)}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise ProviderError(f"Anthropic error: {str(e)}")

    async def _anthropic_chat_completion_stream(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> httpx.Response:
        """Anthropic streaming chat completion"""
        # Convert messages
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "stream": True
        }

        if system_message:
            payload["system"] = system_message
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if top_p is not None:
            payload["top_p"] = top_p
        if stop:
            payload["stop_sequences"] = stop

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
                timeout=120.0
            )
            response.raise_for_status()
            return response

    # ========== Google Gemini Implementation ==========

    async def _gemini_chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Google Gemini chat completion"""
        # Use REST API for Gemini (google-generativeai SDK is sync-only)
        headers = {
            "Content-Type": "application/json"
        }

        # Convert OpenAI-style messages to Gemini format
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            elif msg["role"] == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })

        payload = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        if top_p is not None:
            payload["generationConfig"]["topP"] = top_p
        if stop:
            payload["generationConfig"]["stopSequences"] = stop
        if tools:
            # Convert tools to Gemini format if needed
            payload["tools"] = tools

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, headers=headers, timeout=120.0)
                    response.raise_for_status()
                    data = response.json()

                # Extract content
                content = ""
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                content += part["text"]

                # Extract token usage
                prompt_tokens = 0
                completion_tokens = 0
                if "usageMetadata" in data:
                    prompt_tokens = data["usageMetadata"].get("promptTokenCount", 0)
                    completion_tokens = data["usageMetadata"].get("candidatesTokenCount", 0)

                # Get finish reason
                finish_reason = "stop"
                if "candidates" in data and len(data["candidates"]) > 0:
                    finish_reason = data["candidates"][0].get("finishReason", "stop").lower()

                return {
                    "id": f"gemini-{data.get('modelVersion', 'unknown')}",
                    "model": model,
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": content
                            },
                            "finish_reason": finish_reason,
                            "index": 0
                        }
                    ],
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Gemini rate limit hit, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                elif e.response.status_code == 401:
                    raise AuthenticationError(f"Gemini authentication failed: {str(e)}")
                elif attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Gemini error: {str(e)}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise ProviderError(f"Gemini error: {str(e)}")

    async def _gemini_chat_completion_stream(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> httpx.Response:
        """Google Gemini streaming chat completion"""
        headers = {
            "Content-Type": "application/json"
        }

        # Convert messages
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            elif msg["role"] == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })

        payload = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        if top_p is not None:
            payload["generationConfig"]["topP"] = top_p
        if stop:
            payload["generationConfig"]["stopSequences"] = stop
        if tools:
            payload["tools"] = tools

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}&alt=sse"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            return response

    # ========== Fireworks Implementation ==========

    async def _fireworks_chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Fireworks chat completion (OpenAI-compatible API)"""
        # Fireworks uses OpenAI-compatible API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop:
            payload["stop"] = stop

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.fireworks.ai/inference/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=120.0
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Fireworks rate limit hit, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                elif e.response.status_code == 401:
                    raise AuthenticationError(f"Fireworks authentication failed: {str(e)}")
                elif attempt < self.max_retries - 1:
                    delay = self.base_retry_delay * (2 ** attempt)
                    logger.warning(f"Fireworks error: {str(e)}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise ProviderError(f"Fireworks error: {str(e)}")

    async def _fireworks_chat_completion_stream(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> httpx.Response:
        """Fireworks streaming chat completion (OpenAI-compatible)"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.fireworks.ai/inference/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=120.0
            )
            response.raise_for_status()
            return response


    # ========== Helper Methods ==========

    async def get_provider_credential(
        self,
        db,
        organization_id: str,
        provider: str
    ) -> Optional[Tuple[str, str]]:
        """
        Retrieve provider credentials from database.

        Args:
            db: Database session
            organization_id: Organization ID
            provider: Provider name (openai, anthropic, etc.)

        Returns:
            Tuple of (api_key, provider_name) or None if not found

        Example:
            api_key, provider = await service.get_provider_credential(
                db, "org_123", "openai"
            )
        """
        from ..models.provider_credentials import ProviderCredential

        # Query active credential for this org+provider
        credential = db.query(ProviderCredential).filter(
            ProviderCredential.organization_id == organization_id,
            ProviderCredential.provider == provider,
            ProviderCredential.is_active == True
        ).first()

        if not credential:
            return None

        # Decrypt and return API key
        api_key = credential.get_api_key()
        return (api_key, credential.provider)

    def detect_provider_from_model(self, model: str) -> str:
        """
        Detect provider from model string.

        Examples:
            - "gpt-4" -> "openai"
            - "gpt-3.5-turbo" -> "openai"
            - "claude-3-opus" -> "anthropic"
            - "claude-3-sonnet" -> "anthropic"
            - "gemini-pro" -> "gemini"
            - "gemini-1.5-flash" -> "gemini"
            - "accounts/fireworks/models/llama-v3" -> "fireworks"
        """
        model_lower = model.lower()

        # OpenAI models
        if any(prefix in model_lower for prefix in ["gpt-", "text-davinci", "text-curie", "text-babbage", "text-ada", "o1-", "o3-"]):
            return Provider.OPENAI.value

        # Anthropic models
        if "claude" in model_lower:
            return Provider.ANTHROPIC.value

        # Gemini models
        if "gemini" in model_lower:
            return Provider.GEMINI.value

        # Fireworks models
        if any(prefix in model_lower for prefix in ["llama", "mixtral", "fireworks", "accounts/fireworks"]):
            return Provider.FIREWORKS.value

        # Default to OpenAI for unknown models
        logger.warning(f"Unknown model provider for '{model}', defaulting to OpenAI")
        return Provider.OPENAI.value


def get_direct_provider_service() -> DirectProviderService:
    """Dependency injection for direct provider service"""
    return DirectProviderService()

"""
OpenRouter provider for accessing multiple models via a unified API.

This provider uses OpenRouter's API which provides access to many
different models through an OpenAI-compatible interface.
"""

import os
import json
from typing import List, Optional, Dict, Any, AsyncIterator
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ..base import (
    LLMProvider,
    Message,
    CompletionResult,
    ToolDefinition,
    ToolCall,
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMInvalidRequestError,
)


class OpenRouterProvider(LLMProvider):
    """
    Provider for OpenRouter API (multi-model access).

    Provides access to many different models through OpenRouter's
    OpenAI-compatible API.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenRouter provider.

        Args:
            config: Configuration with api_key, model, base_url, timeout

        Raises:
            ValueError: If API key not found
        """
        super().__init__(config)

        # Get API key from environment variable
        api_key_env = config.get("api_key_env", "OPENROUTER_API_KEY")
        self.api_key = os.getenv(api_key_env)

        if not self.api_key:
            raise ValueError(
                f"OpenRouter API key not found in environment variable {api_key_env}"
            )

        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.model = config.get("model", "openai/gpt-4o")
        self.site_url = config.get("site_url", "")
        self.site_name = config.get("site_name", "Voice Assistant")

        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
            }
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((LLMConnectionError, LLMTimeoutError))
    )
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResult:
        """
        Generate completion using OpenRouter API.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            CompletionResult with response

        Raises:
            LLMConnectionError: Failed to connect to OpenRouter
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMError: Other errors
        """
        try:
            # Build request payload
            payload = self._build_payload(
                messages=messages,
                tools=tools,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=False,
                **kwargs
            )

            # Make request
            response = await self.client.post(
                "/chat/completions",
                json=payload
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            return self._parse_completion_response(data)

        except httpx.ConnectError as e:
            raise LLMConnectionError(f"Failed to connect to OpenRouter API: {e}")
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"OpenRouter API request timed out: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"OpenRouter rate limit exceeded: {e.response.text}")
            elif e.response.status_code == 400:
                raise LLMInvalidRequestError(f"Invalid request to OpenRouter: {e.response.text}")
            raise LLMError(f"HTTP error from OpenRouter: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise LLMError(f"Unexpected error during OpenRouter completion: {e}")

    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens from OpenRouter API.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            String tokens as they're generated

        Raises:
            LLMConnectionError: Failed to connect to OpenRouter
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMError: Other errors
        """
        try:
            # Build request payload
            payload = self._build_payload(
                messages=messages,
                tools=tools,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
                **kwargs
            )

            # Stream request
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or line.startswith(": "):
                        continue

                    if line.startswith("data: "):
                        line = line[6:]  # Remove "data: " prefix

                    if line == "[DONE]":
                        break

                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")

                        if content:
                            yield content

                    except json.JSONDecodeError:
                        continue

        except httpx.ConnectError as e:
            raise LLMConnectionError(f"Failed to connect to OpenRouter API: {e}")
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"OpenRouter stream timed out: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"OpenRouter rate limit exceeded")
            raise LLMError(f"HTTP error from OpenRouter: {e.response.status_code}")
        except Exception as e:
            raise LLMError(f"Unexpected error during OpenRouter streaming: {e}")

    def _build_payload(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request payload for OpenRouter API."""
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        # Add tools if provided
        if tools:
            payload["tools"] = [t.to_dict() for t in tools]
            payload["tool_choice"] = "auto"

        # Add any additional parameters
        payload.update(kwargs)

        return payload

    def _parse_completion_response(self, data: Dict[str, Any]) -> CompletionResult:
        """Parse completion response from OpenRouter API."""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        content = message.get("content", "")
        finish_reason = choice.get("finish_reason", "stop")

        # Parse tool calls if present
        tool_calls = None
        if "tool_calls" in message:
            tool_calls = []
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=json.loads(func.get("arguments", "{}"))
                ))

        # Get token usage
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)

        return CompletionResult(
            content=content,
            model=data.get("model", self.model),
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            metadata={
                "usage": usage,
                "provider": "openrouter",
                "generation_id": data.get("id")
            }
        )

    async def close(self):
        """Close HTTP client and clean up resources."""
        await self.client.aclose()

    def __repr__(self) -> str:
        return f"OpenRouterProvider(model={self.model})"

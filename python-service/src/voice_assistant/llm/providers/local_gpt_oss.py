"""
Local GPT-OSS provider using MLX for on-device inference.

This provider connects to a locally running gpt-oss:120b instance
via MLX, providing full privacy and no API costs.
"""

import json
import asyncio
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
)


class LocalGPTOSSProvider(LLMProvider):
    """
    Provider for local gpt-oss:120b via MLX.

    Connects to localhost MLX server for fully local inference.
    Supports streaming and tool calling.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize local GPT-OSS provider.

        Args:
            config: Configuration with base_url, model, timeout
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8080")
        self.model = config.get("model", "gpt-oss:120b")

        # Create HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(LLMConnectionError)
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
        Generate completion using local MLX model.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            CompletionResult with response

        Raises:
            LLMConnectionError: Failed to connect to local server
            LLMTimeoutError: Request timed out
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
                "/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            return self._parse_completion_response(data)

        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Failed to connect to local MLX server at {self.base_url}: {e}"
            )
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(
                f"Request to local MLX server timed out after {self.timeout}s: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise LLMError(
                f"HTTP error from local MLX server: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise LLMError(f"Unexpected error during completion: {e}")

    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens from local MLX model.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            String tokens as they're generated

        Raises:
            LLMConnectionError: Failed to connect to local server
            LLMTimeoutError: Request timed out
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
                "/v1/chat/completions",
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
            raise LLMConnectionError(
                f"Failed to connect to local MLX server at {self.base_url}: {e}"
            )
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(
                f"Stream request to local MLX server timed out: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise LLMError(
                f"HTTP error from local MLX server: {e.response.status_code}"
            )
        except Exception as e:
            raise LLMError(f"Unexpected error during streaming: {e}")

    def _build_payload(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request payload for MLX API."""
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
        """Parse completion response from MLX API."""
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
                "provider": "local_gpt_oss"
            }
        )

    async def close(self):
        """Close HTTP client and clean up resources."""
        await self.client.aclose()

    def __repr__(self) -> str:
        return f"LocalGPTOSSProvider(model={self.model}, base_url={self.base_url})"

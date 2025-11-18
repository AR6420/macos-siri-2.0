"""
OpenAI provider for GPT-4, GPT-4o, and other OpenAI models.

This provider uses the official OpenAI API for cloud-based inference.
"""

import os
import json
from typing import List, Optional, Dict, Any, AsyncIterator
from openai import AsyncOpenAI
from openai import APIError, APIConnectionError, APITimeoutError, RateLimitError
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


class OpenAIProvider(LLMProvider):
    """
    Provider for OpenAI API (GPT-4, GPT-4o, etc.).

    Supports full OpenAI capabilities including tool calling and streaming.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI provider.

        Args:
            config: Configuration with api_key, model, timeout

        Raises:
            ValueError: If API key not found
        """
        super().__init__(config)

        # Get API key from environment variable
        api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(
                f"OpenAI API key not found in environment variable {api_key_env}"
            )

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.get("base_url"),
            timeout=self.timeout
        )

        self.model = config.get("model", "gpt-4o")

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
        Generate completion using OpenAI API.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Returns:
            CompletionResult with response

        Raises:
            LLMConnectionError: Failed to connect to OpenAI
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMError: Other errors
        """
        try:
            # Build request parameters
            params = self._build_params(
                messages=messages,
                tools=tools,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=False,
                **kwargs
            )

            # Make request
            response = await self.client.chat.completions.create(**params)

            # Parse response
            return self._parse_completion_response(response)

        except APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to OpenAI API: {e}")
        except APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI API request timed out: {e}")
        except RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI API rate limit exceeded: {e}")
        except APIError as e:
            if e.status_code == 400:
                raise LLMInvalidRequestError(f"Invalid request to OpenAI API: {e}")
            raise LLMError(f"OpenAI API error: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error during OpenAI completion: {e}")

    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens from OpenAI API.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Yields:
            String tokens as they're generated

        Raises:
            LLMConnectionError: Failed to connect to OpenAI
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMError: Other errors
        """
        try:
            # Build request parameters
            params = self._build_params(
                messages=messages,
                tools=tools,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
                **kwargs
            )

            # Stream request
            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to OpenAI API: {e}")
        except APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI API stream timed out: {e}")
        except RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI API rate limit exceeded: {e}")
        except APIError as e:
            raise LLMError(f"OpenAI API error during streaming: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error during OpenAI streaming: {e}")

    def _build_params(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request parameters for OpenAI API."""
        params = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        # Add tools if provided
        if tools:
            params["tools"] = [t.to_dict() for t in tools]
            params["tool_choice"] = "auto"

        # Add any additional parameters
        params.update(kwargs)

        return params

    def _parse_completion_response(self, response: Any) -> CompletionResult:
        """Parse completion response from OpenAI API."""
        choice = response.choices[0]
        message = choice.message

        content = message.content or ""
        finish_reason = choice.finish_reason

        # Parse tool calls if present
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))

        # Get token usage
        usage = response.usage
        tokens_used = usage.total_tokens if usage else 0

        return CompletionResult(
            content=content,
            model=response.model,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            metadata={
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": tokens_used
                },
                "provider": "openai"
            }
        )

    async def close(self):
        """Close OpenAI client and clean up resources."""
        await self.client.close()

    def __repr__(self) -> str:
        return f"OpenAIProvider(model={self.model})"

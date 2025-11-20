"""
Anthropic provider for Claude Sonnet, Opus, and other Claude models.

This provider uses the official Anthropic API for cloud-based inference.
"""

from __future__ import annotations

import os
import json
from typing import List, Optional, Dict, Any, AsyncIterator
from anthropic import AsyncAnthropic, APIError, APIConnectionError, APITimeoutError, RateLimitError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ..base import (
    LLMProvider,
    Message,
    MessageRole,
    CompletionResult,
    ToolDefinition,
    ToolCall,
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMInvalidRequestError,
)


class AnthropicProvider(LLMProvider):
    """
    Provider for Anthropic API (Claude Sonnet, Opus, etc.).

    Supports full Claude capabilities including tool calling and streaming.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anthropic provider.

        Args:
            config: Configuration with api_key, model, timeout

        Raises:
            ValueError: If API key not found
        """
        super().__init__(config)

        # Get API key from environment variable
        api_key_env = config.get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(
                f"Anthropic API key not found in environment variable {api_key_env}"
            )

        # Initialize Anthropic client
        self.client = AsyncAnthropic(
            api_key=api_key,
            timeout=self.timeout
        )

        self.model = config.get("model", "claude-sonnet-4-20250514")

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
        Generate completion using Anthropic API.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic parameters

        Returns:
            CompletionResult with response

        Raises:
            LLMConnectionError: Failed to connect to Anthropic
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMError: Other errors
        """
        try:
            # Separate system message from conversation
            system_message, conversation_messages = self._prepare_messages(messages)

            # Build request parameters
            params = {
                "model": self.model,
                "messages": conversation_messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
            }

            if system_message:
                params["system"] = system_message

            # Add tools if provided
            if tools:
                params["tools"] = self._convert_tools(tools)

            # Add any additional parameters
            params.update(kwargs)

            # Make request
            response = await self.client.messages.create(**params)

            # Parse response
            return self._parse_completion_response(response)

        except APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to Anthropic API: {e}")
        except APITimeoutError as e:
            raise LLMTimeoutError(f"Anthropic API request timed out: {e}")
        except RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic API rate limit exceeded: {e}")
        except APIError as e:
            if e.status_code == 400:
                raise LLMInvalidRequestError(f"Invalid request to Anthropic API: {e}")
            raise LLMError(f"Anthropic API error: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error during Anthropic completion: {e}")

    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens from Anthropic API.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic parameters

        Yields:
            String tokens as they're generated

        Raises:
            LLMConnectionError: Failed to connect to Anthropic
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMError: Other errors
        """
        try:
            # Separate system message from conversation
            system_message, conversation_messages = self._prepare_messages(messages)

            # Build request parameters
            params = {
                "model": self.model,
                "messages": conversation_messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "stream": True,
            }

            if system_message:
                params["system"] = system_message

            # Add tools if provided
            if tools:
                params["tools"] = self._convert_tools(tools)

            # Add any additional parameters
            params.update(kwargs)

            # Stream request
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text

        except APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to Anthropic API: {e}")
        except APITimeoutError as e:
            raise LLMTimeoutError(f"Anthropic API stream timed out: {e}")
        except RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic API rate limit exceeded: {e}")
        except APIError as e:
            raise LLMError(f"Anthropic API error during streaming: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error during Anthropic streaming: {e}")

    def _prepare_messages(self, messages: List[Message]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Prepare messages for Anthropic API.

        Anthropic requires system message separate from conversation.

        Returns:
            Tuple of (system_message, conversation_messages)
        """
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Combine multiple system messages
                if system_message:
                    system_message += "\n\n" + msg.content
                else:
                    system_message = msg.content
            else:
                conversation_messages.append(msg.to_dict())

        return system_message, conversation_messages

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """
        Convert tool definitions to Anthropic format.

        Anthropic uses slightly different tool format than OpenAI.
        """
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            })
        return anthropic_tools

    def _parse_completion_response(self, response: Any) -> CompletionResult:
        """Parse completion response from Anthropic API."""
        # Extract text content
        content = ""
        tool_calls = None

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))

        # Get token usage
        usage = response.usage
        tokens_used = usage.input_tokens + usage.output_tokens

        return CompletionResult(
            content=content,
            model=response.model,
            tokens_used=tokens_used,
            finish_reason=response.stop_reason,
            tool_calls=tool_calls,
            metadata={
                "usage": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": tokens_used
                },
                "provider": "anthropic"
            }
        )

    async def close(self):
        """Close Anthropic client and clean up resources."""
        await self.client.close()

    def __repr__(self) -> str:
        return f"AnthropicProvider(model={self.model})"

"""
Tests for LLM providers with mocked HTTP responses.
"""

import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from voice_assistant.llm import (
    Message,
    MessageRole,
    ToolDefinition,
    LocalGPTOSSProvider,
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
)


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        Message(role=MessageRole.SYSTEM, content="You are helpful."),
        Message(role=MessageRole.USER, content="What is 2+2?"),
    ]


@pytest.fixture
def sample_tool():
    """Sample tool definition for testing."""
    return ToolDefinition(
        name="calculator",
        description="Perform calculations",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            }
        }
    )


class TestLocalGPTOSSProvider:
    """Test LocalGPTOSSProvider."""

    @pytest.fixture
    def provider(self):
        """Create LocalGPTOSSProvider instance."""
        config = {
            "base_url": "http://localhost:8080",
            "model": "gpt-oss:120b",
            "timeout": 60,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        return LocalGPTOSSProvider(config)

    @pytest.mark.asyncio
    async def test_complete_success(self, provider, sample_messages):
        """Test successful completion."""
        mock_response = {
            "model": "gpt-oss:120b",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "The answer is 4."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "total_tokens": 30
            }
        }

        with patch.object(provider.client, 'post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            mock_post.return_value.raise_for_status = MagicMock()

            result = await provider.complete(sample_messages)

            assert result.content == "The answer is 4."
            assert result.model == "gpt-oss:120b"
            assert result.tokens_used == 30
            assert result.finish_reason == "stop"
            assert not result.has_tool_calls

    @pytest.mark.asyncio
    async def test_complete_with_tools(self, provider, sample_messages, sample_tool):
        """Test completion with tool calls."""
        mock_response = {
            "model": "gpt-oss:120b",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": '{"expression": "2+2"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": {"total_tokens": 25}
        }

        with patch.object(provider.client, 'post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            mock_post.return_value.raise_for_status = MagicMock()

            result = await provider.complete(sample_messages, tools=[sample_tool])

            assert result.has_tool_calls
            assert len(result.tool_calls) == 1
            assert result.tool_calls[0].name == "calculator"
            assert result.tool_calls[0].arguments == {"expression": "2+2"}

    @pytest.mark.asyncio
    async def test_complete_connection_error(self, provider, sample_messages):
        """Test connection error handling."""
        with patch.object(provider.client, 'post', side_effect=httpx.ConnectError("Connection failed")):
            with pytest.raises(LLMConnectionError, match="Failed to connect"):
                await provider.complete(sample_messages)

    @pytest.mark.asyncio
    async def test_complete_timeout(self, provider, sample_messages):
        """Test timeout error handling."""
        with patch.object(provider.client, 'post', side_effect=httpx.TimeoutException("Timeout")):
            with pytest.raises(LLMTimeoutError, match="timed out"):
                await provider.complete(sample_messages)

    @pytest.mark.asyncio
    async def test_stream_complete(self, provider, sample_messages):
        """Test streaming completion."""
        mock_lines = [
            'data: {"choices":[{"delta":{"content":"The"}}]}',
            'data: {"choices":[{"delta":{"content":" answer"}}]}',
            'data: {"choices":[{"delta":{"content":" is 4."}}]}',
            'data: [DONE]'
        ]

        async def mock_aiter_lines():
            for line in mock_lines:
                yield line

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock()
        mock_stream.aiter_lines = mock_aiter_lines
        mock_stream.raise_for_status = MagicMock()

        with patch.object(provider.client, 'stream', return_value=mock_stream):
            chunks = []
            async for chunk in provider.stream_complete(sample_messages):
                chunks.append(chunk)

            assert chunks == ["The", " answer", " is 4."]

    @pytest.mark.asyncio
    async def test_close(self, provider):
        """Test closing provider."""
        with patch.object(provider.client, 'aclose') as mock_close:
            await provider.close()
            mock_close.assert_called_once()


class TestOpenAIProvider:
    """Test OpenAIProvider."""

    @pytest.fixture
    def provider(self):
        """Create OpenAIProvider instance."""
        os.environ["OPENAI_TEST_KEY"] = "test-key-123"
        config = {
            "model": "gpt-4o",
            "api_key_env": "OPENAI_TEST_KEY",
            "timeout": 60
        }
        provider = OpenAIProvider(config)
        yield provider
        del os.environ["OPENAI_TEST_KEY"]

    @pytest.mark.asyncio
    async def test_complete_success(self, provider, sample_messages):
        """Test successful completion."""
        mock_response = MagicMock()
        mock_response.model = "gpt-4o"
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="The answer is 4.",
                tool_calls=None
            ),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30
        )

        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            result = await provider.complete(sample_messages)

            assert result.content == "The answer is 4."
            assert result.model == "gpt-4o"
            assert result.tokens_used == 30

    @pytest.mark.asyncio
    async def test_stream_complete(self, provider, sample_messages):
        """Test streaming completion."""
        async def mock_stream():
            chunks = ["The", " answer", " is 4."]
            for chunk_text in chunks:
                chunk = MagicMock()
                chunk.choices = [MagicMock(delta=MagicMock(content=chunk_text))]
                yield chunk

        with patch.object(provider.client.chat.completions, 'create', return_value=mock_stream()):
            chunks = []
            async for chunk in provider.stream_complete(sample_messages):
                chunks.append(chunk)

            assert chunks == ["The", " answer", " is 4."]


class TestAnthropicProvider:
    """Test AnthropicProvider."""

    @pytest.fixture
    def provider(self):
        """Create AnthropicProvider instance."""
        os.environ["ANTHROPIC_TEST_KEY"] = "test-key-123"
        config = {
            "model": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_TEST_KEY",
            "timeout": 60
        }
        provider = AnthropicProvider(config)
        yield provider
        del os.environ["ANTHROPIC_TEST_KEY"]

    @pytest.mark.asyncio
    async def test_complete_success(self, provider, sample_messages):
        """Test successful completion."""
        mock_response = MagicMock()
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.content = [
            MagicMock(type="text", text="The answer is 4.")
        ]
        mock_response.usage = MagicMock(
            input_tokens=20,
            output_tokens=10
        )
        mock_response.stop_reason = "end_turn"

        with patch.object(provider.client.messages, 'create', return_value=mock_response):
            result = await provider.complete(sample_messages)

            assert result.content == "The answer is 4."
            assert result.model == "claude-sonnet-4-20250514"
            assert result.tokens_used == 30

    @pytest.mark.asyncio
    async def test_complete_with_tool_use(self, provider, sample_messages, sample_tool):
        """Test completion with tool use."""
        mock_response = MagicMock()
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.content = [
            MagicMock(
                type="tool_use",
                id="call_123",
                name="calculator",
                input={"expression": "2+2"}
            )
        ]
        mock_response.usage = MagicMock(input_tokens=20, output_tokens=10)
        mock_response.stop_reason = "tool_use"

        with patch.object(provider.client.messages, 'create', return_value=mock_response):
            result = await provider.complete(sample_messages, tools=[sample_tool])

            assert result.has_tool_calls
            assert len(result.tool_calls) == 1
            assert result.tool_calls[0].name == "calculator"

    @pytest.mark.asyncio
    async def test_prepare_messages(self, provider):
        """Test message preparation separates system messages."""
        messages = [
            Message(role=MessageRole.SYSTEM, content="System 1"),
            Message(role=MessageRole.SYSTEM, content="System 2"),
            Message(role=MessageRole.USER, content="Hello"),
        ]

        system_msg, conv_msgs = provider._prepare_messages(messages)

        assert system_msg == "System 1\n\nSystem 2"
        assert len(conv_msgs) == 1
        assert conv_msgs[0]["role"] == "user"


class TestOpenRouterProvider:
    """Test OpenRouterProvider."""

    @pytest.fixture
    def provider(self):
        """Create OpenRouterProvider instance."""
        os.environ["OPENROUTER_TEST_KEY"] = "test-key-123"
        config = {
            "model": "openai/gpt-4o",
            "api_key_env": "OPENROUTER_TEST_KEY",
            "base_url": "https://openrouter.ai/api/v1",
            "timeout": 60
        }
        provider = OpenRouterProvider(config)
        yield provider
        del os.environ["OPENROUTER_TEST_KEY"]

    @pytest.mark.asyncio
    async def test_complete_success(self, provider, sample_messages):
        """Test successful completion."""
        mock_response = {
            "id": "gen_123",
            "model": "openai/gpt-4o",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "The answer is 4."
                },
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 30}
        }

        with patch.object(provider.client, 'post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            mock_post.return_value.raise_for_status = MagicMock()

            result = await provider.complete(sample_messages)

            assert result.content == "The answer is 4."
            assert result.metadata["provider"] == "openrouter"
            assert result.metadata["generation_id"] == "gen_123"

    @pytest.mark.asyncio
    async def test_close(self, provider):
        """Test closing provider."""
        with patch.object(provider.client, 'aclose') as mock_close:
            await provider.close()
            mock_close.assert_called_once()

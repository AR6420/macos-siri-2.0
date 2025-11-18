"""
Unit tests for TextRewriter.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from voice_assistant.inline_ai import TextRewriter, ToneType
from voice_assistant.llm.base import CompletionResult, Message


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    provider = Mock()
    provider.complete = AsyncMock()
    return provider


@pytest.fixture
def config():
    """Test configuration."""
    return {
        "default_tone": "professional",
        "max_tokens": 512,
        "temperature": 0.7
    }


@pytest.fixture
def rewriter(mock_llm_provider, config):
    """Create TextRewriter instance."""
    return TextRewriter(mock_llm_provider, config)


@pytest.mark.asyncio
async def test_rewrite_professional(rewriter, mock_llm_provider):
    """Test professional tone rewriting."""
    # Setup mock response
    mock_llm_provider.complete.return_value = CompletionResult(
        content="This is a professional version of the text.",
        model="test-model",
        tokens_used=20,
        finish_reason="stop"
    )

    # Perform rewrite
    result = await rewriter.rewrite(
        "this is casual text",
        ToneType.PROFESSIONAL
    )

    # Verify result
    assert result.success is True
    assert result.rewritten_text == "This is a professional version of the text."
    assert result.tone == ToneType.PROFESSIONAL
    assert result.tokens_used == 20
    assert result.processing_time_ms > 0

    # Verify LLM was called with correct prompt
    call_args = mock_llm_provider.complete.call_args
    messages = call_args.kwargs['messages']
    assert len(messages) == 1
    assert "professional" in messages[0].content.lower()


@pytest.mark.asyncio
async def test_rewrite_friendly(rewriter, mock_llm_provider):
    """Test friendly tone rewriting."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content="Hey there! This is a friendly version.",
        model="test-model",
        tokens_used=15,
        finish_reason="stop"
    )

    result = await rewriter.rewrite(
        "This is formal text",
        ToneType.FRIENDLY
    )

    assert result.success is True
    assert result.rewritten_text == "Hey there! This is a friendly version."
    assert result.tone == ToneType.FRIENDLY


@pytest.mark.asyncio
async def test_rewrite_concise(rewriter, mock_llm_provider):
    """Test concise rewriting."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content="Brief version.",
        model="test-model",
        tokens_used=5,
        finish_reason="stop"
    )

    result = await rewriter.rewrite(
        "This is a very long and wordy piece of text that could be much shorter",
        ToneType.CONCISE
    )

    assert result.success is True
    assert result.rewritten_text == "Brief version."
    assert result.tone == ToneType.CONCISE


@pytest.mark.asyncio
async def test_rewrite_removes_quotes(rewriter, mock_llm_provider):
    """Test that rewriter removes quotes from LLM response."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content='"This has quotes around it"',
        model="test-model",
        tokens_used=10,
        finish_reason="stop"
    )

    result = await rewriter.rewrite("test", ToneType.PROFESSIONAL)

    assert result.success is True
    assert result.rewritten_text == "This has quotes around it"


@pytest.mark.asyncio
async def test_rewrite_timeout(rewriter, mock_llm_provider):
    """Test rewrite timeout handling."""
    import asyncio

    # Mock LLM to take too long
    async def slow_complete(*args, **kwargs):
        await asyncio.sleep(20)
        return CompletionResult(
            content="Too slow",
            model="test-model",
            tokens_used=10,
            finish_reason="stop"
        )

    mock_llm_provider.complete = slow_complete

    # Test with short timeout
    result = await rewriter.rewrite(
        "test text",
        ToneType.PROFESSIONAL,
        timeout_seconds=0.1
    )

    assert result.success is False
    assert "timeout" in result.error.lower()


@pytest.mark.asyncio
async def test_rewrite_error_handling(rewriter, mock_llm_provider):
    """Test error handling during rewrite."""
    mock_llm_provider.complete.side_effect = Exception("API Error")

    result = await rewriter.rewrite("test text", ToneType.PROFESSIONAL)

    assert result.success is False
    assert "API Error" in result.error


@pytest.mark.asyncio
async def test_rewrite_shortcuts(rewriter, mock_llm_provider):
    """Test shortcut methods for different tones."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content="Result",
        model="test-model",
        tokens_used=5,
        finish_reason="stop"
    )

    # Test professional shortcut
    result = await rewriter.rewrite_professional("test")
    assert result.tone == ToneType.PROFESSIONAL

    # Test friendly shortcut
    result = await rewriter.rewrite_friendly("test")
    assert result.tone == ToneType.FRIENDLY

    # Test concise shortcut
    result = await rewriter.rewrite_concise("test")
    assert result.tone == ToneType.CONCISE


@pytest.mark.asyncio
async def test_default_tone_from_config(mock_llm_provider):
    """Test that default tone is loaded from config."""
    config = {"default_tone": "friendly", "max_tokens": 512, "temperature": 0.7}
    rewriter = TextRewriter(mock_llm_provider, config)

    assert rewriter.default_tone == ToneType.FRIENDLY


def test_tone_prompts_contain_text_placeholder():
    """Test that all tone prompts have text placeholder."""
    for tone, prompt in TextRewriter.TONE_PROMPTS.items():
        assert "{text}" in prompt, f"Prompt for {tone} missing {{text}} placeholder"

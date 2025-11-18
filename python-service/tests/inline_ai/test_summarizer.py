"""
Unit tests for TextSummarizer.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from voice_assistant.inline_ai import TextSummarizer
from voice_assistant.llm.base import CompletionResult


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
        "summary_max_length": 100,
        "max_tokens": 256,
        "temperature": 0.5
    }


@pytest.fixture
def summarizer(mock_llm_provider, config):
    """Create TextSummarizer instance."""
    return TextSummarizer(mock_llm_provider, config)


@pytest.mark.asyncio
async def test_summarize_basic(summarizer, mock_llm_provider):
    """Test basic summarization."""
    long_text = """
    This is a very long piece of text that needs to be summarized.
    It contains multiple sentences and paragraphs of information.
    The summary should capture the main points concisely.
    """

    mock_llm_provider.complete.return_value = CompletionResult(
        content="This text needs summarization and contains key information.",
        model="test-model",
        tokens_used=15,
        finish_reason="stop"
    )

    result = await summarizer.summarize(long_text)

    assert result.success is True
    assert len(result.summary) > 0
    assert result.summary == "This text needs summarization and contains key information."
    assert result.tokens_used == 15
    assert result.compression_ratio < 1.0  # Summary should be shorter
    assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_summarize_with_max_sentences(summarizer, mock_llm_provider):
    """Test summarization with specific sentence count."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content="Brief one sentence summary.",
        model="test-model",
        tokens_used=8,
        finish_reason="stop"
    )

    result = await summarizer.summarize(
        "Long text here...",
        max_sentences=1
    )

    assert result.success is True
    # Verify LLM was called with correct prompt
    call_args = mock_llm_provider.complete.call_args
    messages = call_args.kwargs['messages']
    assert "1 sentence" in messages[0].content.lower()


@pytest.mark.asyncio
async def test_summarize_short_text(summarizer, mock_llm_provider):
    """Test summarization of short text uses short prompt."""
    short_text = "This is a very short text."

    mock_llm_provider.complete.return_value = CompletionResult(
        content="Short text summary.",
        model="test-model",
        tokens_used=5,
        finish_reason="stop"
    )

    result = await summarizer.summarize(short_text)

    assert result.success is True
    # Should use SHORT_PROMPT for texts under 50 words
    assert len(short_text.split()) < 50


@pytest.mark.asyncio
async def test_summarize_removes_quotes(summarizer, mock_llm_provider):
    """Test that summarizer removes quotes from LLM response."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content='"Summary with quotes"',
        model="test-model",
        tokens_used=5,
        finish_reason="stop"
    )

    result = await summarizer.summarize("test text")

    assert result.success is True
    assert result.summary == "Summary with quotes"


@pytest.mark.asyncio
async def test_summarize_timeout(summarizer, mock_llm_provider):
    """Test summarization timeout handling."""
    import asyncio

    async def slow_complete(*args, **kwargs):
        await asyncio.sleep(20)
        return CompletionResult(
            content="Too slow",
            model="test-model",
            tokens_used=5,
            finish_reason="stop"
        )

    mock_llm_provider.complete = slow_complete

    result = await summarizer.summarize(
        "test text",
        timeout_seconds=0.1
    )

    assert result.success is False
    assert "timeout" in result.error.lower()


@pytest.mark.asyncio
async def test_summarize_error_handling(summarizer, mock_llm_provider):
    """Test error handling during summarization."""
    mock_llm_provider.complete.side_effect = Exception("API Error")

    result = await summarizer.summarize("test text")

    assert result.success is False
    assert "API Error" in result.error


@pytest.mark.asyncio
async def test_summarize_compression_ratio(summarizer, mock_llm_provider):
    """Test compression ratio calculation."""
    original = "This is a long text " * 20  # 100 chars
    summary = "Brief summary"  # 13 chars

    mock_llm_provider.complete.return_value = CompletionResult(
        content=summary,
        model="test-model",
        tokens_used=5,
        finish_reason="stop"
    )

    result = await summarizer.summarize(original)

    assert result.success is True
    expected_ratio = len(summary) / len(original)
    assert abs(result.compression_ratio - expected_ratio) < 0.01


@pytest.mark.asyncio
async def test_summarize_brief(summarizer, mock_llm_provider):
    """Test brief summarization shortcut."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content="Brief summary.",
        model="test-model",
        tokens_used=5,
        finish_reason="stop"
    )

    result = await summarizer.summarize_brief("test text")

    assert result.success is True
    # Verify it used max_sentences=1
    call_args = mock_llm_provider.complete.call_args
    # Brief should use 1 sentence


@pytest.mark.asyncio
async def test_summarize_detailed(summarizer, mock_llm_provider):
    """Test detailed summarization shortcut."""
    mock_llm_provider.complete.return_value = CompletionResult(
        content="Detailed five sentence summary with more information.",
        model="test-model",
        tokens_used=15,
        finish_reason="stop"
    )

    result = await summarizer.summarize_detailed("test text")

    assert result.success is True
    # Verify it used max_sentences=5
    call_args = mock_llm_provider.complete.call_args
    messages = call_args.kwargs['messages']
    assert "5 sentence" in messages[0].content.lower()


def test_summarizer_initialization(mock_llm_provider, config):
    """Test summarizer initialization with config."""
    summarizer = TextSummarizer(mock_llm_provider, config)

    assert summarizer.max_summary_length == 100
    assert summarizer.max_tokens == 256
    assert summarizer.temperature == 0.5


def test_prompts_contain_text_placeholder():
    """Test that prompts have text placeholder."""
    assert "{text}" in TextSummarizer.DEFAULT_PROMPT
    assert "{text}" in TextSummarizer.SHORT_PROMPT

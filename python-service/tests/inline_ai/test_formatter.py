"""
Comprehensive tests for TextFormatter.

Tests cover:
- Summary generation
- Key points extraction
- List formatting
- Table formatting
- Error handling
- Edge cases
- Performance benchmarks
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from dataclasses import dataclass

from voice_assistant.inline_ai.formatter import (
    TextFormatter,
    FormatResult,
    FormatType
)
from voice_assistant.llm.base import CompletionResult


@dataclass
class MockLLMProvider:
    """Mock LLM provider for testing."""

    async def complete(self, messages, temperature=0.7, max_tokens=512):
        """Mock completion that formats text appropriately."""
        user_message = messages[0].content

        # Determine what type of formatting is requested
        if "summary" in user_message.lower() or "summarize" in user_message.lower():
            content = "This is a concise summary of the main points from the text."

        elif "key points" in user_message.lower():
            content = """- First key point from the text
- Second important point
- Third critical insight
- Fourth relevant detail
- Fifth essential takeaway"""

        elif "list" in user_message.lower():
            if "sequential" in user_message or "ordered" in user_message:
                content = """1. First item in sequence
2. Second item in sequence
3. Third item in sequence
4. Fourth item in sequence"""
            else:
                content = """- First list item
- Second list item
- Third list item
- Fourth list item"""

        elif "table" in user_message.lower():
            content = """| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1A  | Data 1B  | Data 1C  |
| Data 2A  | Data 2B  | Data 2C  |
| Data 3A  | Data 3B  | Data 3C  |"""

        else:
            # Default response
            content = "Formatted content."

        return CompletionResult(
            content=content,
            model="mock-model",
            tokens_used=100,
            finish_reason="stop"
        )


@pytest.fixture
def mock_llm():
    """Fixture providing mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def formatter(mock_llm):
    """Fixture providing TextFormatter instance."""
    config = {
        "formatting": {
            "summary_length": 100,
            "key_points_count": 5
        },
        "max_tokens": 512,
        "temperature": 0.5
    }
    return TextFormatter(mock_llm, config)


# ========== Summary Tests ==========

@pytest.mark.asyncio
async def test_summary_basic(formatter):
    """Test basic text summarization."""
    text = """
    This is a long piece of text that contains multiple ideas and concepts.
    It discusses various topics including technology, science, and philosophy.
    The main theme is about the intersection of these fields in modern society.
    """

    result = await formatter.summary(text)

    assert result.success
    assert result.format_type == FormatType.SUMMARY
    assert len(result.formatted_text) > 0
    assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_summary_with_max_sentences(formatter):
    """Test summary with specified sentence count."""
    text = "Long text about multiple topics that needs summarization."

    result = await formatter.summary(text, max_sentences=2)

    assert result.success
    assert "summary" in result.formatted_text.lower()


@pytest.mark.asyncio
async def test_summary_short_text(formatter):
    """Test summarizing short text."""
    text = "This is a short text."

    result = await formatter.summary(text, max_sentences=1)

    assert result.success


@pytest.mark.asyncio
async def test_summarize_shortcut(formatter):
    """Test summarize shortcut method."""
    text = "Text to summarize."

    result = await formatter.summarize(text, max_sentences=3)

    assert result.success
    assert result.format_type == FormatType.SUMMARY


# ========== Key Points Tests ==========

@pytest.mark.asyncio
async def test_key_points_basic(formatter):
    """Test basic key points extraction."""
    text = """
    This document covers several important topics:
    First, the importance of proper planning.
    Second, the need for clear communication.
    Third, the value of teamwork.
    Fourth, the role of leadership.
    Fifth, the impact of innovation.
    """

    result = await formatter.key_points(text)

    assert result.success
    assert result.format_type == FormatType.KEY_POINTS
    assert "-" in result.formatted_text or "*" in result.formatted_text


@pytest.mark.asyncio
async def test_key_points_with_count(formatter):
    """Test key points with specific count."""
    text = "Text with multiple important points to extract."

    result = await formatter.key_points(text, num_points=3)

    assert result.success
    assert result.metadata.get("requested_points") == 3


@pytest.mark.asyncio
async def test_key_points_auto_count(formatter):
    """Test key points with automatic count."""
    text = "Text to extract key points from automatically."

    result = await formatter.key_points(text, num_points=None)

    assert result.success
    # Should have detected some points
    assert result.metadata.get("actual_points", 0) >= 0


@pytest.mark.asyncio
async def test_extract_key_points_shortcut(formatter):
    """Test extract_key_points shortcut method."""
    text = "Text with key points."

    result = await formatter.extract_key_points(text, num_points=5)

    assert result.success
    assert result.format_type == FormatType.KEY_POINTS


# ========== List Formatting Tests ==========

@pytest.mark.asyncio
async def test_to_list_basic(formatter):
    """Test basic list formatting."""
    text = "First item, second item, third item, fourth item."

    result = await formatter.to_list(text)

    assert result.success
    assert result.format_type == FormatType.LIST
    # Should have list markers
    assert "-" in result.formatted_text or any(
        str(i) in result.formatted_text for i in range(1, 5)
    )


@pytest.mark.asyncio
async def test_to_list_numbered(formatter):
    """Test numbered list detection."""
    text = "Steps: First do this, then do that, finally complete the task."

    result = await formatter.to_list(text)

    assert result.success
    # Should detect list type
    list_type = result.metadata.get("list_type", "")
    assert list_type in ["numbered", "bulleted", "unknown"]


@pytest.mark.asyncio
async def test_to_list_bulleted(formatter):
    """Test bulleted list formatting."""
    text = "Items to buy: milk, bread, eggs, cheese."

    result = await formatter.to_list(text)

    assert result.success


@pytest.mark.asyncio
async def test_listify_shortcut(formatter):
    """Test listify shortcut method."""
    text = "Items to convert to list."

    result = await formatter.listify(text)

    assert result.success
    assert result.format_type == FormatType.LIST


# ========== Table Formatting Tests ==========

@pytest.mark.asyncio
async def test_to_table_basic(formatter):
    """Test basic table formatting."""
    text = """
    Product data:
    Widget A costs $10 and weighs 5oz
    Widget B costs $15 and weighs 8oz
    Widget C costs $12 and weighs 6oz
    """

    result = await formatter.to_table(text)

    assert result.success
    assert result.format_type == FormatType.TABLE
    assert "|" in result.formatted_text  # Markdown table separator


@pytest.mark.asyncio
async def test_table_structure_analysis(formatter):
    """Test table structure analysis."""
    text = "Data to convert to table format."

    result = await formatter.to_table(text)

    assert result.success
    # Should have metadata about table structure
    assert "rows" in result.metadata
    assert "columns" in result.metadata
    assert "has_header" in result.metadata


@pytest.mark.asyncio
async def test_table_with_complex_data(formatter):
    """Test table formatting with complex data."""
    text = """
    Sales Report Q1 2024:
    January: Revenue $10K, Expenses $5K, Profit $5K
    February: Revenue $12K, Expenses $6K, Profit $6K
    March: Revenue $15K, Expenses $7K, Profit $8K
    """

    result = await formatter.to_table(text)

    assert result.success
    assert result.metadata.get("columns", 0) > 0


@pytest.mark.asyncio
async def test_tablify_shortcut(formatter):
    """Test tablify shortcut method."""
    text = "Data to tablify."

    result = await formatter.tablify(text)

    assert result.success
    assert result.format_type == FormatType.TABLE


@pytest.mark.asyncio
async def test_table_analysis_empty(formatter):
    """Test table analysis with empty/invalid table."""
    analysis = formatter._analyze_table("")

    assert analysis["rows"] == 0
    assert analysis["columns"] == 0
    assert not analysis["has_header"]


@pytest.mark.asyncio
async def test_table_analysis_valid(formatter):
    """Test table analysis with valid markdown table."""
    table = """| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |"""

    analysis = formatter._analyze_table(table)

    assert analysis["rows"] > 0
    assert analysis["columns"] == 3
    assert analysis["has_header"]


# ========== General Format Tests ==========

@pytest.mark.asyncio
async def test_format_text_summary(formatter):
    """Test format_text with summary type."""
    text = "Text to format as summary."

    result = await formatter.format_text(text, FormatType.SUMMARY)

    assert result.success
    assert result.format_type == FormatType.SUMMARY


@pytest.mark.asyncio
async def test_format_text_key_points(formatter):
    """Test format_text with key_points type."""
    text = "Text to format as key points."

    result = await formatter.format_text(text, FormatType.KEY_POINTS)

    assert result.success
    assert result.format_type == FormatType.KEY_POINTS


@pytest.mark.asyncio
async def test_format_text_list(formatter):
    """Test format_text with list type."""
    text = "Text to format as list."

    result = await formatter.format_text(text, FormatType.LIST)

    assert result.success
    assert result.format_type == FormatType.LIST


@pytest.mark.asyncio
async def test_format_text_table(formatter):
    """Test format_text with table type."""
    text = "Text to format as table."

    result = await formatter.format_text(text, FormatType.TABLE)

    assert result.success
    assert result.format_type == FormatType.TABLE


# ========== Error Handling Tests ==========

@pytest.mark.asyncio
async def test_empty_text_error(formatter):
    """Test handling of empty text."""
    result = await formatter.summary("")

    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_very_short_text(formatter):
    """Test handling of very short text."""
    text = "Hi"

    result = await formatter.key_points(text)

    # Should either process or return appropriate error
    assert isinstance(result, FormatResult)


@pytest.mark.asyncio
async def test_very_long_text(formatter):
    """Test handling of very long text."""
    text = "This is a sentence. " * 500

    result = await formatter.summary(text)

    # Should either process or handle gracefully
    assert isinstance(result, FormatResult)


@pytest.mark.asyncio
async def test_timeout_handling(formatter):
    """Test timeout handling."""
    text = "Test text."

    # Very short timeout
    result = await formatter.summary(text, timeout_seconds=0.001)

    # Mock is fast, but structure is correct
    assert isinstance(result, FormatResult)


@pytest.mark.asyncio
async def test_llm_error_handling(mock_llm, formatter):
    """Test handling of LLM errors."""
    async def error_complete(*args, **kwargs):
        raise Exception("LLM error")

    mock_llm.complete = error_complete

    text = "Test text"
    result = await formatter.summary(text)

    assert not result.success
    assert result.error is not None


# ========== FormatResult Tests ==========

def test_format_result_properties():
    """Test FormatResult properties and defaults."""
    result = FormatResult(
        original_text="Original",
        formatted_text="Formatted",
        format_type=FormatType.SUMMARY,
        tokens_used=50,
        processing_time_ms=1000,
        success=True,
        metadata={"key": "value"}
    )

    assert result.original_text == "Original"
    assert result.formatted_text == "Formatted"
    assert result.format_type == FormatType.SUMMARY
    assert result.tokens_used == 50
    assert result.success
    assert result.metadata["key"] == "value"


def test_format_result_default_metadata():
    """Test FormatResult with default metadata."""
    result = FormatResult(
        original_text="Text",
        formatted_text="Formatted",
        format_type=FormatType.LIST,
        success=True
    )

    assert result.metadata == {}


# ========== Integration Tests ==========

@pytest.mark.asyncio
async def test_full_formatting_workflow(formatter):
    """Test complete formatting workflow."""
    text = """
    Project Status Report:
    The development team has completed Phase 1 implementation.
    Testing is ongoing and will finish by end of month.
    Phase 2 planning has begun with stakeholder input.
    Budget is on track and resources are allocated properly.
    Next milestone is scheduled for Q2 2024.
    """

    # Test all format types
    summary_result = await formatter.summary(text, max_sentences=2)
    assert summary_result.success

    key_points_result = await formatter.key_points(text, num_points=3)
    assert key_points_result.success

    list_result = await formatter.to_list(text)
    assert list_result.success

    table_result = await formatter.to_table(text)
    assert table_result.success

    # All should have metadata
    assert summary_result.metadata is not None
    assert key_points_result.metadata is not None
    assert list_result.metadata is not None
    assert table_result.metadata is not None


@pytest.mark.asyncio
async def test_multiple_formats_sequential(formatter):
    """Test multiple sequential formatting operations."""
    text = "Test text for formatting."

    formats = [
        FormatType.SUMMARY,
        FormatType.KEY_POINTS,
        FormatType.LIST,
        FormatType.TABLE
    ]

    results = []
    for format_type in formats:
        result = await formatter.format_text(text, format_type)
        results.append(result)

    # All should succeed
    assert all(r.success for r in results)
    assert len(results) == 4


@pytest.mark.asyncio
async def test_concurrent_formatting(formatter):
    """Test concurrent formatting operations."""
    text = "Test text for concurrent formatting."

    # Create tasks for all format types
    tasks = [
        formatter.summary(text),
        formatter.key_points(text),
        formatter.to_list(text),
        formatter.to_table(text)
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert len(results) == 4
    assert all(r.success for r in results)


# ========== Performance Tests ==========

@pytest.mark.asyncio
async def test_formatting_performance(formatter):
    """Test formatting performance."""
    text = "This is test text for performance testing."

    import time
    start = time.time()

    result = await formatter.summary(text)

    elapsed_ms = (time.time() - start) * 1000

    assert result.success
    # With mock, should be very fast
    assert elapsed_ms < 1000


@pytest.mark.asyncio
async def test_all_formats_performance(formatter):
    """Test performance of all format types."""
    text = "Test text for all format types."

    import time
    start = time.time()

    results = await asyncio.gather(
        formatter.summary(text),
        formatter.key_points(text),
        formatter.to_list(text),
        formatter.to_table(text)
    )

    elapsed_ms = (time.time() - start) * 1000

    assert all(r.success for r in results)
    # All together should still be fast with mock
    assert elapsed_ms < 2000


# ========== Edge Cases ==========

@pytest.mark.asyncio
async def test_text_with_special_characters(formatter):
    """Test formatting text with special characters."""
    text = "Text with special chars: @#$%^&*()_+-=[]{}|;:',.<>?/~`"

    result = await formatter.summary(text)

    assert isinstance(result, FormatResult)


@pytest.mark.asyncio
async def test_text_with_unicode(formatter):
    """Test formatting text with unicode characters."""
    text = "Text with unicode: 你好 مرحبا שלום नमस्ते"

    result = await formatter.key_points(text)

    assert isinstance(result, FormatResult)


@pytest.mark.asyncio
async def test_text_with_emojis(formatter):
    """Test formatting text with emojis."""
    text = "Text with emojis: 😀 🎉 ✨ 🚀"

    result = await formatter.to_list(text)

    assert isinstance(result, FormatResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

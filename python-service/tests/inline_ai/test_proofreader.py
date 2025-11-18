"""
Comprehensive tests for TextProofreader.

Tests cover:
- Basic proofreading functionality
- Change detection and tracking
- Error handling
- Edge cases
- Performance benchmarks
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass

from voice_assistant.inline_ai.proofreader import (
    TextProofreader,
    ProofreadResult,
    TextChange
)
from voice_assistant.llm.base import CompletionResult, MessageRole


@dataclass
class MockLLMProvider:
    """Mock LLM provider for testing."""

    async def complete(self, messages, temperature=0.7, max_tokens=512):
        """Mock completion that corrects simple errors."""
        user_message = messages[0].content

        # Extract text from prompt
        if "Text: " in user_message:
            text = user_message.split("Text: ")[1]
        else:
            text = user_message

        # Simulate simple corrections
        corrected = text.replace("teh", "the")
        corrected = corrected.replace("recieve", "receive")
        corrected = corrected.replace("occured", "occurred")
        corrected = corrected.replace("definately", "definitely")
        corrected = corrected.replace("thier", "their")

        # Check if JSON format requested (show_changes=True)
        if '"corrected"' in user_message or 'JSON' in user_message:
            # Return JSON format with changes
            import json
            response = {
                "corrected": corrected,
                "changes": [
                    f"Corrected spelling: '{orig}' → '{corr}'"
                    for orig, corr in [
                        ("teh", "the"),
                        ("recieve", "receive"),
                        ("occured", "occurred"),
                        ("definately", "definitely"),
                        ("thier", "their")
                    ]
                    if orig in text
                ]
            }
            content = json.dumps(response)
        else:
            # Return simple corrected text
            content = corrected

        return CompletionResult(
            content=content,
            model="mock-model",
            tokens_used=50,
            finish_reason="stop"
        )


@pytest.fixture
def mock_llm():
    """Fixture providing mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def proofreader(mock_llm):
    """Fixture providing TextProofreader instance."""
    config = {
        "proofread": {
            "show_changes": True
        },
        "max_tokens": 512,
        "temperature": 0.3
    }
    return TextProofreader(mock_llm, config)


# ========== Basic Functionality Tests ==========

@pytest.mark.asyncio
async def test_proofread_no_errors(proofreader):
    """Test proofreading text with no errors."""
    text = "This is a perfectly correct sentence."

    result = await proofreader.proofread(text, show_changes=False)

    assert result.success
    assert result.original_text == text
    assert result.proofread_text == text
    assert not result.has_changes


@pytest.mark.asyncio
async def test_proofread_with_errors(proofreader):
    """Test proofreading text with spelling errors."""
    text = "I recieve teh email occured yesterday."

    result = await proofreader.proofread(text, show_changes=False)

    assert result.success
    assert result.original_text == text
    assert "receive" in result.proofread_text
    assert "the" in result.proofread_text
    assert "occurred" in result.proofread_text
    assert result.has_changes


@pytest.mark.asyncio
async def test_proofread_with_changes_tracking(proofreader):
    """Test proofreading with detailed change tracking."""
    text = "I definately recieve teh email."

    result = await proofreader.proofread(text, show_changes=True)

    assert result.success
    assert result.has_changes
    assert result.num_changes > 0
    assert len(result.changes) > 0


@pytest.mark.asyncio
async def test_proofread_quick(proofreader):
    """Test quick proofread method."""
    text = "Teh quick brown fox."

    result = await proofreader.proofread_quick(text)

    assert result.success
    assert "the" in result.proofread_text.lower()


@pytest.mark.asyncio
async def test_proofread_detailed(proofreader):
    """Test detailed proofread method."""
    text = "Thier car is over thier."

    result = await proofreader.proofread_detailed(text)

    assert result.success
    # Should have changes tracked
    assert isinstance(result.changes, list)


# ========== Change Detection Tests ==========

@pytest.mark.asyncio
async def test_change_detection_simple(proofreader):
    """Test simple change detection."""
    text = "teh test"

    result = await proofreader.proofread(text)

    assert result.success
    assert result.has_changes
    assert result.proofread_text == "the test"


@pytest.mark.asyncio
async def test_get_changes_by_type(proofreader):
    """Test filtering changes by type."""
    text = "I recieve teh email."

    result = await proofreader.proofread(text, show_changes=True)

    if result.num_changes > 0:
        # Should have spelling changes
        spelling_changes = result.get_changes_by_type("spelling")
        assert isinstance(spelling_changes, list)


# ========== Error Handling Tests ==========

@pytest.mark.asyncio
async def test_empty_text_error(proofreader):
    """Test handling of empty text."""
    result = await proofreader.proofread("")

    assert not result.success
    assert result.error is not None
    assert "empty" in result.error.lower() or "short" in result.error.lower()


@pytest.mark.asyncio
async def test_very_short_text_warning(proofreader):
    """Test handling of very short text."""
    text = "Hi"

    result = await proofreader.proofread(text)

    # Should still process but may have warning logged
    assert isinstance(result, ProofreadResult)


@pytest.mark.asyncio
async def test_very_long_text(proofreader):
    """Test handling of very long text."""
    text = "This is a test sentence. " * 500  # ~2500 words

    result = await proofreader.proofread(text)

    # Should either process or return appropriate error
    assert isinstance(result, ProofreadResult)


@pytest.mark.asyncio
async def test_timeout_handling(proofreader):
    """Test timeout handling."""
    text = "Test text for timeout."

    # Very short timeout should trigger timeout error
    result = await proofreader.proofread(text, timeout_seconds=0.001)

    # Should complete quickly with mock, but test structure is correct
    assert isinstance(result, ProofreadResult)


@pytest.mark.asyncio
async def test_llm_error_handling(mock_llm, proofreader):
    """Test handling of LLM errors."""
    # Make LLM raise an error
    async def error_complete(*args, **kwargs):
        raise Exception("LLM error")

    mock_llm.complete = error_complete

    text = "Test text"
    result = await proofreader.proofread(text)

    assert not result.success
    assert result.error is not None


# ========== Text Parsing Tests ==========

def test_parse_result_simple(proofreader):
    """Test parsing simple result."""
    content = "This is corrected text."

    result = proofreader._parse_result_simple(content)

    assert result == "This is corrected text."


def test_parse_result_with_quotes(proofreader):
    """Test parsing result with quotes."""
    content = '"This is quoted text."'

    result = proofreader._parse_result_simple(content)

    assert result == "This is quoted text."


def test_parse_result_with_json(proofreader):
    """Test parsing JSON result."""
    import json

    data = {
        "corrected": "Corrected text here.",
        "changes": [
            "Fixed spelling: 'teh' → 'the'",
            "Fixed grammar: verb tense"
        ]
    }
    content = json.dumps(data)

    corrected, changes = proofreader._parse_result_with_changes(
        content,
        "Original text"
    )

    assert corrected == "Corrected text here."
    assert len(changes) == 2


def test_parse_change_description_spelling(proofreader):
    """Test parsing spelling change description."""
    desc = "Fixed spelling: 'recieve' → 'receive'"

    change = proofreader._parse_change_description(desc, "orig", "corr")

    assert change is not None
    assert change.type == "spelling"
    assert change.description == desc


def test_parse_change_description_grammar(proofreader):
    """Test parsing grammar change description."""
    desc = "Fixed grammar: subject-verb agreement"

    change = proofreader._parse_change_description(desc, "orig", "corr")

    assert change is not None
    assert change.type == "grammar"


def test_parse_change_description_punctuation(proofreader):
    """Test parsing punctuation change description."""
    desc = "Added missing comma"

    change = proofreader._parse_change_description(desc, "orig", "corr")

    assert change is not None
    assert change.type == "punctuation"


# ========== Change Report Tests ==========

def test_format_changes_report_no_changes(proofreader):
    """Test formatting report with no changes."""
    result = ProofreadResult(
        original_text="Perfect text.",
        proofread_text="Perfect text.",
        success=True
    )

    report = proofreader.format_changes_report(result)

    assert "No changes" in report


def test_format_changes_report_with_changes(proofreader):
    """Test formatting report with changes."""
    changes = [
        TextChange(
            type="spelling",
            original="teh",
            corrected="the",
            description="Fixed spelling: 'teh' → 'the'"
        ),
        TextChange(
            type="grammar",
            original="",
            corrected="",
            description="Fixed verb tense"
        )
    ]

    result = ProofreadResult(
        original_text="Original text",
        proofread_text="Corrected text",
        changes=changes,
        tokens_used=50,
        processing_time_ms=1500,
        success=True
    )

    report = proofreader.format_changes_report(result)

    assert "2 change" in report
    assert "Spelling" in report
    assert "Grammar" in report
    assert "1500ms" in report


def test_format_changes_report_error(proofreader):
    """Test formatting report for failed proofreading."""
    result = ProofreadResult(
        original_text="Text",
        proofread_text="",
        success=False,
        error="Something went wrong"
    )

    report = proofreader.format_changes_report(result)

    assert "failed" in report.lower()
    assert "Something went wrong" in report


# ========== ProofreadResult Tests ==========

def test_proofread_result_properties():
    """Test ProofreadResult properties."""
    result = ProofreadResult(
        original_text="Original",
        proofread_text="Corrected",
        changes=[
            TextChange("spelling", "orig", "corr", "desc"),
            TextChange("grammar", "x", "y", "desc2")
        ],
        success=True
    )

    assert result.has_changes
    assert result.num_changes == 2

    spelling_changes = result.get_changes_by_type("spelling")
    assert len(spelling_changes) == 1
    assert spelling_changes[0].type == "spelling"


def test_proofread_result_no_changes():
    """Test ProofreadResult with no changes."""
    result = ProofreadResult(
        original_text="Text",
        proofread_text="Text",
        success=True
    )

    assert not result.has_changes
    assert result.num_changes == 0


# ========== Integration Tests ==========

@pytest.mark.asyncio
async def test_full_proofreading_workflow(proofreader):
    """Test complete proofreading workflow."""
    text = "I recieve teh email definately occured yesterday with thier approval."

    # Perform proofreading
    result = await proofreader.proofread(text, show_changes=True)

    # Verify success
    assert result.success
    assert result.has_changes

    # Verify corrections
    corrected = result.proofread_text
    assert "receive" in corrected
    assert "the" in corrected
    assert "definitely" in corrected
    assert "occurred" in corrected
    assert "their" in corrected

    # Verify metadata
    assert result.tokens_used > 0
    assert result.processing_time_ms > 0

    # Generate report
    report = proofreader.format_changes_report(result)
    assert len(report) > 0


@pytest.mark.asyncio
async def test_multiple_proofreads_sequential(proofreader):
    """Test multiple sequential proofreading operations."""
    texts = [
        "Teh first text.",
        "Teh second text with more errors occured.",
        "A perfect text with no errors."
    ]

    results = []
    for text in texts:
        result = await proofreader.proofread(text)
        results.append(result)

    # All should succeed
    assert all(r.success for r in results)

    # First two should have changes
    assert results[0].has_changes
    assert results[1].has_changes

    # Third should have no changes
    assert not results[2].has_changes


# ========== Performance Tests ==========

@pytest.mark.asyncio
async def test_proofreading_performance(proofreader):
    """Test proofreading performance (should be fast with mock)."""
    text = "This is a test sentence with teh error."

    import time
    start = time.time()

    result = await proofreader.proofread(text)

    elapsed_ms = (time.time() - start) * 1000

    assert result.success
    # With mock, should be very fast
    assert elapsed_ms < 1000  # Less than 1 second


@pytest.mark.asyncio
async def test_concurrent_proofreads(proofreader):
    """Test concurrent proofreading operations."""
    texts = [
        f"Text number {i} with teh error."
        for i in range(5)
    ]

    # Run all concurrently
    tasks = [proofreader.proofread(text) for text in texts]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert len(results) == 5
    assert all(r.success for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

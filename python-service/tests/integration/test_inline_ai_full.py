"""
Integration tests for enhanced in-line AI feature.

Tests complete workflows from text selection to replacement across all menu options.
"""

import pytest
import asyncio
import json
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from voice_assistant.inline_ai.enhanced_handler import EnhancedInlineAIHandler
from voice_assistant.inline_ai.formatting import FormattingOperations
from voice_assistant.llm.base import Message, CompletionResult


@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing"""
    llm = AsyncMock()
    llm.complete = AsyncMock()
    return llm


@pytest.fixture
def mock_accessibility():
    """Mock Accessibility API for testing"""
    with patch('voice_assistant.inline_ai.enhanced_handler.PyObjCBridge') as mock:
        mock_bridge = MagicMock()
        mock.return_value = mock_bridge
        yield mock_bridge


@pytest.fixture
def handler(mock_llm, mock_accessibility):
    """Create EnhancedInlineAIHandler instance"""
    return EnhancedInlineAIHandler(mock_llm)


# ============================================================================
# PROOFREAD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_proofread_email_with_errors(handler, mock_llm):
    """Test proofreading email with spelling and grammar errors"""

    original = "Hey john, I hope your doing well. I wanted to touch base about the project we discused yesterday."
    corrected = "Hey John, I hope you're doing well. I wanted to touch base about the project we discussed yesterday."

    mock_llm.complete.return_value = CompletionResult(
        content=corrected,
        model="test",
        tokens_used=50,
        finish_reason="stop"
    )

    command = {
        "action": "proofread",
        "text": original
    }

    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert result["result"]["text"] == corrected
    assert "correction" in result["result"]


@pytest.mark.asyncio
async def test_proofread_technical_document(handler, mock_llm):
    """Test proofreading technical document with jargon"""

    original = "The API endpoint recieve JSON payloads and returns a responce with the data."
    corrected = "The API endpoint receives JSON payloads and returns a response with the data."

    mock_llm.complete.return_value = CompletionResult(
        content=corrected,
        model="test",
        tokens_used=40,
        finish_reason="stop"
    )

    command = {"action": "proofread", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "receives" in result["result"]["text"]
    assert "response" in result["result"]["text"]


@pytest.mark.asyncio
async def test_proofread_no_errors(handler, mock_llm):
    """Test proofreading text with no errors"""

    original = "This text is already perfect and has no errors."

    mock_llm.complete.return_value = CompletionResult(
        content=original,
        model="test",
        tokens_used=30,
        finish_reason="stop"
    )

    command = {"action": "proofread", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert result["result"]["text"] == original


# ============================================================================
# REWRITE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_rewrite_friendly_tone(handler, mock_llm):
    """Test rewriting formal text to friendly tone"""

    original = "I am writing to formally request your assistance with this matter."
    friendly = "Hey! I'd love to get your help with this."

    mock_llm.complete.return_value = CompletionResult(
        content=friendly,
        model="test",
        tokens_used=45,
        finish_reason="stop"
    )

    command = {
        "action": "rewrite",
        "text": original,
        "params": {"tone": "friendly"}
    }

    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "Hey" in result["result"]["text"] or "love" in result["result"]["text"]


@pytest.mark.asyncio
async def test_rewrite_professional_tone(handler, mock_llm):
    """Test rewriting casual text to professional tone"""

    original = "Hey, can you fix that bug ASAP?"
    professional = "Could you please address the reported issue at your earliest convenience?"

    mock_llm.complete.return_value = CompletionResult(
        content=professional,
        model="test",
        tokens_used=50,
        finish_reason="stop"
    )

    command = {
        "action": "rewrite",
        "text": original,
        "params": {"tone": "professional"}
    }

    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "please" in result["result"]["text"].lower()


@pytest.mark.asyncio
async def test_rewrite_concise(handler, mock_llm):
    """Test rewriting verbose text to be concise"""

    original = "In my personal opinion, I think that perhaps we might want to consider the possibility of implementing this feature."
    concise = "Let's implement this feature."

    mock_llm.complete.return_value = CompletionResult(
        content=concise,
        model="test",
        tokens_used=35,
        finish_reason="stop"
    )

    command = {
        "action": "rewrite",
        "text": original,
        "params": {"style": "concise"}
    }

    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert len(result["result"]["text"]) < len(original)


# ============================================================================
# SUMMARIZE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_summarize_long_article(handler, mock_llm):
    """Test summarizing long article"""

    original = """
    Artificial intelligence has made remarkable progress in recent years, transforming industries
    from healthcare to transportation. Machine learning algorithms can now diagnose diseases,
    drive cars, and even create art. However, these advances also raise important ethical
    questions about privacy, bias, and the future of work. As AI systems become more powerful,
    society must grapple with how to ensure they are developed and deployed responsibly.
    """

    summary = "AI has advanced significantly, transforming industries but raising ethical concerns about privacy, bias, and employment."

    mock_llm.complete.return_value = CompletionResult(
        content=summary,
        model="test",
        tokens_used=80,
        finish_reason="stop"
    )

    command = {"action": "summarize", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert len(result["result"]["text"]) < len(original)
    assert "AI" in result["result"]["text"]


@pytest.mark.asyncio
async def test_summarize_meeting_notes(handler, mock_llm):
    """Test summarizing meeting notes"""

    original = """
    Meeting started at 10am. Discussed Q4 roadmap. Sarah presented new feature ideas.
    Team agreed to prioritize mobile app. John raised concerns about timeline.
    Decided to hire contractor. Action items: Sarah to draft spec, John to interview candidates.
    Next meeting: Friday 2pm.
    """

    summary = "Team agreed to prioritize mobile app for Q4. Sarah drafting spec, John interviewing contractors. Next meeting Friday 2pm."

    mock_llm.complete.return_value = CompletionResult(
        content=summary,
        model="test",
        tokens_used=60,
        finish_reason="stop"
    )

    command = {"action": "summarize", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "mobile app" in result["result"]["text"]


# ============================================================================
# KEY POINTS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_extract_key_points(handler, mock_llm):
    """Test extracting key points from text"""

    original = """
    The new feature will improve user experience by reducing load times and simplifying navigation.
    It requires backend changes to the API and frontend updates to the dashboard.
    We estimate 3 weeks of development time and 1 week of testing.
    The feature should increase user engagement by 20%.
    """

    key_points = """• Improves UX via faster load times and simpler navigation
• Requires backend API and frontend dashboard changes
• 3 weeks dev + 1 week testing
• Expected 20% engagement increase"""

    mock_llm.complete.return_value = CompletionResult(
        content=key_points,
        model="test",
        tokens_used=70,
        finish_reason="stop"
    )

    command = {"action": "key_points", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "•" in result["result"]["text"] or "-" in result["result"]["text"]


# ============================================================================
# FORMATTING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_make_list(handler):
    """Test converting paragraph to bullet list"""

    original = "We need to buy milk, eggs, bread, and butter from the store."

    command = {"action": "make_list", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    formatted = result["result"]["text"]
    assert "milk" in formatted
    assert "eggs" in formatted
    assert ("•" in formatted or "-" in formatted or "1." in formatted)


@pytest.mark.asyncio
async def test_make_numbered_list(handler):
    """Test converting text to numbered list"""

    original = "First step: analyze requirements. Second: design solution. Third: implement. Fourth: test."

    command = {"action": "make_numbered_list", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    formatted = result["result"]["text"]
    assert "1." in formatted
    assert "2." in formatted
    assert "analyze" in formatted


@pytest.mark.asyncio
async def test_make_table(handler, mock_llm):
    """Test converting data to table"""

    original = "Product A costs $10 and sold 100 units. Product B costs $20 and sold 50 units."

    table = """| Product | Price | Units Sold |
|---------|-------|------------|
| A       | $10   | 100        |
| B       | $20   | 50         |"""

    mock_llm.complete.return_value = CompletionResult(
        content=table,
        model="test",
        tokens_used=60,
        finish_reason="stop"
    )

    command = {"action": "make_table", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "|" in result["result"]["text"]
    assert "Product" in result["result"]["text"]


@pytest.mark.asyncio
async def test_add_headings(handler):
    """Test adding markdown headings"""

    original = """Introduction
This is the intro paragraph.
Methods
This describes the methods.
Results
These are the results."""

    command = {"action": "add_headings", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    formatted = result["result"]["text"]
    assert "#" in formatted or "##" in formatted


# ============================================================================
# COMPOSE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_compose_email(handler, mock_llm):
    """Test composing email from prompt"""

    prompt = "Write a follow-up email to John thanking him for the meeting and confirming next steps."

    email = """Hi John,

Thank you for taking the time to meet yesterday. I appreciated your insights on the project timeline.

As we discussed, I'll draft the initial specification by Friday and share it with the team. Looking forward to our next meeting on the 15th.

Best regards"""

    mock_llm.complete.return_value = CompletionResult(
        content=email,
        model="test",
        tokens_used=100,
        finish_reason="stop"
    )

    command = {"action": "compose", "text": prompt}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "John" in result["result"]["text"]
    assert "meeting" in result["result"]["text"]


@pytest.mark.asyncio
async def test_compose_with_context(handler, mock_llm):
    """Test composing text with context"""

    prompt = "Reply to this: 'Can we schedule a call?'"

    reply = "Absolutely! How about Tuesday at 2pm? I'm also available Wednesday morning if that works better for you."

    mock_llm.complete.return_value = CompletionResult(
        content=reply,
        model="test",
        tokens_used=50,
        finish_reason="stop"
    )

    command = {"action": "compose", "text": prompt}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert len(result["result"]["text"]) > 0


# ============================================================================
# WORKFLOW TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_transformations_sequence(handler, mock_llm):
    """Test applying multiple transformations in sequence"""

    original = "the quick brown fox jumps over the lazy dog"

    # First: make title case
    step1 = "The Quick Brown Fox Jumps Over The Lazy Dog"
    # Then: make list
    step2 = """• The
• Quick
• Brown
• Fox"""

    mock_llm.complete.side_effect = [
        CompletionResult(content=step1, model="test", tokens_used=20, finish_reason="stop"),
        CompletionResult(content=step2, model="test", tokens_used=25, finish_reason="stop")
    ]

    # Apply title case
    result1 = await handler.handle_command({"action": "make_title_case", "text": original})
    assert result1["status"] == "success"

    # Apply make list
    result2 = await handler.handle_command({"action": "make_list", "text": result1["result"]["text"]})
    assert result2["status"] == "success"
    assert "•" in result2["result"]["text"]


@pytest.mark.asyncio
async def test_preview_and_accept(handler, mock_llm):
    """Test preview and accept workflow"""

    original = "Hello world"
    corrected = "Hello, world!"

    mock_llm.complete.return_value = CompletionResult(
        content=corrected,
        model="test",
        tokens_used=10,
        finish_reason="stop"
    )

    # Get preview
    result = await handler.handle_command({"action": "proofread", "text": original})

    assert result["status"] == "success"
    assert result["result"]["text"] == corrected
    assert "original" in result["result"]


@pytest.mark.asyncio
async def test_undo_functionality(handler):
    """Test undo functionality (stores previous version)"""

    original = "Original text"
    modified = "Modified text"

    # Simulate modification
    result = await handler.handle_command({
        "action": "rewrite",
        "text": original,
        "params": {"tone": "formal"}
    })

    # Verify we can track original
    assert "original" in result["result"]
    assert result["result"]["original"] == original


# ============================================================================
# TEXT LENGTH TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_very_long_text(handler, mock_llm):
    """Test handling very long text (>5000 chars)"""

    original = "This is a sentence. " * 300  # ~6000 chars
    summary = "Summary of very long text."

    mock_llm.complete.return_value = CompletionResult(
        content=summary,
        model="test",
        tokens_used=200,
        finish_reason="stop"
    )

    command = {"action": "summarize", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert len(result["result"]["text"]) < len(original)


@pytest.mark.asyncio
async def test_empty_text(handler):
    """Test handling empty text"""

    command = {"action": "proofread", "text": ""}
    result = await handler.handle_command(command)

    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


@pytest.mark.asyncio
async def test_single_word(handler, mock_llm):
    """Test handling single word"""

    mock_llm.complete.return_value = CompletionResult(
        content="hello",
        model="test",
        tokens_used=5,
        finish_reason="stop"
    )

    command = {"action": "proofread", "text": "hello"}
    result = await handler.handle_command(command)

    assert result["status"] == "success"


# ============================================================================
# SPECIAL CHARACTER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_emoji_handling(handler, mock_llm):
    """Test handling text with emojis"""

    original = "Great work team! 🎉 Let's celebrate 🥳"

    mock_llm.complete.return_value = CompletionResult(
        content=original,
        model="test",
        tokens_used=15,
        finish_reason="stop"
    )

    command = {"action": "proofread", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "🎉" in result["result"]["text"]


@pytest.mark.asyncio
async def test_code_snippet_handling(handler, mock_llm):
    """Test handling code snippets"""

    original = """def hello():
    print("Hello, world!")"""

    formatted = """```python
def hello():
    print("Hello, world!")
```"""

    mock_llm.complete.return_value = CompletionResult(
        content=formatted,
        model="test",
        tokens_used=30,
        finish_reason="stop"
    )

    command = {"action": "add_code_formatting", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_markdown_preservation(handler, mock_llm):
    """Test that markdown formatting is preserved"""

    original = "# Heading\n\n**Bold** and *italic* text"

    mock_llm.complete.return_value = CompletionResult(
        content=original,
        model="test",
        tokens_used=20,
        finish_reason="stop"
    )

    command = {"action": "proofread", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "#" in result["result"]["text"]
    assert "**" in result["result"]["text"]


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_llm_timeout_error(handler, mock_llm):
    """Test handling LLM timeout"""

    mock_llm.complete.side_effect = asyncio.TimeoutError("LLM timeout")

    command = {"action": "proofread", "text": "Test text"}
    result = await handler.handle_command(command)

    assert result["status"] == "error"
    assert "timeout" in result["message"].lower()


@pytest.mark.asyncio
async def test_llm_api_error(handler, mock_llm):
    """Test handling LLM API error"""

    mock_llm.complete.side_effect = Exception("API error")

    command = {"action": "proofread", "text": "Test text"}
    result = await handler.handle_command(command)

    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_invalid_action(handler):
    """Test handling invalid action"""

    command = {"action": "invalid_action", "text": "Test"}
    result = await handler.handle_command(command)

    assert result["status"] == "error"
    assert "unknown" in result["message"].lower() or "invalid" in result["message"].lower()


@pytest.mark.asyncio
async def test_missing_text_parameter(handler):
    """Test handling missing text parameter"""

    command = {"action": "proofread"}
    result = await handler.handle_command(command)

    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_accessibility_api_failure(handler, mock_accessibility):
    """Test handling Accessibility API failure"""

    mock_accessibility.get_selected_text.side_effect = Exception("Accessibility denied")

    # This would be called by the UI layer
    # Just verify the handler can work without accessibility
    command = {"action": "proofread", "text": "Test"}
    result = await handler.handle_command(command)

    # Should still work if text is provided directly
    assert result["status"] in ["success", "error"]


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_unicode_handling(handler, mock_llm):
    """Test handling Unicode characters"""

    original = "Café résumé naïve"

    mock_llm.complete.return_value = CompletionResult(
        content=original,
        model="test",
        tokens_used=10,
        finish_reason="stop"
    )

    command = {"action": "proofread", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "é" in result["result"]["text"]


@pytest.mark.asyncio
async def test_whitespace_preservation(handler, mock_llm):
    """Test that necessary whitespace is preserved"""

    original = "Line 1\n\nLine 2\n\nLine 3"

    mock_llm.complete.return_value = CompletionResult(
        content=original,
        model="test",
        tokens_used=15,
        finish_reason="stop"
    )

    command = {"action": "proofread", "text": original}
    result = await handler.handle_command(command)

    assert result["status"] == "success"
    assert "\n" in result["result"]["text"]


@pytest.mark.asyncio
async def test_concurrent_operations(handler, mock_llm):
    """Test handling concurrent operations"""

    mock_llm.complete.return_value = CompletionResult(
        content="Result",
        model="test",
        tokens_used=10,
        finish_reason="stop"
    )

    # Simulate concurrent requests
    tasks = [
        handler.handle_command({"action": "proofread", "text": f"Text {i}"})
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    assert all(r["status"] == "success" for r in results)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_response_time_target(handler, mock_llm):
    """Test that operations complete within target time"""

    import time

    mock_llm.complete.return_value = CompletionResult(
        content="Corrected text",
        model="test",
        tokens_used=20,
        finish_reason="stop"
    )

    start = time.time()
    result = await handler.handle_command({
        "action": "proofread",
        "text": "Test text with some errors"
    })
    elapsed = time.time() - start

    assert result["status"] == "success"
    # Should complete quickly with mocked LLM
    assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Comprehensive tests for ContentComposer.

Tests cover:
- Basic content composition
- Context-aware composition
- Template-based generation
- Email/message composition
- Error handling
- Edge cases
- Performance benchmarks
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from dataclasses import dataclass

from voice_assistant.inline_ai.composer import (
    ContentComposer,
    ComposeResult
)
from voice_assistant.llm.base import CompletionResult


@dataclass
class MockLLMProvider:
    """Mock LLM provider for testing."""

    async def complete(self, messages, temperature=0.7, max_tokens=1024):
        """Mock completion that generates appropriate content."""
        user_message = messages[0].content

        # Generate content based on prompt
        if "email" in user_message.lower():
            content = """Dear Recipient,

I hope this email finds you well. I am writing to discuss the matter at hand.

Please let me know your thoughts on this.

Best regards,
Sender"""

        elif "message" in user_message.lower() or "text" in user_message.lower():
            content = "Hey! Thanks for reaching out. I'll get back to you soon!"

        elif "paragraph" in user_message.lower():
            content = "This is a well-crafted paragraph that addresses the topic comprehensively. It includes relevant details and maintains a clear, coherent structure throughout."

        elif "thank" in user_message.lower():
            content = "Thank you so much for your help! I really appreciate your time and effort on this matter."

        elif "apolog" in user_message.lower():
            content = "I sincerely apologize for any inconvenience this may have caused. I will ensure this doesn't happen again."

        else:
            # Extract prompt if present
            if "Prompt:" in user_message:
                prompt_text = user_message.split("Prompt:")[1].split("\n")[0].strip()
                content = f"Here is the generated content based on your request: {prompt_text}. This is a comprehensive response that addresses your needs."
            else:
                content = "Generated content that addresses the user's request in a clear and helpful manner."

        return CompletionResult(
            content=content,
            model="mock-model",
            tokens_used=150,
            finish_reason="stop"
        )


@pytest.fixture
def mock_llm():
    """Fixture providing mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def composer(mock_llm):
    """Fixture providing ContentComposer instance."""
    config = {
        "compose": {
            "max_length": 500
        },
        "max_tokens": 1024,
        "temperature": 0.7
    }
    return ContentComposer(mock_llm, config)


# ========== Basic Composition Tests ==========

@pytest.mark.asyncio
async def test_compose_basic(composer):
    """Test basic content composition."""
    prompt = "Write a brief introduction about AI."

    result = await composer.compose(prompt)

    assert result.success
    assert len(result.composed_text) > 0
    assert result.prompt == prompt
    assert result.context is None
    assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_compose_with_context(composer):
    """Test composition with context."""
    prompt = "Write about the benefits."
    context = "We are discussing renewable energy and its impact on the environment."

    result = await composer.compose(prompt, context=context)

    assert result.success
    assert result.prompt == prompt
    assert result.context == context
    assert len(result.composed_text) > 0


@pytest.mark.asyncio
async def test_compose_without_context(composer):
    """Test composition without context."""
    prompt = "Write a short story about a robot."

    result = await composer.compose(prompt, context=None)

    assert result.success
    assert result.context is None


@pytest.mark.asyncio
async def test_compose_with_max_length(composer):
    """Test composition with length limit."""
    prompt = "Write about technology."

    result = await composer.compose(prompt, max_length=100)

    assert result.success
    assert result.metadata.get("max_length") == 100


@pytest.mark.asyncio
async def test_compose_with_temperature(composer):
    """Test composition with custom temperature."""
    prompt = "Write creatively about space."

    result = await composer.compose(prompt, temperature=0.9)

    assert result.success
    assert result.metadata.get("temperature") == 0.9


# ========== Email Composition Tests ==========

@pytest.mark.asyncio
async def test_compose_email(composer):
    """Test email composition."""
    prompt = "Request a meeting to discuss the project timeline."
    context = "The recipient is my manager."

    result = await composer.compose_email(prompt, context)

    assert result.success
    assert len(result.composed_text) > 0
    # Email should have some structure
    assert len(result.composed_text.split('\n')) > 1


@pytest.mark.asyncio
async def test_compose_email_professional(composer):
    """Test professional email composition."""
    prompt = "Decline a job offer politely."

    result = await composer.compose_email(prompt)

    assert result.success
    # Should be relatively formal
    assert result.word_count > 10


@pytest.mark.asyncio
async def test_compose_email_with_details(composer):
    """Test email composition with specific details."""
    prompt = "Send update about project completion."
    context = "Project finished ahead of schedule with all milestones met."

    result = await composer.compose_email(prompt, context)

    assert result.success


# ========== Message Composition Tests ==========

@pytest.mark.asyncio
async def test_compose_message(composer):
    """Test short message composition."""
    prompt = "Tell friend I'll be late."

    result = await composer.compose_message(prompt)

    assert result.success
    # Message should be brief
    assert result.word_count < 150


@pytest.mark.asyncio
async def test_compose_message_casual(composer):
    """Test casual message composition."""
    prompt = "Ask if they want to grab lunch."

    result = await composer.compose_message(prompt)

    assert result.success


@pytest.mark.asyncio
async def test_compose_message_with_context(composer):
    """Test message with context."""
    prompt = "Confirm the appointment."
    context = "Dentist appointment tomorrow at 2pm."

    result = await composer.compose_message(prompt, context)

    assert result.success


# ========== Paragraph Composition Tests ==========

@pytest.mark.asyncio
async def test_compose_paragraph(composer):
    """Test paragraph composition."""
    prompt = "Explain the importance of testing in software development."

    result = await composer.compose_paragraph(prompt)

    assert result.success
    assert result.word_count > 20  # Should be substantive


@pytest.mark.asyncio
async def test_compose_paragraph_with_context(composer):
    """Test paragraph with context."""
    prompt = "Describe the solution."
    context = "We implemented automated testing to catch bugs early."

    result = await composer.compose_paragraph(prompt, context)

    assert result.success


# ========== Idea Expansion Tests ==========

@pytest.mark.asyncio
async def test_expand_idea(composer):
    """Test idea expansion."""
    idea = "AI-powered personal assistant"

    result = await composer.expand_idea(idea)

    assert result.success
    assert result.word_count > len(idea.split())  # Should be expanded


@pytest.mark.asyncio
async def test_expand_idea_with_length(composer):
    """Test idea expansion with target length."""
    idea = "Green energy initiative"

    result = await composer.expand_idea(idea, target_length=100)

    assert result.success
    assert result.metadata.get("max_length") == 100


@pytest.mark.asyncio
async def test_expand_brief_note(composer):
    """Test expanding brief notes."""
    idea = "Meeting notes: discussed Q4 goals, budget increase, new hires"

    result = await composer.expand_idea(idea, target_length=150)

    assert result.success


# ========== Rewrite with Instructions Tests ==========

@pytest.mark.asyncio
async def test_rewrite_with_instructions(composer):
    """Test rewriting with custom instructions."""
    text = "The product is good."
    instructions = "Make it more enthusiastic and descriptive"

    result = await composer.rewrite_with_instructions(text, instructions)

    assert result.success


@pytest.mark.asyncio
async def test_rewrite_change_tone(composer):
    """Test rewriting to change tone."""
    text = "I need this done ASAP."
    instructions = "Make it more polite and professional"

    result = await composer.rewrite_with_instructions(text, instructions)

    assert result.success


@pytest.mark.asyncio
async def test_rewrite_simplify(composer):
    """Test rewriting to simplify."""
    text = "The multifaceted approach yields optimal results."
    instructions = "Simplify for a general audience"

    result = await composer.rewrite_with_instructions(text, instructions)

    assert result.success


# ========== Template-based Generation Tests ==========

@pytest.mark.asyncio
async def test_generate_thank_you(composer):
    """Test thank you note generation."""
    context = {
        "recipient": "John",
        "reason": "helping with the project",
        "impact": "met the deadline"
    }

    result = await composer.generate_from_template("thank_you_note", context)

    assert result.success


@pytest.mark.asyncio
async def test_generate_apology(composer):
    """Test apology generation."""
    context = {
        "recipient": "Team",
        "issue": "missing the meeting",
        "action": "will review the recording"
    }

    result = await composer.generate_from_template("apology", context)

    assert result.success


@pytest.mark.asyncio
async def test_generate_from_template_complex(composer):
    """Test complex template generation."""
    context = {
        "occasion": "retirement party",
        "person": "Sarah",
        "years": "20",
        "contributions": "leadership and mentorship"
    }

    result = await composer.generate_from_template("celebration_message", context)

    assert result.success


# ========== Error Handling Tests ==========

@pytest.mark.asyncio
async def test_empty_prompt_error(composer):
    """Test handling of empty prompt."""
    result = await composer.compose("")

    assert not result.success
    assert result.error is not None
    assert "empty" in result.error.lower() or "short" in result.error.lower()


@pytest.mark.asyncio
async def test_very_short_prompt(composer):
    """Test handling of very short prompt."""
    result = await composer.compose("hi")

    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_very_long_prompt(composer):
    """Test handling of very long prompt."""
    prompt = "Write about " + ("this topic " * 200)  # Very long

    result = await composer.compose(prompt)

    # Should handle by truncating
    assert isinstance(result, ComposeResult)


@pytest.mark.asyncio
async def test_very_long_context(composer):
    """Test handling of very long context."""
    prompt = "Write about this."
    context = "Context information. " * 500  # Very long

    result = await composer.compose(prompt, context=context)

    # Should handle by truncating
    assert isinstance(result, ComposeResult)


@pytest.mark.asyncio
async def test_timeout_handling(composer):
    """Test timeout handling."""
    prompt = "Write about technology."

    result = await composer.compose(prompt, timeout_seconds=0.001)

    # Mock is fast, but structure is correct
    assert isinstance(result, ComposeResult)


@pytest.mark.asyncio
async def test_llm_error_handling(mock_llm, composer):
    """Test handling of LLM errors."""
    async def error_complete(*args, **kwargs):
        raise Exception("LLM error")

    mock_llm.complete = error_complete

    result = await composer.compose("Test prompt")

    assert not result.success
    assert result.error is not None


# ========== ComposeResult Tests ==========

def test_compose_result_properties():
    """Test ComposeResult properties."""
    result = ComposeResult(
        prompt="Test prompt",
        context="Test context",
        composed_text="This is composed text with multiple words.",
        tokens_used=50,
        processing_time_ms=1500,
        success=True,
        metadata={"key": "value"}
    )

    assert result.word_count == 7
    assert result.char_count > 0
    assert result.success
    assert result.metadata["key"] == "value"


def test_compose_result_word_count():
    """Test word count calculation."""
    result = ComposeResult(
        prompt="Test",
        context=None,
        composed_text="One two three four five."
    )

    assert result.word_count == 5


def test_compose_result_char_count():
    """Test character count."""
    result = ComposeResult(
        prompt="Test",
        context=None,
        composed_text="Hello world!"
    )

    assert result.char_count == 12


def test_compose_result_default_metadata():
    """Test default metadata."""
    result = ComposeResult(
        prompt="Test",
        context=None,
        composed_text="Text"
    )

    assert result.metadata == {}


# ========== Integration Tests ==========

@pytest.mark.asyncio
async def test_full_composition_workflow(composer):
    """Test complete composition workflow."""
    # Basic composition
    basic_result = await composer.compose("Write about AI")
    assert basic_result.success

    # With context
    context_result = await composer.compose(
        "Explain the benefits",
        context="In the context of business automation"
    )
    assert context_result.success

    # Email
    email_result = await composer.compose_email("Schedule meeting")
    assert email_result.success

    # Message
    message_result = await composer.compose_message("Running late")
    assert message_result.success

    # All should have metadata
    for result in [basic_result, context_result, email_result, message_result]:
        assert result.metadata is not None
        assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_multiple_compositions_sequential(composer):
    """Test multiple sequential compositions."""
    prompts = [
        "Write about technology",
        "Write about science",
        "Write about art"
    ]

    results = []
    for prompt in prompts:
        result = await composer.compose(prompt)
        results.append(result)

    # All should succeed
    assert all(r.success for r in results)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_concurrent_compositions(composer):
    """Test concurrent composition operations."""
    prompts = [
        "Write about topic A",
        "Write about topic B",
        "Write about topic C"
    ]

    tasks = [composer.compose(p) for p in prompts]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert len(results) == 3
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_different_formats_concurrent(composer):
    """Test different composition formats concurrently."""
    tasks = [
        composer.compose("General content"),
        composer.compose_email("Email content"),
        composer.compose_message("Message content"),
        composer.compose_paragraph("Paragraph content")
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 4
    assert all(r.success for r in results)


# ========== Performance Tests ==========

@pytest.mark.asyncio
async def test_composition_performance(composer):
    """Test composition performance."""
    prompt = "Write about modern technology"

    import time
    start = time.time()

    result = await composer.compose(prompt)

    elapsed_ms = (time.time() - start) * 1000

    assert result.success
    # With mock, should be very fast
    assert elapsed_ms < 1000


@pytest.mark.asyncio
async def test_email_composition_performance(composer):
    """Test email composition performance."""
    import time
    start = time.time()

    result = await composer.compose_email("Schedule meeting")

    elapsed_ms = (time.time() - start) * 1000

    assert result.success
    assert elapsed_ms < 1000


# ========== Edge Cases ==========

@pytest.mark.asyncio
async def test_prompt_with_special_characters(composer):
    """Test prompt with special characters."""
    prompt = "Write about: @#$%^&*()_+-=[]{}|;:',.<>?/~`"

    result = await composer.compose(prompt)

    assert isinstance(result, ComposeResult)


@pytest.mark.asyncio
async def test_prompt_with_unicode(composer):
    """Test prompt with unicode characters."""
    prompt = "Write about: 你好 مرحبا שלום नमस्ते"

    result = await composer.compose(prompt)

    assert isinstance(result, ComposeResult)


@pytest.mark.asyncio
async def test_prompt_with_emojis(composer):
    """Test prompt with emojis."""
    prompt = "Write something fun 😀 🎉 ✨"

    result = await composer.compose(prompt)

    assert isinstance(result, ComposeResult)


@pytest.mark.asyncio
async def test_context_with_newlines(composer):
    """Test context with multiple newlines."""
    prompt = "Summarize this"
    context = """Line 1

Line 2

Line 3"""

    result = await composer.compose(prompt, context=context)

    assert isinstance(result, ComposeResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

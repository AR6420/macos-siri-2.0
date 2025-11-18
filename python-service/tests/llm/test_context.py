"""
Tests for conversation context management.
"""

import pytest
from voice_assistant.llm import ConversationContext, Message, MessageRole


class TestConversationContext:
    """Test ConversationContext class."""

    def test_initialization(self):
        """Test context initialization."""
        context = ConversationContext(max_turns=5)
        assert len(context) == 0
        assert context.get_turn_count() == 0

    def test_initialization_with_system_message(self):
        """Test context initialization with system message."""
        system_msg = "You are a helpful assistant."
        context = ConversationContext(system_message=system_msg)

        assert len(context) == 1
        messages = context.get_messages()
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == system_msg

    def test_add_user_message(self):
        """Test adding user message."""
        context = ConversationContext()
        context.add_user_message("Hello")

        assert len(context) == 1
        messages = context.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"

    def test_add_assistant_message(self):
        """Test adding assistant message."""
        context = ConversationContext()
        context.add_assistant_message("Hi there!")

        assert len(context) == 1
        messages = context.get_messages()
        assert messages[0].role == MessageRole.ASSISTANT
        assert messages[0].content == "Hi there!"

    def test_add_exchange(self):
        """Test adding complete user-assistant exchange."""
        context = ConversationContext()
        context.add_exchange("What's the weather?", "It's sunny today.")

        assert len(context) == 2
        assert context.get_turn_count() == 1
        messages = context.get_messages()
        assert messages[0].role == MessageRole.USER
        assert messages[1].role == MessageRole.ASSISTANT

    def test_add_tool_result(self):
        """Test adding tool result message."""
        context = ConversationContext()
        context.add_tool_result(
            tool_call_id="call_123",
            content="Result data",
            name="web_search"
        )

        assert len(context) == 1
        messages = context.get_messages()
        assert messages[0].role == MessageRole.TOOL
        assert messages[0].tool_call_id == "call_123"
        assert messages[0].name == "web_search"

    def test_prune_by_turn_count(self):
        """Test pruning messages by turn count."""
        context = ConversationContext(max_turns=2)

        # Add 3 exchanges (6 messages)
        for i in range(3):
            context.add_exchange(f"Question {i}", f"Answer {i}")

        # Should keep only last 2 turns (4 messages)
        assert len(context) == 4
        assert context.get_turn_count() == 2

        messages = context.get_messages()
        assert messages[0].content == "Question 1"  # First message should be from turn 1

    def test_prune_preserves_system_message(self):
        """Test that pruning preserves system message."""
        context = ConversationContext(
            max_turns=2,
            system_message="You are helpful."
        )

        # Add 3 exchanges
        for i in range(3):
            context.add_exchange(f"Question {i}", f"Answer {i}")

        # Should have system message + 2 turns (5 messages total)
        assert len(context) == 5

        messages = context.get_messages()
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[0].content == "You are helpful."

    def test_clear(self):
        """Test clearing conversation."""
        context = ConversationContext(system_message="System")
        context.add_exchange("Hello", "Hi")
        context.add_exchange("How are you?", "I'm good")

        context.clear()

        # Should keep only system message
        assert len(context) == 1
        assert context.get_turn_count() == 0
        messages = context.get_messages()
        assert messages[0].role == MessageRole.SYSTEM

    def test_clear_without_system_message(self):
        """Test clearing conversation without system message."""
        context = ConversationContext()
        context.add_exchange("Hello", "Hi")

        context.clear()

        assert len(context) == 0
        assert context.get_turn_count() == 0

    def test_estimated_tokens(self):
        """Test token estimation."""
        context = ConversationContext()
        context.add_user_message("a" * 100)  # ~25 tokens

        estimated = context.get_estimated_tokens()
        assert estimated == 25  # 100 chars / 4

    def test_metadata(self):
        """Test metadata storage."""
        context = ConversationContext()
        context.set_metadata("user_id", "123")
        context.set_metadata("session", "abc")

        assert context.get_metadata("user_id") == "123"
        assert context.get_metadata("session") == "abc"
        assert context.get_metadata("missing", "default") == "default"

    def test_repr(self):
        """Test string representation."""
        context = ConversationContext()
        context.add_exchange("Hello", "Hi")

        repr_str = repr(context)
        assert "ConversationContext" in repr_str
        assert "turns=1" in repr_str
        assert "messages=2" in repr_str

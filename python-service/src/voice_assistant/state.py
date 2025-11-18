"""
Conversation State Management

Manages conversation history, context window, and session state.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .llm import Message, MessageRole

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn (user + assistant)"""
    user_message: str
    assistant_message: str
    timestamp: float
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationState:
    """
    Manage conversation history and context.

    Features:
    - Message history with configurable max turns
    - Automatic pruning of old messages
    - Context window token management
    - Session timeout handling
    - Metadata tracking for analytics
    """

    def __init__(
        self,
        max_turns: int = 10,
        max_context_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        session_timeout_minutes: int = 30,
    ):
        """
        Initialize conversation state.

        Args:
            max_turns: Maximum number of turns to keep in history
            max_context_tokens: Maximum tokens to keep in context (approximate)
            system_prompt: System prompt for the conversation
            session_timeout_minutes: Minutes of inactivity before session reset
        """
        self.max_turns = max_turns
        self.max_context_tokens = max_context_tokens
        self.system_prompt = system_prompt or "You are a helpful AI voice assistant."
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

        self._messages: List[Message] = []
        self._turns: List[ConversationTurn] = []
        self._session_start: float = time.time()
        self._last_interaction: float = time.time()
        self._metadata: Dict[str, Any] = {}

        # Add system prompt as first message
        self._messages.append(
            Message(role=MessageRole.SYSTEM, content=self.system_prompt)
        )

        logger.info(
            f"Conversation state initialized: max_turns={max_turns}, "
            f"max_tokens={max_context_tokens}, timeout={session_timeout_minutes}m"
        )

    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the conversation.

        Args:
            content: User's message content
        """
        self._check_session_timeout()
        self._messages.append(Message(role=MessageRole.USER, content=content))
        self._last_interaction = time.time()
        logger.debug(f"Added user message: {content[:100]}")

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add an assistant message to the conversation.

        Args:
            content: Assistant's response content
            tool_calls: Optional list of tool calls made
        """
        self._messages.append(Message(role=MessageRole.ASSISTANT, content=content))
        self._last_interaction = time.time()
        logger.debug(f"Added assistant message: {content[:100]}")

        # Track this turn if we have a previous user message
        if len(self._messages) >= 2 and self._messages[-2].role == MessageRole.USER:
            turn = ConversationTurn(
                user_message=self._messages[-2].content,
                assistant_message=content,
                timestamp=time.time(),
                tool_calls=tool_calls or [],
            )
            self._turns.append(turn)

        # Prune if needed
        self._prune_history()

    def add_tool_message(
        self,
        tool_name: str,
        tool_result: str,
        tool_call_id: Optional[str] = None
    ) -> None:
        """
        Add a tool result message to the conversation.

        Args:
            tool_name: Name of the tool that was called
            tool_result: Result from the tool execution
            tool_call_id: Optional tool call ID for tracking
        """
        self._messages.append(
            Message(
                role=MessageRole.TOOL,
                content=tool_result,
                name=tool_name,
                tool_call_id=tool_call_id,
            )
        )
        logger.debug(f"Added tool message: {tool_name} -> {tool_result[:100]}")

    def add_exchange(
        self,
        user_msg: str,
        assistant_msg: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add a complete user-assistant exchange.

        This is a convenience method for adding both messages at once.

        Args:
            user_msg: User's message
            assistant_msg: Assistant's response
            tool_calls: Optional tool calls made during this exchange
        """
        self.add_user_message(user_msg)
        self.add_assistant_message(assistant_msg, tool_calls)

    def get_messages(self) -> List[Message]:
        """
        Get all messages for LLM context.

        Returns:
            Copy of message list
        """
        self._check_session_timeout()
        return self._messages.copy()

    def get_recent_turns(self, n: int = 5) -> List[ConversationTurn]:
        """
        Get recent conversation turns.

        Args:
            n: Number of recent turns to retrieve

        Returns:
            List of recent turns
        """
        return self._turns[-n:] if len(self._turns) > n else self._turns.copy()

    def clear(self) -> None:
        """Clear all conversation history (except system prompt)"""
        logger.info("Clearing conversation history")
        self._messages = [
            Message(role=MessageRole.SYSTEM, content=self.system_prompt)
        ]
        self._turns.clear()
        self._session_start = time.time()
        self._last_interaction = time.time()
        self._metadata.clear()

    def reset_session(self) -> None:
        """Reset the session (same as clear but logs differently)"""
        logger.info("Resetting conversation session")
        self.clear()

    def _prune_history(self) -> None:
        """Prune old messages to stay within limits"""
        # Keep system prompt + last N turns (2 messages per turn)
        max_messages = 1 + (self.max_turns * 2)

        if len(self._messages) > max_messages:
            # Keep system prompt and recent messages
            system_messages = [m for m in self._messages if m.role == MessageRole.SYSTEM]
            other_messages = [m for m in self._messages if m.role != MessageRole.SYSTEM]

            # Keep most recent messages
            pruned_messages = system_messages + other_messages[-max_messages + 1:]
            removed_count = len(self._messages) - len(pruned_messages)

            self._messages = pruned_messages
            logger.debug(f"Pruned {removed_count} messages from history")

        # Also prune turns
        if len(self._turns) > self.max_turns:
            removed_count = len(self._turns) - self.max_turns
            self._turns = self._turns[-self.max_turns:]
            logger.debug(f"Pruned {removed_count} turns from history")

    def _check_session_timeout(self) -> None:
        """Check if session has timed out and reset if needed"""
        if time.time() - self._last_interaction > self.session_timeout.total_seconds():
            logger.info("Session timeout reached, resetting conversation")
            self.reset_session()

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.

        Returns:
            Dictionary with session statistics
        """
        return {
            "session_duration_seconds": time.time() - self._session_start,
            "turns_count": len(self._turns),
            "messages_count": len(self._messages),
            "last_interaction": datetime.fromtimestamp(self._last_interaction).isoformat(),
            "session_start": datetime.fromtimestamp(self._session_start).isoformat(),
        }

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the session"""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the session"""
        return self._metadata.get(key, default)

    def get_context_summary(self) -> str:
        """
        Get a summary of the conversation context.

        Returns:
            Human-readable summary string
        """
        if not self._turns:
            return "No conversation history"

        recent_turns = self.get_recent_turns(3)
        summary_parts = []

        for i, turn in enumerate(recent_turns, 1):
            summary_parts.append(
                f"Turn {i}:\n"
                f"  User: {turn.user_message[:100]}\n"
                f"  Assistant: {turn.assistant_message[:100]}"
            )

        return "\n".join(summary_parts)

    def __repr__(self) -> str:
        return (
            f"ConversationState(turns={len(self._turns)}, "
            f"messages={len(self._messages)}, "
            f"duration={time.time() - self._session_start:.1f}s)"
        )

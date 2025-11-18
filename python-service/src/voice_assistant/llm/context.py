"""
Conversation context management for maintaining message history.
"""

from typing import List, Dict, Any, Optional
from .base import Message, MessageRole


class ConversationContext:
    """
    Manages conversation history and context.

    Keeps track of message history with automatic pruning to stay
    within token limits and turn count limits.
    """

    def __init__(
        self,
        max_turns: int = 10,
        max_tokens: Optional[int] = 4096,
        system_message: Optional[str] = None
    ):
        """
        Initialize conversation context.

        Args:
            max_turns: Maximum number of user-assistant turn pairs to keep
            max_tokens: Maximum estimated tokens to keep (approximate)
            system_message: Optional system message to prepend
        """
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {}

        if system_message:
            self.messages.append(Message(
                role=MessageRole.SYSTEM,
                content=system_message
            ))

    def add_user_message(self, content: str):
        """Add a user message to the conversation."""
        self.messages.append(Message(
            role=MessageRole.USER,
            content=content
        ))
        self._prune_history()

    def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation."""
        self.messages.append(Message(
            role=MessageRole.ASSISTANT,
            content=content
        ))
        self._prune_history()

    def add_tool_result(self, tool_call_id: str, content: str, name: str):
        """Add a tool result message to the conversation."""
        self.messages.append(Message(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name
        ))
        self._prune_history()

    def add_exchange(self, user_content: str, assistant_content: str):
        """
        Add a complete user-assistant exchange.

        Args:
            user_content: User's message
            assistant_content: Assistant's response
        """
        self.add_user_message(user_content)
        self.add_assistant_message(assistant_content)

    def get_messages(self) -> List[Message]:
        """
        Get all messages in the conversation.

        Returns:
            Copy of the message list
        """
        return self.messages.copy()

    def clear(self):
        """Clear all messages (except system message if present)."""
        system_messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        self.messages = system_messages
        self.metadata.clear()

    def _prune_history(self):
        """Prune old messages to stay within limits."""
        # Separate system messages from conversation
        system_messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        conversation_messages = [m for m in self.messages if m.role != MessageRole.SYSTEM]

        # Count turns (user-assistant pairs)
        # Keep only the most recent max_turns exchanges
        if len(conversation_messages) > self.max_turns * 2:
            # Keep the most recent messages
            conversation_messages = conversation_messages[-(self.max_turns * 2):]

        # Estimate token count (rough approximation: 4 chars per token)
        if self.max_tokens:
            total_chars = sum(len(m.content) for m in conversation_messages)
            estimated_tokens = total_chars // 4

            while estimated_tokens > self.max_tokens and len(conversation_messages) > 2:
                # Remove oldest non-system message
                conversation_messages.pop(0)
                total_chars = sum(len(m.content) for m in conversation_messages)
                estimated_tokens = total_chars // 4

        # Reconstruct message list
        self.messages = system_messages + conversation_messages

    def get_turn_count(self) -> int:
        """Get the number of conversation turns (user-assistant pairs)."""
        conversation_messages = [m for m in self.messages if m.role != MessageRole.SYSTEM]
        return len(conversation_messages) // 2

    def get_estimated_tokens(self) -> int:
        """
        Get estimated token count for all messages.

        Returns approximate token count using 4 chars per token heuristic.
        """
        total_chars = sum(len(m.content) for m in self.messages)
        return total_chars // 4

    def set_metadata(self, key: str, value: Any):
        """Set metadata for the conversation."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the conversation."""
        return self.metadata.get(key, default)

    def __len__(self) -> int:
        """Return number of messages in context."""
        return len(self.messages)

    def __repr__(self) -> str:
        return (
            f"ConversationContext(turns={self.get_turn_count()}, "
            f"messages={len(self.messages)}, "
            f"tokens≈{self.get_estimated_tokens()})"
        )

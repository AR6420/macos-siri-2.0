"""
Base abstractions for LLM providers.

Defines the interface that all LLM providers must implement,
along with common data structures for messages, completions, and tool calls.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, AsyncIterator
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """Represents a message in the conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "role": self.role.value,
            "content": self.content
        }
        if self.name:
            result["name"] = self.name
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class ToolDefinition:
    """Defines a tool/function that the LLM can call."""
    name: str
    description: str
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class ToolCall:
    """Represents a tool call made by the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Create ToolCall from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            arguments=data.get("arguments", {})
        )


@dataclass
class CompletionResult:
    """Result from an LLM completion request."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    tool_calls: Optional[List[ToolCall]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        """Check if result contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must inherit from this class and implement
    the required methods for completion and streaming.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.model = config.get("model", "unknown")
        self.timeout = config.get("timeout", 60)
        self.max_tokens = config.get("max_tokens", 1024)
        self.temperature = config.get("temperature", 0.7)

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResult:
        """
        Generate a completion from messages.

        Args:
            messages: List of conversation messages
            tools: Optional list of tools the LLM can call
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Provider-specific additional parameters

        Returns:
            CompletionResult with the LLM's response

        Raises:
            LLMError: On API or processing errors
        """
        pass

    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens as they're generated.

        Args:
            messages: List of conversation messages
            tools: Optional list of tools the LLM can call
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Provider-specific additional parameters

        Yields:
            String tokens as they're generated

        Raises:
            LLMError: On API or processing errors
        """
        pass

    async def close(self):
        """
        Clean up provider resources.

        Override this method if your provider needs cleanup.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Error connecting to LLM service."""
    pass


class LLMTimeoutError(LLMError):
    """LLM request timed out."""
    pass


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded."""
    pass


class LLMInvalidRequestError(LLMError):
    """Invalid request to LLM."""
    pass

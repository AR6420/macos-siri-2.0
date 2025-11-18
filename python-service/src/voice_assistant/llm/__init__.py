"""
LLM module for flexible multi-provider AI inference.

Provides a unified interface for working with different LLM providers
including local models and cloud APIs.

Example:
    >>> from voice_assistant.llm import ProviderFactory, Message, MessageRole
    >>>
    >>> # Create provider from config
    >>> config = {
    ...     "llm": {
    ...         "backend": "local_gpt_oss",
    ...         "local_gpt_oss": {
    ...             "base_url": "http://localhost:8080",
    ...             "model": "gpt-oss:120b",
    ...             "timeout": 120
    ...         }
    ...     }
    ... }
    >>> provider = ProviderFactory.create_from_config(config)
    >>>
    >>> # Create messages
    >>> messages = [
    ...     Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
    ...     Message(role=MessageRole.USER, content="What is the weather like?")
    ... ]
    >>>
    >>> # Get completion
    >>> result = await provider.complete(messages)
    >>> print(result.content)
"""

from .base import (
    LLMProvider,
    Message,
    MessageRole,
    CompletionResult,
    ToolDefinition,
    ToolCall,
    LLMError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMInvalidRequestError,
)

from .context import ConversationContext

from .factory import ProviderFactory

from .providers import (
    LocalGPTOSSProvider,
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
)

__all__ = [
    # Base classes and data models
    "LLMProvider",
    "Message",
    "MessageRole",
    "CompletionResult",
    "ToolDefinition",
    "ToolCall",

    # Exceptions
    "LLMError",
    "LLMConnectionError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMInvalidRequestError",

    # Context management
    "ConversationContext",

    # Factory
    "ProviderFactory",

    # Providers
    "LocalGPTOSSProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OpenRouterProvider",
]

__version__ = "1.0.0"

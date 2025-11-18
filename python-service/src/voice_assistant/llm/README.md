# LLM Module - Flexible Multi-Provider AI Inference

**Agent 4 Deliverable** - Complete LLM abstraction layer for Voice Assistant

## Overview

The LLM module provides a unified interface for working with different language model providers, supporting both local on-device inference and cloud APIs. This enables the Voice Assistant to work with maximum privacy (local models) or leverage powerful cloud models when needed.

## Architecture

```
llm/
├── base.py              # Abstract base class and data models
├── context.py           # Conversation context management
├── factory.py           # Provider factory for dynamic instantiation
├── providers/
│   ├── local_gpt_oss.py    # Local gpt-oss:120b via MLX
│   ├── openai.py           # OpenAI API (GPT-4, GPT-4o)
│   ├── anthropic.py        # Anthropic API (Claude Sonnet, Opus)
│   └── openrouter.py       # OpenRouter (multi-model access)
└── __init__.py
```

## Key Features

- **Multi-Provider Support**: Local MLX, OpenAI, Anthropic, OpenRouter
- **Unified Interface**: Same API across all providers
- **Async/Await**: Full async support for non-blocking operations
- **Streaming**: Progressive response streaming where supported
- **Tool Calling**: Function calling support for compatible models
- **Retry Logic**: Automatic retries with exponential backoff
- **Context Management**: Conversation history with automatic pruning
- **Error Handling**: Comprehensive error types and recovery

## Quick Start

### Basic Usage

```python
from voice_assistant.llm import ProviderFactory, Message, MessageRole

# Load configuration
config = {
    "llm": {
        "backend": "local_gpt_oss",
        "local_gpt_oss": {
            "base_url": "http://localhost:8080",
            "model": "gpt-oss:120b",
            "timeout": 120
        }
    }
}

# Create provider
provider = ProviderFactory.create_from_config(config)

# Create messages
messages = [
    Message(role=MessageRole.SYSTEM, content="You are helpful."),
    Message(role=MessageRole.USER, content="What is 2+2?"),
]

# Get completion
result = await provider.complete(messages)
print(result.content)  # "2+2 equals 4."

# Clean up
await provider.close()
```

### Streaming Responses

```python
async for chunk in provider.stream_complete(messages):
    print(chunk, end="", flush=True)
```

### Tool Calling

```python
from voice_assistant.llm import ToolDefinition

# Define tools
tools = [
    ToolDefinition(
        name="web_search",
        description="Search the web",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            }
        }
    )
]

# Request with tools
result = await provider.complete(messages, tools=tools)

if result.has_tool_calls:
    for tool_call in result.tool_calls:
        print(f"Tool: {tool_call.name}")
        print(f"Args: {tool_call.arguments}")
```

### Conversation Context

```python
from voice_assistant.llm import ConversationContext

# Create context
context = ConversationContext(
    max_turns=10,
    system_message="You are a helpful assistant."
)

# Multi-turn conversation
context.add_user_message("My name is Alice")
result = await provider.complete(context.get_messages())
context.add_assistant_message(result.content)

context.add_user_message("What is my name?")
result = await provider.complete(context.get_messages())
context.add_assistant_message(result.content)
# Response: "Your name is Alice."
```

## Interface for Orchestrator (Agent 6)

### Complete Pipeline Integration

```python
from voice_assistant.llm import (
    ProviderFactory,
    ConversationContext,
    Message,
    MessageRole,
    LLMError,
)

class VoiceAssistantOrchestrator:
    def __init__(self, config):
        # Create LLM provider from config
        self.llm = ProviderFactory.create_from_config(config)

        # Create conversation context
        system_prompt = config.get("conversation", {}).get("system_prompt", "")
        self.context = ConversationContext(
            max_turns=config.get("conversation", {}).get("max_history_turns", 10),
            system_message=system_prompt
        )

    async def process_user_input(self, user_text: str, tools=None):
        """Process user input through LLM pipeline."""
        try:
            # Add user message to context
            self.context.add_user_message(user_text)

            # Get LLM response
            result = await self.llm.complete(
                self.context.get_messages(),
                tools=tools,
                temperature=0.7
            )

            # Handle tool calls if present
            if result.has_tool_calls:
                # Execute tools (via MCP client)
                for tool_call in result.tool_calls:
                    tool_result = await self.execute_tool(
                        tool_call.name,
                        tool_call.arguments
                    )

                    # Add tool result to context
                    self.context.add_tool_result(
                        tool_call_id=tool_call.id,
                        content=str(tool_result),
                        name=tool_call.name
                    )

                # Get final response with tool results
                result = await self.llm.complete(
                    self.context.get_messages(),
                    tools=tools
                )

            # Add assistant response to context
            self.context.add_assistant_message(result.content)

            return result.content

        except LLMError as e:
            # Handle LLM errors
            return f"Error: {e}"

    async def execute_tool(self, name: str, arguments: dict):
        """Execute tool via MCP client."""
        # Implemented by MCP integration
        pass

    async def cleanup(self):
        """Clean up resources."""
        await self.llm.close()
```

### Streaming Integration

```python
async def process_user_input_streaming(self, user_text: str):
    """Process user input with streaming response."""
    self.context.add_user_message(user_text)

    # Collect response
    response_chunks = []

    async for chunk in self.llm.stream_complete(
        self.context.get_messages()
    ):
        response_chunks.append(chunk)
        # Optionally: Stream to TTS here
        await self.tts.speak_partial(chunk)

    # Complete response
    full_response = "".join(response_chunks)
    self.context.add_assistant_message(full_response)

    return full_response
```

## Data Models

### Message

```python
@dataclass
class Message:
    role: MessageRole          # SYSTEM | USER | ASSISTANT | TOOL
    content: str               # Message content
    name: Optional[str]        # Tool name (for tool messages)
    tool_call_id: Optional[str]  # Tool call ID (for tool messages)
```

### CompletionResult

```python
@dataclass
class CompletionResult:
    content: str               # LLM response text
    model: str                 # Model name used
    tokens_used: int           # Total tokens consumed
    finish_reason: str         # "stop" | "length" | "tool_calls"
    tool_calls: Optional[List[ToolCall]]  # Tool calls if any
    metadata: Dict[str, Any]   # Provider-specific metadata

    @property
    def has_tool_calls(self) -> bool:
        """Check if result contains tool calls."""
```

### ToolCall

```python
@dataclass
class ToolCall:
    id: str                    # Unique tool call ID
    name: str                  # Tool/function name
    arguments: Dict[str, Any]  # Tool arguments
```

### ToolDefinition

```python
@dataclass
class ToolDefinition:
    name: str                  # Tool name
    description: str           # Tool description (for LLM)
    parameters: Dict[str, Any] # JSON Schema for parameters
```

## Supported Providers

### 1. LocalGPTOSSProvider

**For**: Privacy-first on-device inference

**Configuration**:
```yaml
llm:
  backend: local_gpt_oss
  local_gpt_oss:
    base_url: http://localhost:8080
    model: gpt-oss:120b
    timeout: 120
    max_tokens: 1024
    temperature: 0.7
```

**Features**:
- On-device processing (M3 Ultra)
- No API costs
- Full privacy
- MLX acceleration
- Streaming support
- Tool calling support

**Requirements**:
- MLX server running locally
- ~75GB RAM for 120B model

### 2. OpenAIProvider

**For**: Cloud-based inference with GPT-4/GPT-4o

**Configuration**:
```yaml
llm:
  backend: openai
  openai:
    api_key_env: OPENAI_API_KEY
    model: gpt-4o
    timeout: 60
    max_tokens: 1024
    temperature: 0.7
```

**Features**:
- Latest OpenAI models
- Excellent tool calling
- Fast response times
- Streaming support

**Requirements**:
- OPENAI_API_KEY environment variable
- Internet connection

### 3. AnthropicProvider

**For**: Claude models (Sonnet, Opus)

**Configuration**:
```yaml
llm:
  backend: anthropic
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
    model: claude-sonnet-4-20250514
    timeout: 60
    max_tokens: 1024
    temperature: 0.7
```

**Features**:
- Claude 4 Sonnet/Opus models
- Advanced reasoning
- Large context windows
- Tool calling support
- Streaming support

**Requirements**:
- ANTHROPIC_API_KEY environment variable
- Internet connection

### 4. OpenRouterProvider

**For**: Access to many models via unified API

**Configuration**:
```yaml
llm:
  backend: openrouter
  openrouter:
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1
    model: openai/gpt-4o
    timeout: 60
```

**Features**:
- Access to 100+ models
- Flexible provider switching
- Cost optimization
- Streaming support

**Requirements**:
- OPENROUTER_API_KEY environment variable
- Internet connection

## Error Handling

### Error Types

```python
from voice_assistant.llm import (
    LLMError,              # Base exception
    LLMConnectionError,    # Connection failed
    LLMTimeoutError,       # Request timed out
    LLMRateLimitError,     # Rate limit exceeded
    LLMInvalidRequestError,  # Invalid request
)

try:
    result = await provider.complete(messages)
except LLMConnectionError:
    # Retry or fallback to cloud API
    pass
except LLMTimeoutError:
    # Reduce max_tokens or increase timeout
    pass
except LLMRateLimitError:
    # Wait and retry or switch provider
    pass
except LLMError as e:
    # Generic error handling
    pass
```

### Automatic Retries

All providers have automatic retry logic with exponential backoff:
- 3 attempts maximum
- Exponential backoff (2s, 4s, 8s)
- Only retries transient errors

## Performance Characteristics

| Provider | Avg Latency | Tokens/sec | Privacy | Cost |
|----------|-------------|------------|---------|------|
| Local GPT-OSS | 2-3s | 40-60 | Full | Free |
| OpenAI GPT-4o | 3-5s | 80-100 | Cloud | $$ |
| Anthropic Claude | 3-5s | 70-90 | Cloud | $$ |
| OpenRouter | Varies | Varies | Cloud | $ |

## Testing

Run tests:
```bash
cd python-service
pytest tests/llm/ -v
```

Test coverage:
```bash
pytest tests/llm/ --cov=voice_assistant.llm --cov-report=html
```

## Advanced Usage

### Custom Provider

```python
from voice_assistant.llm import LLMProvider, ProviderFactory

class CustomProvider(LLMProvider):
    async def complete(self, messages, **kwargs):
        # Your implementation
        pass

    async def stream_complete(self, messages, **kwargs):
        # Your implementation
        pass

# Register custom provider
ProviderFactory.register_provider("custom", CustomProvider)

# Use it
config = {
    "llm": {
        "backend": "custom",
        "custom": {"model": "my-model"}
    }
}
provider = ProviderFactory.create_from_config(config)
```

### Dynamic Provider Switching

```python
class AdaptiveOrchestrator:
    """Switch between local and cloud based on availability."""

    async def get_provider(self):
        try:
            # Try local first
            provider = ProviderFactory.create("local_gpt_oss", self.config)
            await provider.complete([test_message])
            return provider
        except LLMConnectionError:
            # Fallback to cloud
            return ProviderFactory.create("anthropic", self.config)
```

## Integration Checklist for Agent 6 (Orchestrator)

- [ ] Import ProviderFactory and create provider from config
- [ ] Create ConversationContext with system prompt
- [ ] Add user messages to context after STT
- [ ] Call provider.complete() with context messages
- [ ] Handle tool calls if result.has_tool_calls
- [ ] Execute tools via MCP client
- [ ] Add tool results back to context
- [ ] Get final response after tool execution
- [ ] Add assistant response to context
- [ ] Pass response text to TTS
- [ ] Handle LLM errors gracefully
- [ ] Close provider on shutdown

## Support

For issues or questions about the LLM module:
1. Check examples in `examples/llm_example.py`
2. Review test cases in `tests/llm/`
3. See CLAUDE.md for architecture details

## License

Apache 2.0 - See LICENSE file

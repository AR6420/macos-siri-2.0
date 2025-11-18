# LLM Module - Quick Reference

## 30-Second Start

```python
from voice_assistant.llm import ProviderFactory, Message, MessageRole

# 1. Create provider
config = {"llm": {"backend": "local_gpt_oss", "local_gpt_oss": {"base_url": "http://localhost:8080", "model": "gpt-oss:120b"}}}
provider = ProviderFactory.create_from_config(config)

# 2. Create messages
messages = [Message(role=MessageRole.USER, content="What is 2+2?")]

# 3. Get response
result = await provider.complete(messages)
print(result.content)  # "2+2 equals 4."

# 4. Cleanup
await provider.close()
```

## Common Patterns

### Load from config.yaml
```python
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)
provider = ProviderFactory.create_from_config(config)
```

### Multi-turn conversation
```python
from voice_assistant.llm import ConversationContext

context = ConversationContext(system_message="You are helpful.")
context.add_user_message("My name is Alice")
result = await provider.complete(context.get_messages())
context.add_assistant_message(result.content)

context.add_user_message("What's my name?")
result = await provider.complete(context.get_messages())
# Response: "Your name is Alice."
```

### Streaming
```python
async for chunk in provider.stream_complete(messages):
    print(chunk, end="", flush=True)
```

### Tool calling
```python
from voice_assistant.llm import ToolDefinition

tools = [ToolDefinition(name="search", description="Search web", parameters={...})]
result = await provider.complete(messages, tools=tools)

if result.has_tool_calls:
    for call in result.tool_calls:
        print(f"{call.name}({call.arguments})")
```

### Error handling
```python
from voice_assistant.llm import LLMError, LLMConnectionError

try:
    result = await provider.complete(messages)
except LLMConnectionError:
    # Retry or fallback
    pass
except LLMError as e:
    print(f"Error: {e}")
```

## Supported Backends

| Backend | Config Key | Requires |
|---------|------------|----------|
| Local GPT-OSS | `local_gpt_oss` | MLX server |
| OpenAI | `openai` | OPENAI_API_KEY |
| Anthropic | `anthropic` | ANTHROPIC_API_KEY |
| OpenRouter | `openrouter` | OPENROUTER_API_KEY |

## Key Classes

```python
# Data models
Message(role, content, name?, tool_call_id?)
CompletionResult(content, model, tokens_used, finish_reason, tool_calls?, metadata)
ToolCall(id, name, arguments)
ToolDefinition(name, description, parameters)

# Context
ConversationContext(max_turns=10, system_message="")
  .add_user_message(text)
  .add_assistant_message(text)
  .add_tool_result(id, content, name)
  .get_messages() -> List[Message]

# Factory
ProviderFactory
  .create_from_config(config) -> Provider
  .create(backend, config) -> Provider
  .list_supported_backends() -> List[str]

# Provider (all providers)
  .complete(messages, tools?, temp?, max_tokens?) -> CompletionResult
  .stream_complete(messages, ...) -> AsyncIterator[str]
  .close()
```

## Configuration Template

```yaml
llm:
  backend: local_gpt_oss  # or openai, anthropic, openrouter

  local_gpt_oss:
    base_url: http://localhost:8080
    model: gpt-oss:120b
    timeout: 120
    max_tokens: 1024
    temperature: 0.7

  openai:
    api_key_env: OPENAI_API_KEY
    model: gpt-4o
    timeout: 60

  anthropic:
    api_key_env: ANTHROPIC_API_KEY
    model: claude-sonnet-4-20250514
    timeout: 60

  openrouter:
    api_key_env: OPENROUTER_API_KEY
    model: openai/gpt-4o
    timeout: 60
```

## Orchestrator Integration

```python
class VoiceAssistant:
    def __init__(self, config):
        # Setup
        self.llm = ProviderFactory.create_from_config(config)
        self.context = ConversationContext(
            max_turns=10,
            system_message=config["conversation"]["system_prompt"]
        )

    async def process(self, user_text, mcp_tools):
        # Add user input
        self.context.add_user_message(user_text)

        # Get LLM response
        result = await self.llm.complete(
            self.context.get_messages(),
            tools=mcp_tools
        )

        # Handle tool calls
        if result.has_tool_calls:
            for call in result.tool_calls:
                tool_result = await self.execute_tool(call)
                self.context.add_tool_result(call.id, tool_result, call.name)
            result = await self.llm.complete(self.context.get_messages(), tools=mcp_tools)

        # Add response
        self.context.add_assistant_message(result.content)
        return result.content

    async def cleanup(self):
        await self.llm.close()
```

## Testing

```bash
# Run all tests
pytest tests/llm/ -v

# With coverage
pytest tests/llm/ --cov=voice_assistant.llm --cov-report=html

# Specific test file
pytest tests/llm/test_context.py -v

# Run example
cd python-service
PYTHONPATH=src python3 examples/llm_example.py
```

## Common Issues

**Import Error**: Make sure dependencies installed: `poetry install`

**Connection Error (local)**: Ensure MLX server running on localhost:8080

**API Key Error**: Set environment variable before running:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENROUTER_API_KEY="sk-or-..."
```

**Rate Limit**: Automatic retry with backoff (3 attempts)

## Performance Tips

1. Use local provider for privacy and no API costs
2. Use streaming for better UX during long responses
3. Limit `max_turns` in context to reduce token usage
4. Set appropriate `timeout` based on model/provider
5. Use `temperature=0.7` for balanced creativity/consistency

## More Info

- Full docs: `README.md` in this directory
- Examples: `python-service/examples/llm_example.py`
- Tests: `python-service/tests/llm/`
- Architecture: `/CLAUDE.md` (project root)

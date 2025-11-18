# LLM Module Architecture

## Module Overview

```
voice_assistant.llm/
│
├── Interface Layer (base.py)
│   ├── LLMProvider (abstract)
│   ├── Message, CompletionResult, ToolCall, ToolDefinition
│   └── Exception hierarchy
│
├── Context Management (context.py)
│   └── ConversationContext
│       ├── Message history management
│       ├── Auto-pruning (turns & tokens)
│       └── Metadata storage
│
├── Provider Factory (factory.py)
│   └── ProviderFactory
│       ├── Dynamic provider instantiation
│       ├── Config validation
│       └── Provider registry
│
└── Providers (providers/)
    ├── LocalGPTOSSProvider (MLX)
    ├── OpenAIProvider (GPT-4/4o)
    ├── AnthropicProvider (Claude)
    └── OpenRouterProvider (Multi-model)
```

## Data Flow

```
User Input (from STT)
        ↓
  ConversationContext
        ↓ (add_user_message)
    Message List
        ↓
  [LLMProvider].complete()
        ↓
  CompletionResult
        ↓
   Tool Calls? ──Yes→ Execute via MCP → Add results → Re-call LLM
        ↓ No
  Assistant Response
        ↓ (add_assistant_message)
  ConversationContext
        ↓
  To TTS
```

## Integration with Voice Assistant Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE ASSISTANT PIPELINE                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Wake Word   │ →   │   Whisper    │ →   │     LLM      │
│  Detection   │     │     STT      │     │   (Agent 4)  │
│  (Agent 2)   │     │  (Agent 3)   │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ↓
                                        ┌─────────────────┐
                    ┌──────────────────→│  MCP Tools      │
                    │                   │  (Agent 5)      │
                    │                   └─────────────────┘
                    │                           │
                    └───────────────────────────┘
                           Tool Execution
                                  │
                                  ↓
                         ┌────────────────┐
                         │      TTS       │ → Response
                         │  (macOS API)   │
                         └────────────────┘
```

## Class Diagram

```
┌─────────────────────────────────────────┐
│          LLMProvider (ABC)              │
├─────────────────────────────────────────┤
│ + config: Dict                          │
│ + model: str                            │
│ + timeout: int                          │
├─────────────────────────────────────────┤
│ + complete() → CompletionResult         │
│ + stream_complete() → AsyncIterator     │
│ + close()                               │
└─────────────────────────────────────────┘
                    △
                    │ inherits
        ┌───────────┴───────────┬─────────────────┬────────────────┐
        │                       │                 │                │
┌───────────────┐  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐
│ LocalGPTOSS   │  │   OpenAI       │  │   Anthropic     │  │ OpenRouter   │
│   Provider    │  │   Provider     │  │    Provider     │  │   Provider   │
├───────────────┤  ├────────────────┤  ├─────────────────┤  ├──────────────┤
│ MLX server    │  │ OpenAI API     │  │ Claude API      │  │ Multi-model  │
│ localhost     │  │ GPT-4/4o       │  │ Sonnet/Opus     │  │ API gateway  │
└───────────────┘  └────────────────┘  └─────────────────┘  └──────────────┘


┌─────────────────────────────────────────┐
│      ConversationContext                │
├─────────────────────────────────────────┤
│ - messages: List[Message]               │
│ - max_turns: int                        │
│ - max_tokens: int                       │
├─────────────────────────────────────────┤
│ + add_user_message(text)                │
│ + add_assistant_message(text)           │
│ + add_tool_result(id, content, name)    │
│ + get_messages() → List[Message]        │
│ + clear()                               │
└─────────────────────────────────────────┘


┌─────────────────────────────────────────┐
│        ProviderFactory                  │
├─────────────────────────────────────────┤
│ - _PROVIDERS: Dict                      │
├─────────────────────────────────────────┤
│ + create(backend, config) → Provider    │
│ + create_from_config(config)            │
│ + list_supported_backends()             │
│ + register_provider(name, class)        │
└─────────────────────────────────────────┘
```

## Sequence Diagram: Complete Request Flow

```
User → Orchestrator → LLM → Provider → API → Provider → LLM → Orchestrator

1. User speaks "Open Safari"
2. STT transcribes → "Open Safari"
3. Orchestrator.process(text)
4. Context.add_user_message("Open Safari")
5. LLM.complete(context.get_messages(), tools=[execute_applescript, ...])
6. Provider sends request to API/MLX
7. API/MLX processes and returns
8. Provider parses response → CompletionResult(tool_calls=[...])
9. Orchestrator detects tool_calls
10. For each tool_call:
    a. MCP.execute_tool(name, args)
    b. Context.add_tool_result(id, result, name)
11. LLM.complete(context.get_messages()) # with tool results
12. Provider returns final response
13. Context.add_assistant_message(response)
14. TTS.speak(response)
```

## Provider Selection Logic

```python
# config.yaml determines provider
llm:
  backend: local_gpt_oss  # or openai, anthropic, openrouter

# Factory creates appropriate provider
provider = ProviderFactory.create_from_config(config)

# Returns one of:
# - LocalGPTOSSProvider (privacy-first, free, on-device)
# - OpenAIProvider (cloud, fast, powerful)
# - AnthropicProvider (cloud, advanced reasoning)
# - OpenRouterProvider (multi-model access)
```

## Error Handling Flow

```
Provider.complete(messages)
    ↓
Try API Call
    ↓
Success? ──Yes→ Return CompletionResult
    ↓ No
Exception Type?
    ├─ ConnectError → LLMConnectionError → Retry (3x) or Fallback
    ├─ TimeoutError → LLMTimeoutError → Retry or Reduce max_tokens
    ├─ RateLimitError → LLMRateLimitError → Wait & Retry
    └─ Other → LLMError → Log & Notify user
```

## Configuration Flow

```
config.yaml
    ↓
YAML Parser
    ↓
Config Dict
    ↓
ProviderFactory.create_from_config()
    ↓
Extract backend name
    ↓
Validate provider config
    ↓
Get provider class from registry
    ↓
Instantiate provider with config
    ↓
Return LLMProvider instance
```

## Tool Calling Flow

```
1. Orchestrator calls LLM with tools:
   result = await llm.complete(messages, tools=[tool1, tool2, ...])

2. LLM decides to use tools:
   result.tool_calls = [
       ToolCall(id="1", name="execute_applescript", arguments={...}),
       ToolCall(id="2", name="web_search", arguments={...})
   ]

3. Orchestrator executes each tool via MCP:
   for call in result.tool_calls:
       tool_result = await mcp.execute_tool(call.name, call.arguments)
       context.add_tool_result(call.id, str(tool_result), call.name)

4. Orchestrator calls LLM again with tool results:
   final_result = await llm.complete(context.get_messages(), tools=tools)

5. LLM synthesizes final response with tool results:
   "I've opened Safari for you."
```

## Context Management Flow

```
Turn 1:
  User: "My name is Alice"
  → context.add_user_message("My name is Alice")
  → LLM processes
  → context.add_assistant_message("Nice to meet you, Alice!")
  State: [system, user1, asst1]

Turn 2:
  User: "What's my name?"
  → context.add_user_message("What's my name?")
  → LLM processes with full context
  → context.add_assistant_message("Your name is Alice.")
  State: [system, user1, asst1, user2, asst2]

Turn 11 (exceeds max_turns=10):
  → Auto-prune oldest messages
  → Keep system message + last 10 turns
  State: [system, user2, asst2, ..., user11, asst11]
```

## Performance Optimization

```
1. Connection Pooling (Local/OpenRouter):
   - Reuse HTTP connections
   - Reduce handshake overhead

2. Streaming:
   - Start speaking before full response
   - Better perceived latency

3. Context Pruning:
   - Automatic by turns and tokens
   - Reduces API costs
   - Maintains relevant history

4. Retry Logic:
   - Exponential backoff
   - Avoid thundering herd
   - Automatic recovery

5. Async/Await:
   - Non-blocking operations
   - Concurrent tool execution possible
```

## Security Considerations

```
1. API Keys:
   ✓ Stored in environment variables
   ✓ Never logged or exposed
   ✓ Loaded at runtime only

2. User Data:
   ✓ Local provider = full privacy
   ✓ Cloud providers = transmitted over HTTPS
   ✓ No conversation storage (configurable)

3. Tool Execution:
   ✓ LLM requests tools
   ✓ Orchestrator validates
   ✓ MCP enforces permissions
   ✓ User confirmation for sensitive ops

4. Error Messages:
   ✓ Sanitized (no API keys)
   ✓ User-friendly
   ✓ Detailed logging separately
```

## Extension Points

```
1. Custom Providers:
   class MyProvider(LLMProvider):
       async def complete(self, messages, **kwargs):
           # Your implementation
           pass

   ProviderFactory.register_provider("myprovider", MyProvider)

2. Custom Tools:
   tools.append(ToolDefinition(
       name="my_tool",
       description="Does something",
       parameters={...}
   ))

3. Custom Context Pruning:
   class SmartContext(ConversationContext):
       def _prune_history(self):
           # Your custom logic
           pass
```

## Testing Strategy

```
Unit Tests (mocked):
  - Base classes and data models
  - Context management
  - Factory logic
  - Each provider with mocked HTTP

Integration Tests (real):
  - Full pipeline with test accounts
  - Provider switching
  - Tool calling end-to-end
  - Error recovery

Performance Tests:
  - Latency benchmarks
  - Token throughput
  - Memory usage
  - Concurrent requests
```

## Dependencies

```
Production:
  - httpx: HTTP client (Local, OpenRouter)
  - openai: OpenAI SDK
  - anthropic: Anthropic SDK
  - mlx-lm: Local MLX inference
  - tenacity: Retry logic

Development:
  - pytest: Testing framework
  - pytest-asyncio: Async test support
  - pytest-mock: Mocking utilities
```

---

For implementation details, see source files in `python-service/src/voice_assistant/llm/`

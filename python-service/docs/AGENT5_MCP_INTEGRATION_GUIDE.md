# Agent 5: MCP Server Integration Guide

**For Agent 6 (Orchestrator) - How to integrate with MCP server**

---

## Quick Start

### 1. Import MCP Components

```python
from voice_assistant.mcp import MCPServer, get_server
from voice_assistant.mcp.server import (
    execute_applescript,
    control_application,
    file_operation,
    send_message,
    web_search,
    get_system_info,
)
```

### 2. Initialize MCP Server

```python
# Get server instance (singleton)
mcp_server = get_server()

# Check which tools are enabled
if mcp_server.is_tool_enabled("execute_applescript"):
    print("AppleScript tool is enabled")
```

### 3. Call Tools

```python
# Call tools directly
result = await execute_applescript('tell application "Safari" to activate')
print(result)

# Or use the server's tool instances
result = await mcp_server.applescript.execute(script)
```

---

## Integration with LLM

The MCP server is designed to work seamlessly with LLM providers that support tool calling (function calling).

### Tool Definitions for LLM

All 6 tools are already defined with FastMCP decorators. To get tool definitions for your LLM provider:

```python
from voice_assistant.mcp.server import mcp

# Get all tool definitions
tools = mcp.list_tools()

# Convert to format your LLM expects
# For OpenAI/Anthropic, tools are already in correct format
```

### Example: Tool Calling with Anthropic Claude

```python
from anthropic import Anthropic
from voice_assistant.mcp import get_server
from voice_assistant.mcp.server import (
    execute_applescript,
    control_application,
    file_operation,
    send_message,
    web_search,
    get_system_info,
)

client = Anthropic()

# Define available tools for Claude
tools = [
    {
        "name": "execute_applescript",
        "description": "Execute AppleScript code on macOS...",
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "AppleScript code to execute"
                }
            },
            "required": ["script"]
        }
    },
    # ... other tools
]

# Get LLM response with tools
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "Open Safari and search for weather"}
    ]
)

# Execute tool calls
if response.stop_reason == "tool_use":
    for tool_use in response.content:
        if tool_use.type == "tool_use":
            tool_name = tool_use.name
            tool_input = tool_use.input

            # Execute the tool
            if tool_name == "execute_applescript":
                result = await execute_applescript(**tool_input)
            elif tool_name == "control_application":
                result = await control_application(**tool_input)
            # ... etc

            # Feed result back to LLM
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result
                    }
                ]
            })
```

### Example: Tool Calling with OpenAI

```python
from openai import OpenAI
from voice_assistant.mcp.server import execute_applescript

client = OpenAI()

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_applescript",
            "description": "Execute AppleScript code on macOS",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "AppleScript code to execute"
                    }
                },
                "required": ["script"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Open Safari"}
    ],
    tools=tools
)

# Execute tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "execute_applescript":
            result = await execute_applescript(**arguments)
```

---

## Orchestrator Integration Pattern

Here's the recommended pattern for Agent 6 (Orchestrator):

```python
class VoiceAssistant:
    """Main orchestrator coordinating all subsystems"""

    def __init__(self, config: Configuration):
        self.audio_pipeline = AudioPipeline(config)
        self.stt = WhisperSTT(config)
        self.llm = ProviderFactory.create(config.llm_backend, config)
        self.mcp_server = get_server()  # Initialize MCP server
        self.tts = MacOSTTS(config)
        self.state = ConversationState()

    async def _handle_audio(self, audio_event: AudioEvent):
        """Main processing pipeline"""

        # 1. Transcribe audio
        transcription = await self.stt.transcribe(audio_event.audio_data)

        # 2. Get LLM response with MCP tools
        messages = self.state.get_messages()
        messages.append(Message(role="user", content=transcription.text))

        # Get MCP tool definitions
        tools = self._get_mcp_tools()

        # Call LLM with tools
        result = await self.llm.complete(messages, tools=tools)

        # 3. Execute tool calls if present
        if result.tool_calls:
            for tool_call in result.tool_calls:
                # Execute MCP tool
                tool_result = await self._execute_mcp_tool(
                    tool_call.name,
                    tool_call.arguments
                )

                # Add tool result to messages
                messages.append(Message(
                    role="tool",
                    content=str(tool_result)
                ))

            # Get final response with tool results
            result = await self.llm.complete(messages)

        # 4. Speak response
        await self.tts.speak(result.content)

        # 5. Update conversation state
        self.state.add_exchange(transcription.text, result.content)

    def _get_mcp_tools(self) -> List[ToolDefinition]:
        """Get MCP tool definitions for LLM"""
        tools = []

        # Only include enabled tools
        if self.mcp_server.is_tool_enabled("execute_applescript"):
            tools.append({
                "name": "execute_applescript",
                "description": "Execute AppleScript code on macOS",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script": {"type": "string"}
                    },
                    "required": ["script"]
                }
            })

        # Add other tools...
        # (See full tool definitions in MCP_TOOLS_REFERENCE.md)

        return tools

    async def _execute_mcp_tool(
        self,
        tool_name: str,
        arguments: dict
    ) -> str:
        """Execute MCP tool by name"""

        # Import tools
        from voice_assistant.mcp.server import (
            execute_applescript,
            control_application,
            file_operation,
            send_message,
            web_search,
            get_system_info,
        )

        # Map tool names to functions
        tool_map = {
            "execute_applescript": execute_applescript,
            "control_application": control_application,
            "file_operation": file_operation,
            "send_message": send_message,
            "web_search": web_search,
            "get_system_info": get_system_info,
        }

        # Execute tool
        if tool_name in tool_map:
            try:
                result = await tool_map[tool_name](**arguments)
                return result
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"
        else:
            return f"Unknown tool: {tool_name}"
```

---

## Complete Tool Definitions

For easy copy-paste into your LLM integration:

```python
MCP_TOOL_DEFINITIONS = [
    {
        "name": "execute_applescript",
        "description": """Execute AppleScript code on macOS. Use this for opening apps,
        controlling Safari, setting volume, showing notifications, etc. Dangerous patterns
        like shell execution are automatically blocked.""",
        "parameters": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "AppleScript code to execute"
                }
            },
            "required": ["script"]
        }
    },
    {
        "name": "control_application",
        "description": """Control macOS applications using Accessibility API. Can click
        buttons, fill text fields, read text. Requires Accessibility permission.""",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Application name (e.g., 'Safari', 'Messages')"
                },
                "action": {
                    "type": "string",
                    "enum": ["click_button", "fill_field", "get_text"],
                    "description": "Action to perform"
                },
                "params": {
                    "type": "object",
                    "description": "Action-specific parameters",
                    "properties": {
                        "button_title": {"type": "string"},
                        "field_label": {"type": "string"},
                        "text": {"type": "string"},
                        "window_index": {"type": "integer"},
                        "element_type": {"type": "string"}
                    }
                }
            },
            "required": ["app_name", "action"]
        }
    },
    {
        "name": "file_operation",
        "description": """Perform file system operations (read, write, list, delete,
        move, copy). All operations sandboxed to home directory for security.""",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "delete", "move", "copy"],
                    "description": "Operation type"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path (supports ~ expansion)"
                },
                "content": {
                    "type": "string",
                    "description": "Content for write operations"
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Allow overwriting existing files (write operation)"
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files (list operation)"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Delete non-empty directories (delete operation)"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path (move/copy operations)"
                }
            },
            "required": ["operation", "path"]
        }
    },
    {
        "name": "send_message",
        "description": """Send iMessage or SMS via Messages app. Requires user
        confirmation by default for security. Can send to phone numbers or contact names.""",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Phone number (e.g., '+1234567890') or contact name"
                },
                "message": {
                    "type": "string",
                    "description": "Message text (max 1000 characters)"
                },
                "platform": {
                    "type": "string",
                    "enum": ["imessage", "sms"],
                    "description": "Message platform (both use Messages app)"
                }
            },
            "required": ["recipient", "message"]
        }
    },
    {
        "name": "web_search",
        "description": """Search the web using DuckDuckGo and return formatted results
        with titles, descriptions, and URLs. Privacy-focused with no tracking.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (max 500 characters)"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10, default: 5)",
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_system_info",
        "description": """Get macOS system information including battery, disk, memory,
        CPU, network status, running apps, date/time, and system details.""",
        "parameters": {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "enum": [
                        "battery", "disk", "memory", "cpu", "network",
                        "apps", "datetime", "system", "summary"
                    ],
                    "description": "Type of information to retrieve"
                }
            },
            "required": []
        }
    }
]
```

---

## Error Handling

Always handle tool execution errors:

```python
async def _execute_mcp_tool(self, tool_name: str, arguments: dict) -> str:
    """Execute MCP tool with error handling"""

    try:
        # Execute tool
        result = await tool_map[tool_name](**arguments)
        return result

    except ValidationError as e:
        # Input validation failed
        logger.warning(f"Tool validation error: {e}")
        return f"Validation error: {str(e)}"

    except Exception as e:
        # Tool execution failed
        logger.error(f"Tool execution error: {e}")
        return f"Error: {str(e)}"
```

---

## Testing MCP Integration

```python
import pytest
from voice_assistant.mcp import get_server
from voice_assistant.mcp.server import execute_applescript, get_system_info

@pytest.mark.asyncio
async def test_mcp_integration():
    """Test MCP server integration"""

    # Get server
    server = get_server()
    assert server is not None

    # Test tool execution
    result = await execute_applescript('return "test"')
    assert isinstance(result, str)

    # Test system info
    result = await get_system_info("datetime")
    assert isinstance(result, str)
    assert len(result) > 0
```

---

## Configuration

The MCP server automatically loads configuration from `config.yaml`:

```yaml
mcp:
  tools_enabled:
    - execute_applescript
    - control_application
    - file_operation
    - send_message
    - web_search
    - get_system_info

  tools:
    execute_applescript:
      timeout: 30
      sandbox: true

    file_operation:
      allowed_paths:
        - ~/Documents
        - ~/Downloads
        - ~/Desktop
      blocked_paths:
        - ~/.ssh
        - ~/.gnupg

    send_message:
      require_confirmation: true
      allowed_contacts: []

    web_search:
      engine: duckduckgo
      max_results: 5
      timeout: 10
```

---

## Logging

MCP server logs to `/tmp/voice-assistant/logs/mcp-server.log`:

```python
from loguru import logger

# Configure logging in orchestrator
logger.add(
    "/tmp/voice-assistant/logs/orchestrator.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)

# MCP tool execution is automatically logged
```

---

## Performance Considerations

### 1. Tool Timeouts

Be aware of tool execution times:
- AppleScript: Up to 30s
- Web search: Up to 10s
- File operations: Variable (depends on file size)
- System info: <1s
- Messages: <5s
- Accessibility: <2s

### 2. Concurrent Execution

Tools can be executed concurrently if independent:

```python
# Execute multiple system info queries in parallel
battery, cpu, memory = await asyncio.gather(
    get_system_info("battery"),
    get_system_info("cpu"),
    get_system_info("memory")
)
```

### 3. Caching

Consider caching frequent queries:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedSystemInfo:
    def __init__(self):
        self._cache = {}
        self._cache_duration = timedelta(seconds=30)

    async def get_info(self, info_type: str) -> str:
        # Check cache
        if info_type in self._cache:
            cached_time, cached_result = self._cache[info_type]
            if datetime.now() - cached_time < self._cache_duration:
                return cached_result

        # Fetch fresh data
        result = await get_system_info(info_type)
        self._cache[info_type] = (datetime.now(), result)
        return result
```

---

## Complete Integration Example

```python
"""
Complete example of MCP integration in orchestrator
"""

import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass

from voice_assistant.mcp import get_server
from voice_assistant.mcp.server import (
    execute_applescript,
    control_application,
    file_operation,
    send_message,
    web_search,
    get_system_info,
)


@dataclass
class ToolCall:
    name: str
    arguments: dict


class MCPOrchestrator:
    """Orchestrator with MCP integration"""

    def __init__(self):
        self.mcp_server = get_server()
        self.tool_map = {
            "execute_applescript": execute_applescript,
            "control_application": control_application,
            "file_operation": file_operation,
            "send_message": send_message,
            "web_search": web_search,
            "get_system_info": get_system_info,
        }

    async def execute_tool_calls(
        self,
        tool_calls: List[ToolCall]
    ) -> List[str]:
        """Execute multiple tool calls and return results"""

        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool(
                tool_call.name,
                tool_call.arguments
            )
            results.append(result)

        return results

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict
    ) -> str:
        """Execute a single tool"""

        # Check if tool exists and is enabled
        if tool_name not in self.tool_map:
            return f"Unknown tool: {tool_name}"

        if not self.mcp_server.is_tool_enabled(tool_name):
            return f"Tool '{tool_name}' is disabled"

        # Execute tool
        try:
            tool_func = self.tool_map[tool_name]
            result = await tool_func(**arguments)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for LLM"""

        # Import definitions
        from .tool_definitions import MCP_TOOL_DEFINITIONS

        # Filter to enabled tools
        enabled_tools = []
        for tool_def in MCP_TOOL_DEFINITIONS:
            if self.mcp_server.is_tool_enabled(tool_def["name"]):
                enabled_tools.append(tool_def)

        return enabled_tools


# Example usage
async def main():
    orchestrator = MCPOrchestrator()

    # Get tool definitions for LLM
    tools = orchestrator.get_tool_definitions()
    print(f"Available tools: {len(tools)}")

    # Execute a tool
    result = await orchestrator.execute_tool(
        "get_system_info",
        {"info_type": "datetime"}
    )
    print(f"Result: {result}")

    # Execute multiple tools
    tool_calls = [
        ToolCall("get_system_info", {"info_type": "battery"}),
        ToolCall("get_system_info", {"info_type": "cpu"}),
    ]
    results = await orchestrator.execute_tool_calls(tool_calls)
    for i, result in enumerate(results):
        print(f"Result {i+1}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Next Steps

1. **Read**: MCP_TOOLS_REFERENCE.md for detailed tool documentation
2. **Implement**: Tool calling in your LLM provider integration
3. **Test**: Run integration tests in tests/mcp/
4. **Monitor**: Check logs at /tmp/voice-assistant/logs/mcp-server.log

---

**Questions?**

See:
- MCP_TOOLS_REFERENCE.md - Complete tool documentation
- tests/mcp/ - Example usage in tests
- config.yaml - Configuration options

---

**End of Integration Guide**

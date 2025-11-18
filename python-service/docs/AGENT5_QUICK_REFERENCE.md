# Agent 5: MCP Tools Quick Reference

**Quick reference for integrating MCP tools into the orchestrator**

---

## Import

```python
from voice_assistant.mcp import get_server
from voice_assistant.mcp.server import (
    execute_applescript,
    control_application,
    file_operation,
    send_message,
    web_search,
    get_system_info,
)
```

---

## Initialize

```python
# In orchestrator __init__
self.mcp_server = get_server()
```

---

## Tool Calls

### 1. AppleScript
```python
result = await execute_applescript('tell application "Safari" to activate')
```

### 2. Control Application
```python
result = await control_application(
    app_name="Safari",
    action="click_button",
    params={"button_title": "Search"}
)
```

### 3. File Operation
```python
result = await file_operation(
    operation="read",
    path="~/Documents/notes.txt"
)
```

### 4. Send Message
```python
result = await send_message(
    recipient="+1234567890",
    message="Hello!"
)
```

### 5. Web Search
```python
result = await web_search(
    query="macOS features",
    num_results=5
)
```

### 6. System Info
```python
result = await get_system_info(info_type="battery")
```

---

## Tool Definitions for LLM

```python
MCP_TOOLS = [
    {
        "name": "execute_applescript",
        "description": "Execute AppleScript code on macOS",
        "parameters": {
            "type": "object",
            "properties": {
                "script": {"type": "string"}
            },
            "required": ["script"]
        }
    },
    {
        "name": "control_application",
        "description": "Control macOS apps via Accessibility API",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string"},
                "action": {
                    "type": "string",
                    "enum": ["click_button", "fill_field", "get_text"]
                },
                "params": {"type": "object"}
            },
            "required": ["app_name", "action"]
        }
    },
    {
        "name": "file_operation",
        "description": "Perform file operations",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "delete", "move", "copy"]
                },
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["operation", "path"]
        }
    },
    {
        "name": "send_message",
        "description": "Send iMessage/SMS",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "message": {"type": "string"},
                "platform": {"type": "string"}
            },
            "required": ["recipient", "message"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "num_results": {"type": "integer"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_system_info",
        "description": "Get system information",
        "parameters": {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "enum": ["battery", "disk", "memory", "cpu", "network", "apps", "datetime", "system", "summary"]
                }
            }
        }
    }
]
```

---

## Execute Tool by Name

```python
async def execute_tool(tool_name: str, arguments: dict) -> str:
    tool_map = {
        "execute_applescript": execute_applescript,
        "control_application": control_application,
        "file_operation": file_operation,
        "send_message": send_message,
        "web_search": web_search,
        "get_system_info": get_system_info,
    }

    if tool_name in tool_map:
        return await tool_map[tool_name](**arguments)
    else:
        return f"Unknown tool: {tool_name}"
```

---

## Error Handling

```python
try:
    result = await execute_applescript(script)
except Exception as e:
    # All errors return as strings, no exceptions raised
    # Check result content for error messages
    if "error" in result.lower() or "failed" in result.lower():
        # Handle error
        pass
```

---

## Common Patterns

### Open App and Navigate
```python
await execute_applescript('tell application "Safari" to activate')
await control_application(
    "Safari", "fill_field",
    {"field_label": "Search", "text": "weather"}
)
```

### Get System Status
```python
battery = await get_system_info("battery")
cpu = await get_system_info("cpu")
memory = await get_system_info("memory")
```

### Search and Open
```python
results = await web_search("best restaurants NYC", 3)
# Parse results and open in Safari
await execute_applescript(
    'tell application "Safari" to open location "URL"'
)
```

### File Management
```python
# List files
files = await file_operation("list", "~/Downloads")
# Read file
content = await file_operation("read", "~/Documents/notes.txt")
# Write file
await file_operation("write", "~/Documents/new.txt", content="Hello")
```

---

## Documentation

- **Complete Reference**: `docs/MCP_TOOLS_REFERENCE.md`
- **Integration Guide**: `docs/AGENT5_MCP_INTEGRATION_GUIDE.md`
- **Delivery Summary**: `AGENT_5_DELIVERY_SUMMARY.md`

---

## Testing

```bash
# Run MCP tests
cd python-service
pytest tests/mcp/ -v
```

---

## Configuration

```yaml
# config.yaml
mcp:
  tools_enabled:
    - execute_applescript
    - control_application
    - file_operation
    - send_message
    - web_search
    - get_system_info
```

---

**Quick Start**: Import → Initialize → Call Tools → Handle Results

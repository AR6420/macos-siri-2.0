# MCP Tools Reference

**Complete reference for Voice Assistant MCP automation tools**

Version: 1.0.0
Date: 2025-11-18

---

## Overview

The MCP (Model Context Protocol) server provides 6 powerful automation tools that enable the Voice Assistant to interact with macOS:

1. **execute_applescript** - Execute AppleScript commands
2. **control_application** - Control apps via Accessibility API
3. **file_operation** - File system operations
4. **send_message** - Send iMessages/SMS
5. **web_search** - Search the web
6. **get_system_info** - Query system information

All tools include security validation, error handling, and detailed documentation.

---

## Tool 1: execute_applescript

Execute AppleScript code on macOS for application automation and system control.

### Function Signature

```python
async def execute_applescript(script: str) -> str
```

### Parameters

- **script** (str): AppleScript code to execute

### Returns

- **str**: Script output or error message

### Security Features

- ✅ Dangerous patterns blocked (shell execution, sudo, rm -rf, etc.)
- ✅ Script length limited to 10,000 characters
- ✅ Execution timeout of 30 seconds
- ✅ Sandboxed execution mode

### Examples

#### Example 1: Open Application
```python
result = await execute_applescript('tell application "Safari" to activate')
# Returns: ""
```

#### Example 2: Get Current Date
```python
result = await execute_applescript('return (current date) as text')
# Returns: "Tuesday, November 18, 2025 at 3:45:00 PM"
```

#### Example 3: Set System Volume
```python
result = await execute_applescript('set volume output volume 50')
# Returns: ""
```

#### Example 4: Show Notification
```python
result = await execute_applescript('''
display notification "Task completed!" with title "Voice Assistant"
''')
# Returns: ""
```

#### Example 5: Control Safari
```python
result = await execute_applescript('''
tell application "Safari"
    activate
    open location "https://www.apple.com"
end tell
''')
# Returns: ""
```

#### Example 6: Get Window Title
```python
result = await execute_applescript('''
tell application "Safari"
    if (count of windows) > 0 then
        return name of front window
    else
        return "No windows open"
    end if
end tell
''')
# Returns: "Apple - Safari"
```

### Common AppleScript Patterns

#### Open Application
```applescript
tell application "AppName" to activate
```

#### Quit Application
```applescript
tell application "AppName" to quit
```

#### Get Clipboard
```applescript
the clipboard as text
```

#### Set Clipboard
```applescript
set the clipboard to "text"
```

#### Music Control
```applescript
tell application "Music"
    playpause
end tell
```

### Error Handling

```python
try:
    result = await execute_applescript(script)
except ValidationError as e:
    # Script contains dangerous patterns
    print(f"Validation failed: {e}")
except AppleScriptError as e:
    # Script execution failed
    print(f"Execution failed: {e}")
```

---

## Tool 2: control_application

Control macOS applications using the Accessibility API.

### Function Signature

```python
async def control_application(
    app_name: str,
    action: str,
    params: Optional[Dict[str, Any]] = None
) -> str
```

### Parameters

- **app_name** (str): Application name (e.g., "Safari", "Messages")
- **action** (str): Action to perform
  - `"click_button"` - Click a button
  - `"fill_field"` - Fill a text field
  - `"get_text"` - Read text from element
- **params** (dict, optional): Action-specific parameters

### Action-Specific Parameters

#### click_button
```python
{
    "button_title": "Search",      # Button label/title
    "window_index": 0              # Window index (0 = front)
}
```

#### fill_field
```python
{
    "field_label": "Search",       # Field label/title
    "text": "query text",          # Text to enter
    "window_index": 0              # Window index
}
```

#### get_text
```python
{
    "element_type": "title"        # "title", "text", "value"
}
```

### Returns

- **str**: Success message or error

### Security Features

- ✅ Requires Accessibility permission
- ✅ System utilities blocked (Terminal, Activity Monitor, etc.)
- ✅ App name validation
- ✅ Only works with running applications

### Examples

#### Example 1: Click Button
```python
result = await control_application(
    app_name="Safari",
    action="click_button",
    params={"button_title": "Search"}
)
# Returns: "Successfully clicked 'Search' in Safari"
```

#### Example 2: Fill Search Field
```python
result = await control_application(
    app_name="Safari",
    action="fill_field",
    params={
        "field_label": "Search",
        "text": "macOS features"
    }
)
# Returns: "Successfully filled 'Search' in Safari"
```

#### Example 3: Get Window Title
```python
result = await control_application(
    app_name="Safari",
    action="get_text",
    params={"element_type": "title"}
)
# Returns: "Apple - Safari"
```

### Permission Requirements

To use this tool, Accessibility permission must be granted:

1. Open **System Settings**
2. Go to **Privacy & Security** > **Accessibility**
3. Enable **Voice Assistant**

### Limitations

- Not all applications support Accessibility API equally
- Some apps may have protected UI elements
- Electron apps may have limited support
- Complex UI hierarchies may be challenging

---

## Tool 3: file_operation

Perform secure file system operations.

### Function Signature

```python
async def file_operation(
    operation: str,
    path: str,
    content: Optional[str] = None,
    **kwargs: Any
) -> str
```

### Parameters

- **operation** (str): Operation type
  - `"read"` - Read file contents
  - `"write"` - Write content to file
  - `"list"` - List directory contents
  - `"delete"` - Delete file/directory
  - `"move"` - Move file/directory
  - `"copy"` - Copy file/directory
- **path** (str): File/directory path (supports `~` expansion)
- **content** (str, optional): Content for write operations
- **kwargs**: Operation-specific parameters

### Operation-Specific Parameters

#### read
```python
{
    "max_size_mb": 10  # Maximum file size in MB
}
```

#### write
```python
{
    "overwrite": True  # Allow overwriting existing file
}
```

#### list
```python
{
    "include_hidden": False  # Include hidden files (.*)
}
```

#### delete
```python
{
    "recursive": False  # Delete non-empty directories
}
```

#### move / copy
```python
{
    "destination": "~/Documents/newfile.txt"  # Destination path
}
```

### Returns

- **str**: Operation result or error message

### Security Features

- ✅ Sandboxed to home directory
- ✅ System paths blocked (/System, /Library, etc.)
- ✅ Sensitive directories blocked (~/.ssh, ~/.gnupg)
- ✅ File size limits (10MB default for reads)
- ✅ Path validation and resolution

### Examples

#### Example 1: Read File
```python
result = await file_operation(
    operation="read",
    path="~/Documents/notes.txt"
)
# Returns: "File contents here..."
```

#### Example 2: Write File
```python
result = await file_operation(
    operation="write",
    path="~/Documents/todo.txt",
    content="1. Buy groceries\n2. Call dentist",
    overwrite=True
)
# Returns: "Successfully wrote 35 bytes to ~/Documents/todo.txt"
```

#### Example 3: List Directory
```python
result = await file_operation(
    operation="list",
    path="~/Downloads"
)
# Returns:
# Contents of ~/Downloads:
# FILE      1.2MB  report.pdf
# FILE      500KB  image.png
# DIR            0  Archive
```

#### Example 4: Delete File
```python
result = await file_operation(
    operation="delete",
    path="~/Downloads/old-file.txt"
)
# Returns: "Successfully deleted file: ~/Downloads/old-file.txt"
```

#### Example 5: Move File
```python
result = await file_operation(
    operation="move",
    path="~/Downloads/document.pdf",
    destination="~/Documents/document.pdf"
)
# Returns: "Successfully moved ~/Downloads/document.pdf to ~/Documents/document.pdf"
```

#### Example 6: Copy File
```python
result = await file_operation(
    operation="copy",
    path="~/Documents/template.txt",
    destination="~/Documents/new-doc.txt"
)
# Returns: "Successfully copied ~/Documents/template.txt to ~/Documents/new-doc.txt"
```

### Allowed Paths

By default, operations are allowed in:
- `~/Documents`
- `~/Downloads`
- `~/Desktop`
- `~/Pictures`
- `~/Music`
- `~/Videos`

### Blocked Paths

The following paths are always blocked:
- `/System`
- `/Library`
- `/private`
- `/usr`
- `/bin`
- `/sbin`
- `~/.ssh`
- `~/.gnupg`

---

## Tool 4: send_message

Send messages via the macOS Messages app.

### Function Signature

```python
async def send_message(
    recipient: str,
    message: str,
    platform: str = "imessage"
) -> str
```

### Parameters

- **recipient** (str): Phone number (e.g., "+1234567890") or contact name
- **message** (str): Message text (max 1000 characters)
- **platform** (str): "imessage" or "sms" (both use Messages app)

### Returns

- **str**: Success message or confirmation request

### Security Features

- ✅ Requires user confirmation by default (configurable)
- ✅ Contact whitelist support (optional)
- ✅ Message length limited to 1000 characters
- ✅ Phone number format validation

### Examples

#### Example 1: Send iMessage
```python
result = await send_message(
    recipient="+1234567890",
    message="Hello from Voice Assistant!"
)
# Returns: "Message prepared for +1234567890. User confirmation required..."
```

#### Example 2: Send to Contact
```python
result = await send_message(
    recipient="John Doe",
    message="Meeting at 3pm in conference room"
)
# Returns: "Message prepared for John Doe. User confirmation required..."
```

### Configuration

In `config.yaml`:

```yaml
mcp:
  tools:
    send_message:
      require_confirmation: true
      allowed_contacts: []  # Empty = all allowed
```

To disable confirmation (not recommended):

```yaml
send_message:
  require_confirmation: false
```

To whitelist specific contacts:

```yaml
send_message:
  require_confirmation: true
  allowed_contacts:
    - "+1234567890"
    - "John Doe"
```

### Requirements

- Messages app must be installed (default on macOS)
- Messages app must be signed in with iMessage or phone number
- For reading messages: Full Disk Access permission required

### Limitations

- Requires user confirmation by default for security
- Cannot read message history without Full Disk Access
- Group messages may have limited support
- Delivery confirmation not available

---

## Tool 5: web_search

Search the web using DuckDuckGo.

### Function Signature

```python
async def web_search(
    query: str,
    num_results: int = 5
) -> str
```

### Parameters

- **query** (str): Search query (max 500 characters)
- **num_results** (int): Number of results (1-10, default: 5)

### Returns

- **str**: Formatted search results with titles, descriptions, and URLs

### Security Features

- ✅ Privacy-focused DuckDuckGo search
- ✅ Query length limited to 500 characters
- ✅ Search timeout: 10 seconds
- ✅ No tracking or data collection

### Examples

#### Example 1: Basic Search
```python
result = await web_search(
    query="macOS Tahoe features",
    num_results=3
)
# Returns:
# Web search results for 'macOS Tahoe features':
#
# 1. macOS Tahoe 26.1 - New Features Overview
#    Discover the latest features in macOS Tahoe including...
#    URL: https://www.apple.com/macos/tahoe
#
# 2. What's New in macOS 26.1 Tahoe
#    Complete guide to macOS Tahoe new features...
#    URL: https://support.apple.com/macos-tahoe
#
# 3. macOS Tahoe Review
#    In-depth review of macOS Tahoe's new capabilities...
#    URL: https://www.macworld.com/macos-tahoe-review
```

#### Example 2: Definition Search
```python
result = await web_search(
    query="what is machine learning",
    num_results=2
)
# Returns formatted results with definitions
```

#### Example 3: News Search
```python
result = await web_search(
    query="latest tech news",
    num_results=5
)
# Returns current news articles
```

### Result Format

Each result includes:
- **Title**: Page title
- **Description**: Page snippet/summary
- **URL**: Full URL

### Configuration

In `config.yaml`:

```yaml
mcp:
  tools:
    web_search:
      engine: duckduckgo  # Currently only DuckDuckGo supported
      max_results: 5
      timeout: 10
```

### Requirements

- Internet connection required
- No API keys needed (DuckDuckGo is free)

### Limitations

- DuckDuckGo only (Google support planned)
- Results may vary by region
- No image search support yet
- No advanced search operators

---

## Tool 6: get_system_info

Query macOS system information and status.

### Function Signature

```python
async def get_system_info(
    info_type: str = "summary"
) -> str
```

### Parameters

- **info_type** (str): Type of information to retrieve
  - `"battery"` - Battery status and charge level
  - `"disk"` - Disk usage and available space
  - `"memory"` - RAM usage and availability
  - `"cpu"` - CPU usage and core count
  - `"network"` - Network interfaces and IP addresses
  - `"apps"` - Running applications with resource usage
  - `"datetime"` - Current date and time
  - `"system"` - System information (OS version, architecture)
  - `"summary"` - All of the above (default)

### Returns

- **str**: Formatted system information

### Security Features

- ✅ Read-only operations
- ✅ No sensitive information exposed
- ✅ No system modification capabilities

### Examples

#### Example 1: Get Battery Status
```python
result = await get_system_info(info_type="battery")
# Returns: "Battery: 85% (On battery, 4h 30m remaining)"
# Or: "No battery found (desktop system)"
```

#### Example 2: Get Disk Usage
```python
result = await get_system_info(info_type="disk")
# Returns:
# Disk Usage (/):
#   Total: 1000.0 GB
#   Used: 450.0 GB (45%)
#   Free: 550.0 GB
```

#### Example 3: Get Memory Usage
```python
result = await get_system_info(info_type="memory")
# Returns:
# Memory Usage:
#   Total: 256.0 GB
#   Used: 128.5 GB (50%)
#   Available: 127.5 GB
```

#### Example 4: Get CPU Usage
```python
result = await get_system_info(info_type="cpu")
# Returns:
# CPU Usage:
#   Average: 25.3%
#   Cores: 24 physical, 24 logical
```

#### Example 5: Get Network Status
```python
result = await get_system_info(info_type="network")
# Returns:
# Network Interfaces:
#   en0: 192.168.1.100
#   en1: 10.0.0.50
```

#### Example 6: Get Running Apps
```python
result = await get_system_info(info_type="apps")
# Returns:
# Running Applications:
#   Safari               - CPU:  10.5%, Memory:   2.3%
#   Music                - CPU:   5.2%, Memory:   1.8%
#   Messages             - CPU:   1.1%, Memory:   0.9%
```

#### Example 7: Get Date/Time
```python
result = await get_system_info(info_type="datetime")
# Returns: "Tuesday, November 18, 2025 at 03:45 PM"
```

#### Example 8: Get System Info
```python
result = await get_system_info(info_type="system")
# Returns:
# System Information:
#   OS: Darwin 26.1
#   Version: Darwin Kernel Version 26.1.0
#   Architecture: arm64
#   Processor: Apple M3 Ultra
```

#### Example 9: Get Summary (All Info)
```python
result = await get_system_info(info_type="summary")
# Returns comprehensive system overview with all categories
```

### Use Cases

- **Voice queries**: "What's my battery level?"
- **System monitoring**: Check resource usage
- **Troubleshooting**: Diagnose performance issues
- **Automation**: Trigger actions based on system state

### Requirements

- No special permissions required for most queries
- Battery info only available on laptops
- Network info may require network access

### Limitations

- Battery info not available on desktop Macs
- Some resource values are snapshots (not real-time)
- App list filtered for relevance (top 10 only)

---

## Tool Configuration

All tools can be enabled/disabled in `config.yaml`:

```yaml
mcp:
  tools_enabled:
    - execute_applescript
    - control_application
    - file_operation
    - send_message
    - web_search
    - get_system_info
```

To disable a tool, remove it from the list.

### Tool-Specific Configuration

```yaml
mcp:
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

## Error Handling

All tools return clear error messages when operations fail:

### Validation Errors

```
"Validation error: AppleScript validation failed: Potentially dangerous pattern detected"
"Validation error: Invalid path: Access to /System is blocked for security"
"Validation error: Invalid recipient: Recipient cannot be empty"
```

### Execution Errors

```
"Error executing AppleScript: Script execution timed out after 30s"
"Error controlling application: Application 'Safari' is not running"
"Error performing file operation: File does not exist: ~/missing.txt"
"Error sending message: Failed to send message: Messages app not running"
"Error searching web: Failed to search web: Network timeout"
"Error getting system info: Failed to get battery status: No battery found"
```

### Permission Errors

```
"Accessibility permission not granted. Please enable in System Settings..."
"Full Disk Access required to read messages"
```

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
try:
    result = await execute_applescript(script)
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
    # Provide helpful feedback to user
```

### 2. Validation

Validate inputs before calling tools:

```python
if not phone_number.startswith("+"):
    phone_number = f"+1{phone_number}"  # Add country code

result = await send_message(phone_number, message)
```

### 3. Timeouts

Be aware of tool timeouts:

- AppleScript: 30 seconds
- Web search: 10 seconds
- File operations: No timeout (synchronous)

### 4. Permissions

Check permissions before using tools:

```python
# Check Accessibility permission
from voice_assistant.mcp.tools import AccessibilityController

controller = AccessibilityController()
if not controller.check_accessibility_permission():
    print("Please enable Accessibility permission")
```

### 5. Security

Never disable security features without good reason:

```yaml
# DON'T DO THIS in production
execute_applescript:
  sandbox: false  # Dangerous!

send_message:
  require_confirmation: false  # Not recommended!
```

---

## Integration with LLM

Tools are designed for LLM consumption with:

- **Clear descriptions**: Each tool has detailed documentation
- **Type hints**: All parameters properly typed
- **Examples**: Comprehensive examples for each tool
- **Error messages**: Human-readable error feedback
- **Return values**: Formatted strings ready for voice output

### Example LLM Prompt

When the LLM needs to perform an action, it calls tools like:

```python
# User: "Open Safari and search for weather"

# LLM calls:
await execute_applescript('tell application "Safari" to activate')
await control_application(
    app_name="Safari",
    action="fill_field",
    params={"field_label": "Search", "text": "weather"}
)
```

---

## Troubleshooting

### Tool Not Working

1. **Check if enabled**: Verify tool is in `tools_enabled` list
2. **Check permissions**: Ensure required permissions granted
3. **Check logs**: Look at `/tmp/voice-assistant/logs/mcp-server.log`
4. **Test manually**: Try tool in isolation

### Permission Issues

1. **Accessibility**: System Settings > Privacy & Security > Accessibility
2. **Full Disk Access**: System Settings > Privacy & Security > Full Disk Access
3. **Automation**: System Settings > Privacy & Security > Automation

### Performance Issues

1. **Reduce timeout**: Lower timeout values in config
2. **Limit results**: Reduce `num_results` for web search
3. **Filter apps**: App list already filtered, but can be customized

---

## Future Enhancements

Planned features:

- [ ] Google search support
- [ ] Image search
- [ ] Calendar integration
- [ ] Email automation
- [ ] Spotlight search integration
- [ ] Siri Shortcuts integration
- [ ] Home Assistant integration
- [ ] Custom tool plugins

---

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/yourusername/macos-voice-assistant/issues
- **Documentation**: https://github.com/yourusername/macos-voice-assistant/docs
- **Logs**: `/tmp/voice-assistant/logs/`

---

**End of MCP Tools Reference**

"""
MCP Server for macOS Automation Tools

FastMCP 2.0 server providing tools for:
- AppleScript execution
- Accessibility API control
- File operations
- Message sending
- Web search
- System information queries
"""

import os
from typing import Any, Dict, List, Optional

import yaml
from fastmcp import FastMCP
from loguru import logger

from .tools import (
    AccessibilityController,
    AppleScriptExecutor,
    AppleScriptTemplates,
    FileOperations,
    MessagesAutomation,
    SystemInfo,
    WebSearch,
)
from .validation import ValidationError, validate_permissions

# Initialize FastMCP server
mcp = FastMCP("Voice Assistant MCP Server")


class MCPServer:
    """MCP Server managing all automation tools"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MCP server

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)

        # Initialize tool instances
        self.applescript = AppleScriptExecutor(
            timeout=self.config["mcp"]["tools"]["execute_applescript"].get(
                "timeout", 30
            ),
            sandbox=self.config["mcp"]["tools"]["execute_applescript"].get(
                "sandbox", True
            ),
        )

        self.accessibility = AccessibilityController()

        self.file_ops = FileOperations(
            config=self.config["mcp"]["tools"].get("file_operation", {})
        )

        self.messages = MessagesAutomation(
            require_confirmation=self.config["mcp"]["tools"]["send_message"].get(
                "require_confirmation", True
            ),
            config=self.config["mcp"]["tools"].get("send_message", {}),
        )

        self.web_search = WebSearch(
            config=self.config["mcp"]["tools"].get("web_search", {})
        )

        # Check which tools are enabled
        self.enabled_tools = set(self.config["mcp"].get("tools_enabled", []))

        logger.info(
            f"MCP Server initialized with {len(self.enabled_tools)} enabled tools"
        )

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            # Default config path
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "config.yaml"
            )

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            # Return default config
            return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration"""
        return {
            "mcp": {
                "tools_enabled": [
                    "execute_applescript",
                    "control_application",
                    "file_operation",
                    "send_message",
                    "web_search",
                    "get_system_info",
                ],
                "tools": {
                    "execute_applescript": {"timeout": 30, "sandbox": True},
                    "file_operation": {
                        "allowed_paths": [
                            "~/Documents",
                            "~/Downloads",
                            "~/Desktop",
                        ],
                        "blocked_paths": ["~/.ssh", "~/.gnupg"],
                    },
                    "send_message": {
                        "require_confirmation": True,
                        "allowed_contacts": [],
                    },
                    "web_search": {
                        "engine": "duckduckgo",
                        "max_results": 5,
                        "timeout": 10,
                    },
                },
            }
        }

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if tool is enabled in configuration"""
        return tool_name in self.enabled_tools


# Initialize server instance (singleton)
_server_instance: Optional[MCPServer] = None


def get_server() -> MCPServer:
    """Get or create server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = MCPServer()
    return _server_instance


# Define MCP Tools
# Tool 1: execute_applescript
@mcp.tool()
async def execute_applescript(script: str) -> str:
    """
    Execute AppleScript code on macOS.

    This tool allows you to automate macOS applications and system functions using
    AppleScript. Common uses include opening applications, controlling Safari,
    getting system information, and more.

    Args:
        script: AppleScript code to execute

    Returns:
        Script output as string, or error message if execution fails

    Examples:
        - Open Safari: 'tell application "Safari" to activate'
        - Get current date: 'return (current date) as text'
        - Set volume: 'set volume output volume 50'
        - Show notification: 'display notification "Hello" with title "Voice Assistant"'

    Security:
        - Dangerous patterns (shell execution, sudo) are blocked
        - Script length limited to 10000 characters
        - Execution timeout of 30 seconds
    """
    server = get_server()

    if not server.is_tool_enabled("execute_applescript"):
        return "Tool 'execute_applescript' is disabled in configuration"

    try:
        result = await server.applescript.execute(script)
        return result
    except ValidationError as e:
        logger.warning(f"AppleScript validation error: {e}")
        return f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"AppleScript execution error: {e}")
        return f"Error executing AppleScript: {str(e)}"


# Tool 2: control_application
@mcp.tool()
async def control_application(
    app_name: str, action: str, params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Control macOS applications using the Accessibility API.

    This tool allows interaction with application UI elements like clicking buttons,
    filling text fields, and reading text. Requires Accessibility permission.

    Args:
        app_name: Name of the application (e.g., "Safari", "Messages", "Finder")
        action: Action to perform:
            - "click_button": Click a button
            - "fill_field": Fill a text field
            - "get_text": Read text from application
        params: Action-specific parameters:
            - For click_button: {"button_title": "Search", "window_index": 0}
            - For fill_field: {"field_label": "Search", "text": "query", "window_index": 0}
            - For get_text: {"element_type": "title"}

    Returns:
        Action result as string, or error message if operation fails

    Examples:
        - Click Safari search button:
          app_name="Safari", action="click_button", params={"button_title": "Search"}
        - Fill search field:
          app_name="Safari", action="fill_field",
          params={"field_label": "Search", "text": "weather"}
        - Get window title:
          app_name="Safari", action="get_text", params={"element_type": "title"}

    Security:
        - Requires Accessibility permission
        - System utilities (Terminal, etc.) are blocked
        - Only works with running applications
    """
    server = get_server()

    if not server.is_tool_enabled("control_application"):
        return "Tool 'control_application' is disabled in configuration"

    if params is None:
        params = {}

    try:
        if action == "click_button":
            button_title = params.get("button_title", "")
            window_index = params.get("window_index", 0)
            result = await server.accessibility.click_button(
                app_name, button_title, window_index
            )
            return result

        elif action == "fill_field":
            field_label = params.get("field_label", "")
            text = params.get("text", "")
            window_index = params.get("window_index", 0)
            result = await server.accessibility.fill_field(
                app_name, field_label, text, window_index
            )
            return result

        elif action == "get_text":
            element_type = params.get("element_type", "text")
            result = await server.accessibility.get_text(app_name, element_type)
            return result

        else:
            return f"Unknown action: {action}. Valid actions: click_button, fill_field, get_text"

    except ValidationError as e:
        logger.warning(f"Accessibility validation error: {e}")
        return f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Accessibility control error: {e}")
        return f"Error controlling application: {str(e)}"


# Tool 3: file_operation
@mcp.tool()
async def file_operation(
    operation: str, path: str, content: Optional[str] = None, **kwargs: Any
) -> str:
    """
    Perform file system operations.

    This tool allows reading, writing, listing, deleting, moving, and copying files
    and directories. All operations are sandboxed to the user's home directory.

    Args:
        operation: Operation type:
            - "read": Read file contents
            - "write": Write content to file
            - "list": List directory contents
            - "delete": Delete file or directory
            - "move": Move file or directory
            - "copy": Copy file or directory
        path: File or directory path (supports ~ expansion)
        content: Content for write operations
        **kwargs: Additional parameters:
            - For write: overwrite=True/False
            - For list: include_hidden=True/False
            - For delete: recursive=True/False
            - For move/copy: destination="path"

    Returns:
        Operation result as string, or error message if operation fails

    Examples:
        - Read file: operation="read", path="~/Documents/notes.txt"
        - Write file: operation="write", path="~/Documents/todo.txt",
          content="Buy groceries", overwrite=True
        - List directory: operation="list", path="~/Downloads"
        - Delete file: operation="delete", path="~/Documents/old.txt"
        - Move file: operation="move", path="~/Downloads/file.pdf",
          destination="~/Documents/file.pdf"

    Security:
        - Operations restricted to home directory
        - System paths (/System, /Library, etc.) are blocked
        - Sensitive directories (~/.ssh, etc.) are blocked
        - File size limit: 10MB for read operations
    """
    server = get_server()

    if not server.is_tool_enabled("file_operation"):
        return "Tool 'file_operation' is disabled in configuration"

    try:
        if operation == "read":
            max_size_mb = kwargs.get("max_size_mb", 10)
            result = await server.file_ops.read(path, max_size_mb)
            return result

        elif operation == "write":
            if content is None:
                return "Error: 'content' parameter required for write operation"
            overwrite = kwargs.get("overwrite", False)
            result = await server.file_ops.write(path, content, overwrite)
            return result

        elif operation == "list":
            include_hidden = kwargs.get("include_hidden", False)
            result = await server.file_ops.list_directory(path, include_hidden)
            return result

        elif operation == "delete":
            recursive = kwargs.get("recursive", False)
            result = await server.file_ops.delete(path, recursive)
            return result

        elif operation == "move":
            destination = kwargs.get("destination")
            if not destination:
                return "Error: 'destination' parameter required for move operation"
            result = await server.file_ops.move(path, destination)
            return result

        elif operation == "copy":
            destination = kwargs.get("destination")
            if not destination:
                return "Error: 'destination' parameter required for copy operation"
            result = await server.file_ops.copy(path, destination)
            return result

        else:
            return (
                f"Unknown operation: {operation}. "
                f"Valid operations: read, write, list, delete, move, copy"
            )

    except ValidationError as e:
        logger.warning(f"File operation validation error: {e}")
        return f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"File operation error: {e}")
        return f"Error performing file operation: {str(e)}"


# Tool 4: send_message
@mcp.tool()
async def send_message(
    recipient: str, message: str, platform: str = "imessage"
) -> str:
    """
    Send message via Messages app (iMessage or SMS).

    This tool sends messages through the macOS Messages app. By default, requires
    user confirmation before sending for security.

    Args:
        recipient: Phone number (e.g., "+1234567890") or contact name
        message: Message text to send (max 1000 characters)
        platform: Message platform - "imessage" or "sms" (both use Messages app)

    Returns:
        Success message or confirmation request, or error message if operation fails

    Examples:
        - Send iMessage: recipient="+1234567890",
          message="Hello from Voice Assistant!"
        - Send to contact: recipient="John Doe",
          message="Meeting at 3pm"

    Security:
        - Requires user confirmation by default (configurable)
        - Contact whitelist support (optional)
        - Message length limited to 1000 characters
        - Validates phone number format

    Note:
        - Messages app must be running
        - Requires Full Disk Access for reading messages
        - Sending works without Full Disk Access
    """
    server = get_server()

    if not server.is_tool_enabled("send_message"):
        return "Tool 'send_message' is disabled in configuration"

    try:
        result = await server.messages.send_message(recipient, message, platform)
        return result

    except ValidationError as e:
        logger.warning(f"Message validation error: {e}")
        return f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Message sending error: {e}")
        return f"Error sending message: {str(e)}"


# Tool 5: web_search
@mcp.tool()
async def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web and return summarized results.

    This tool performs web searches using DuckDuckGo and returns formatted results
    with titles, descriptions, and URLs.

    Args:
        query: Search query (max 500 characters)
        num_results: Number of results to return (default: 5, max: 10)

    Returns:
        Formatted search results with titles, descriptions, and URLs,
        or error message if search fails

    Examples:
        - Search news: query="latest macOS features", num_results=5
        - Search definition: query="what is machine learning"
        - Search local: query="restaurants near me"

    Security:
        - Query length limited to 500 characters
        - Uses privacy-focused DuckDuckGo search
        - Search timeout: 10 seconds
        - No tracking or data collection

    Note:
        - Requires internet connection
        - Results are from DuckDuckGo
        - Results are summarized for voice consumption
    """
    server = get_server()

    if not server.is_tool_enabled("web_search"):
        return "Tool 'web_search' is disabled in configuration"

    # Clamp num_results
    num_results = max(1, min(10, num_results))

    try:
        result = await server.web_search.search(query, num_results)
        return result

    except ValidationError as e:
        logger.warning(f"Web search validation error: {e}")
        return f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Error searching web: {str(e)}"


# Tool 6: get_system_info
@mcp.tool()
async def get_system_info(info_type: str = "summary") -> str:
    """
    Get macOS system information and status.

    This tool retrieves various system information including battery status,
    disk usage, memory usage, CPU usage, network status, and running applications.

    Args:
        info_type: Type of information to retrieve:
            - "battery": Battery status and charge level
            - "disk": Disk usage and available space
            - "memory": RAM usage and availability
            - "cpu": CPU usage and core count
            - "network": Network interfaces and IP addresses
            - "apps": Running applications with resource usage
            - "datetime": Current date and time
            - "system": System information (OS version, architecture)
            - "summary": All of the above (default)

    Returns:
        Formatted system information, or error message if query fails

    Examples:
        - Get battery: info_type="battery"
        - Get disk space: info_type="disk"
        - Get all info: info_type="summary"
        - Get time: info_type="datetime"

    Security:
        - Read-only operations
        - No sensitive information exposed
        - No system modification capabilities

    Note:
        - Battery info only available on laptops
        - Some info may require permissions
        - Resource usage values are snapshots
    """
    server = get_server()

    if not server.is_tool_enabled("get_system_info"):
        return "Tool 'get_system_info' is disabled in configuration"

    try:
        if info_type == "battery":
            return await SystemInfo.get_battery_status()

        elif info_type == "disk":
            return await SystemInfo.get_disk_usage()

        elif info_type == "memory":
            return await SystemInfo.get_memory_usage()

        elif info_type == "cpu":
            return await SystemInfo.get_cpu_usage()

        elif info_type == "network":
            return await SystemInfo.get_network_status()

        elif info_type == "apps":
            return await SystemInfo.get_running_apps()

        elif info_type == "datetime":
            return await SystemInfo.get_datetime()

        elif info_type == "system":
            return await SystemInfo.get_system_info()

        elif info_type == "summary":
            # Get all information
            results = []
            results.append(await SystemInfo.get_datetime())
            results.append(await SystemInfo.get_system_info())
            results.append(await SystemInfo.get_battery_status())
            results.append(await SystemInfo.get_cpu_usage())
            results.append(await SystemInfo.get_memory_usage())
            results.append(await SystemInfo.get_disk_usage())

            return "\n\n".join(results)

        else:
            return (
                f"Unknown info_type: {info_type}. Valid types: "
                f"battery, disk, memory, cpu, network, apps, datetime, system, summary"
            )

    except Exception as e:
        logger.error(f"System info error: {e}")
        return f"Error getting system info: {str(e)}"


# Server management functions
def start_server(host: str = "localhost", port: int = 8765) -> None:
    """
    Start the MCP server

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info(f"Starting MCP server on {host}:{port}")
    get_server()  # Initialize server
    mcp.run(transport="stdio")  # FastMCP uses stdio by default


if __name__ == "__main__":
    # Initialize logging
    logger.add(
        "/tmp/voice-assistant/logs/mcp-server.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
    )

    # Start server
    start_server()

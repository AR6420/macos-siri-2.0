"""
MCP (Model Context Protocol) Server Module

Provides macOS automation tools via FastMCP 2.0 server:
- AppleScript execution
- Accessibility API control
- File operations
- Message sending
- Web search
- System information queries
"""

from .server import MCPServer, get_server, mcp, start_server
from .tools import (
    AccessibilityController,
    AppleScriptExecutor,
    AppleScriptTemplates,
    FileOperations,
    MessagesAutomation,
    SystemInfo,
    WebSearch,
)
from .validation import ToolValidator, ValidationError, validate_permissions

__all__ = [
    # Server
    "MCPServer",
    "get_server",
    "start_server",
    "mcp",
    # Tools
    "AppleScriptExecutor",
    "AppleScriptTemplates",
    "AccessibilityController",
    "FileOperations",
    "MessagesAutomation",
    "SystemInfo",
    "WebSearch",
    # Validation
    "ToolValidator",
    "ValidationError",
    "validate_permissions",
]

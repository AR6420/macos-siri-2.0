"""
MCP Tools Module

Exports all MCP automation tools for use by the FastMCP server.
"""

from .accessibility import AccessibilityController, AccessibilityError
from .applescript import (
    AppleScriptError,
    AppleScriptExecutor,
    AppleScriptTemplates,
)
from .files import FileOperationError, FileOperations
from .messages import MessagesAutomation, MessagesError
from .system import SystemError, SystemInfo, WebSearch, WebSearchError

__all__ = [
    # AppleScript
    "AppleScriptExecutor",
    "AppleScriptTemplates",
    "AppleScriptError",
    # Accessibility
    "AccessibilityController",
    "AccessibilityError",
    # Files
    "FileOperations",
    "FileOperationError",
    # Messages
    "MessagesAutomation",
    "MessagesError",
    # System & Web Search
    "SystemInfo",
    "WebSearch",
    "SystemError",
    "WebSearchError",
]

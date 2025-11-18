"""
MCP Tool Validation & Safety Checks

Provides security validation and safety checks for all MCP tools to ensure
they operate within safe boundaries and respect user permissions.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger


class ValidationError(Exception):
    """Raised when tool validation fails"""

    pass


class ToolValidator:
    """Validates and sanitizes tool inputs for security"""

    # Dangerous AppleScript patterns
    DANGEROUS_APPLESCRIPT_PATTERNS = [
        r"do\s+shell\s+script",  # Shell execution
        r"system\s+events",  # System manipulation (partially blocked)
        r"administrator\s+privileges",  # Privilege escalation
        r"sudo",  # Sudo attempts
        r"rm\s+-rf",  # Destructive file operations
        r"format\s+volume",  # Disk formatting
    ]

    # System paths that should never be accessed
    BLOCKED_PATHS = [
        "/System",
        "/Library",
        "/private",
        "/usr",
        "/bin",
        "/sbin",
        "/var",
        "/.ssh",
        "/.gnupg",
        "/Applications/Utilities",
    ]

    # Allowed home directory paths
    ALLOWED_HOME_DIRS = [
        "~/Documents",
        "~/Downloads",
        "~/Desktop",
        "~/Pictures",
        "~/Music",
        "~/Videos",
        "~/Movies",
    ]

    @classmethod
    def validate_applescript(cls, script: str) -> Tuple[bool, Optional[str]]:
        """
        Validate AppleScript for dangerous patterns

        Args:
            script: AppleScript code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        script_lower = script.lower()

        for pattern in cls.DANGEROUS_APPLESCRIPT_PATTERNS:
            if re.search(pattern, script_lower, re.IGNORECASE):
                return False, f"Potentially dangerous pattern detected: {pattern}"

        # Check for excessive length
        if len(script) > 10000:
            return False, "AppleScript exceeds maximum length (10000 characters)"

        return True, None

    @classmethod
    def validate_file_path(
        cls, path: str, operation: str = "read", config: Optional[dict] = None
    ) -> Tuple[bool, Optional[str], Path]:
        """
        Validate file path for safety

        Args:
            path: File path to validate
            operation: Operation type (read, write, delete, etc.)
            config: Optional configuration override

        Returns:
            Tuple of (is_valid, error_message, resolved_path)
        """
        try:
            # Expand user path
            expanded_path = os.path.expanduser(path)
            resolved_path = Path(expanded_path).resolve()

            # Check if path is blocked
            path_str = str(resolved_path)
            for blocked in cls.BLOCKED_PATHS:
                if path_str.startswith(blocked):
                    return False, f"Access to {blocked} is blocked for security", resolved_path

            # For write/delete operations, must be in home directory
            if operation in ["write", "delete", "move", "copy"]:
                home_dir = str(Path.home())
                if not path_str.startswith(home_dir):
                    return (
                        False,
                        f"{operation} operations only allowed in home directory",
                        resolved_path,
                    )

            # Check allowed paths from config
            if config and "allowed_paths" in config:
                allowed = False
                for allowed_path in config["allowed_paths"]:
                    expanded_allowed = os.path.expanduser(allowed_path)
                    if path_str.startswith(expanded_allowed):
                        allowed = True
                        break

                if not allowed:
                    return (
                        False,
                        f"Path not in allowed directories: {config['allowed_paths']}",
                        resolved_path,
                    )

            # Check blocked paths from config
            if config and "blocked_paths" in config:
                for blocked_path in config["blocked_paths"]:
                    expanded_blocked = os.path.expanduser(blocked_path)
                    if path_str.startswith(expanded_blocked):
                        return False, f"Path is explicitly blocked: {blocked_path}", resolved_path

            return True, None, resolved_path

        except Exception as e:
            return False, f"Invalid path: {str(e)}", Path()

    @classmethod
    def validate_contact(
        cls, recipient: str, config: Optional[dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate message recipient

        Args:
            recipient: Phone number or contact name
            config: Optional configuration with allowed contacts

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not recipient or not recipient.strip():
            return False, "Recipient cannot be empty"

        # If allowed_contacts is configured and not empty, check whitelist
        if config and "allowed_contacts" in config:
            allowed = config["allowed_contacts"]
            if allowed and recipient not in allowed:
                return False, f"Recipient not in allowed contacts list"

        # Basic validation for phone numbers
        if re.match(r"^\+?\d[\d\s\-\(\)]+$", recipient):
            # Looks like a phone number
            digits = re.sub(r"\D", "", recipient)
            if len(digits) < 10 or len(digits) > 15:
                return False, "Invalid phone number format"

        return True, None

    @classmethod
    def validate_message_content(cls, message: str) -> Tuple[bool, Optional[str]]:
        """
        Validate message content

        Args:
            message: Message text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message or not message.strip():
            return False, "Message cannot be empty"

        if len(message) > 1000:
            return False, "Message exceeds maximum length (1000 characters)"

        return True, None

    @classmethod
    def validate_web_query(cls, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate web search query

        Args:
            query: Search query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Search query cannot be empty"

        if len(query) > 500:
            return False, "Search query exceeds maximum length (500 characters)"

        return True, None

    @classmethod
    def sanitize_output(cls, output: str, max_length: int = 5000) -> str:
        """
        Sanitize tool output for LLM consumption

        Args:
            output: Raw output from tool
            max_length: Maximum output length

        Returns:
            Sanitized output string
        """
        if not output:
            return ""

        # Truncate if too long
        if len(output) > max_length:
            output = output[:max_length] + "\n... (output truncated)"

        # Remove any null bytes
        output = output.replace("\x00", "")

        return output

    @classmethod
    def validate_app_name(cls, app_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate application name

        Args:
            app_name: Application name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not app_name or not app_name.strip():
            return False, "Application name cannot be empty"

        # Basic sanitization - no path separators
        if "/" in app_name or "\\" in app_name:
            return False, "Invalid application name"

        # Block system utilities
        blocked_apps = ["Terminal", "Activity Monitor", "System Preferences", "System Settings"]
        if app_name in blocked_apps:
            return False, f"Access to {app_name} is restricted for security"

        return True, None


def validate_permissions(required_permissions: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if required macOS permissions are granted

    Args:
        required_permissions: List of permission types to check

    Returns:
        Tuple of (all_granted, missing_permissions)
    """
    missing = []

    # Note: Actual permission checking would use PyObjC to query TCC database
    # This is a placeholder that would be implemented with platform-specific code

    for permission in required_permissions:
        # Placeholder - in real implementation, check actual permissions
        # from ApplicationServices import AXIsProcessTrusted
        # if permission == "accessibility" and not AXIsProcessTrusted():
        #     missing.append(permission)
        logger.debug(f"Permission check for {permission} - would check actual status on macOS")

    return len(missing) == 0, missing

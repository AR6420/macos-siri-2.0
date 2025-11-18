"""
Tests for MCP validation module
"""

import pytest

from voice_assistant.mcp.validation import ToolValidator


class TestToolValidator:
    """Test ToolValidator class"""

    def test_validate_applescript_safe(self):
        """Test that safe AppleScript passes validation"""
        script = 'tell application "Safari" to activate'
        is_valid, error_msg = ToolValidator.validate_applescript(script)

        assert is_valid is True
        assert error_msg is None

    def test_validate_applescript_dangerous_shell(self):
        """Test that shell script execution is blocked"""
        script = 'do shell script "rm -rf /"'
        is_valid, error_msg = ToolValidator.validate_applescript(script)

        assert is_valid is False
        assert "dangerous pattern" in error_msg.lower()

    def test_validate_applescript_sudo(self):
        """Test that sudo attempts are blocked"""
        script = 'do shell script "sudo systemsetup"'
        is_valid, error_msg = ToolValidator.validate_applescript(script)

        assert is_valid is False
        assert "dangerous pattern" in error_msg.lower()

    def test_validate_applescript_too_long(self):
        """Test that overly long scripts are rejected"""
        script = "a" * 10001
        is_valid, error_msg = ToolValidator.validate_applescript(script)

        assert is_valid is False
        assert "maximum length" in error_msg.lower()

    def test_validate_file_path_home_directory(self):
        """Test that home directory paths are allowed"""
        is_valid, error_msg, resolved = ToolValidator.validate_file_path(
            "~/Documents/test.txt", operation="read"
        )

        assert is_valid is True
        assert error_msg is None
        assert "Documents" in str(resolved)

    def test_validate_file_path_system_blocked(self):
        """Test that system paths are blocked"""
        is_valid, error_msg, resolved = ToolValidator.validate_file_path(
            "/System/Library/test.txt", operation="read"
        )

        assert is_valid is False
        assert "blocked" in error_msg.lower()

    def test_validate_file_path_ssh_blocked(self):
        """Test that .ssh directory is blocked"""
        is_valid, error_msg, resolved = ToolValidator.validate_file_path(
            "~/.ssh/id_rsa", operation="read"
        )

        assert is_valid is False
        assert "blocked" in error_msg.lower()

    def test_validate_contact_phone_valid(self):
        """Test that valid phone numbers pass validation"""
        is_valid, error_msg = ToolValidator.validate_contact("+1234567890")

        assert is_valid is True
        assert error_msg is None

    def test_validate_contact_empty(self):
        """Test that empty contacts are rejected"""
        is_valid, error_msg = ToolValidator.validate_contact("")

        assert is_valid is False
        assert "empty" in error_msg.lower()

    def test_validate_message_content_valid(self):
        """Test that valid messages pass validation"""
        is_valid, error_msg = ToolValidator.validate_message_content("Hello, world!")

        assert is_valid is True
        assert error_msg is None

    def test_validate_message_content_empty(self):
        """Test that empty messages are rejected"""
        is_valid, error_msg = ToolValidator.validate_message_content("")

        assert is_valid is False
        assert "empty" in error_msg.lower()

    def test_validate_message_content_too_long(self):
        """Test that overly long messages are rejected"""
        message = "a" * 1001
        is_valid, error_msg = ToolValidator.validate_message_content(message)

        assert is_valid is False
        assert "maximum length" in error_msg.lower()

    def test_validate_web_query_valid(self):
        """Test that valid queries pass validation"""
        is_valid, error_msg = ToolValidator.validate_web_query("macOS features")

        assert is_valid is True
        assert error_msg is None

    def test_validate_web_query_empty(self):
        """Test that empty queries are rejected"""
        is_valid, error_msg = ToolValidator.validate_web_query("")

        assert is_valid is False
        assert "empty" in error_msg.lower()

    def test_sanitize_output(self):
        """Test output sanitization"""
        output = "Normal output"
        sanitized = ToolValidator.sanitize_output(output)

        assert sanitized == output

    def test_sanitize_output_truncation(self):
        """Test that long output is truncated"""
        output = "a" * 6000
        sanitized = ToolValidator.sanitize_output(output, max_length=1000)

        assert len(sanitized) <= 1020  # Including truncation message
        assert "truncated" in sanitized

    def test_validate_app_name_valid(self):
        """Test that valid app names pass validation"""
        is_valid, error_msg = ToolValidator.validate_app_name("Safari")

        assert is_valid is True
        assert error_msg is None

    def test_validate_app_name_blocked(self):
        """Test that system apps are blocked"""
        is_valid, error_msg = ToolValidator.validate_app_name("Terminal")

        assert is_valid is False
        assert "restricted" in error_msg.lower()

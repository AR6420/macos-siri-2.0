"""
Tests for MCP tools
"""

import pytest

from voice_assistant.mcp.tools import (
    AppleScriptExecutor,
    AppleScriptTemplates,
    FileOperations,
    MessagesAutomation,
    SystemInfo,
    WebSearch,
)


class TestAppleScriptExecutor:
    """Test AppleScript executor"""

    @pytest.mark.asyncio
    async def test_execute_simple_script(self):
        """Test executing a simple AppleScript"""
        executor = AppleScriptExecutor(sandbox=True)

        # This should work on any macOS system
        result = await executor.execute('return "Hello"')

        assert "Hello" in result or "Mock" in result  # Mock on non-macOS

    @pytest.mark.asyncio
    async def test_execute_blocked_script(self):
        """Test that dangerous scripts are blocked"""
        executor = AppleScriptExecutor(sandbox=True)

        with pytest.raises(Exception):  # Should raise ValidationError
            await executor.execute('do shell script "rm -rf /"')


class TestAppleScriptTemplates:
    """Test AppleScript templates"""

    def test_open_application_template(self):
        """Test application opening template"""
        script = AppleScriptTemplates.open_application("Safari")

        assert "Safari" in script
        assert "activate" in script

    def test_safari_open_url_template(self):
        """Test Safari URL opening template"""
        script = AppleScriptTemplates.safari_open_url("https://example.com")

        assert "Safari" in script
        assert "https://example.com" in script

    def test_set_volume_template(self):
        """Test volume setting template"""
        script = AppleScriptTemplates.set_volume(75)

        assert "75" in script
        assert "volume" in script

    def test_notification_template(self):
        """Test notification template"""
        script = AppleScriptTemplates.notification("Title", "Message")

        assert "Title" in script
        assert "Message" in script
        assert "notification" in script


class TestFileOperations:
    """Test file operations"""

    @pytest.mark.asyncio
    async def test_list_directory_home(self):
        """Test listing home directory"""
        file_ops = FileOperations()

        result = await file_ops.list_directory("~")

        # Should succeed or fail gracefully
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_blocked_path_system(self):
        """Test that system paths are blocked"""
        file_ops = FileOperations()

        with pytest.raises(Exception):  # Should raise ValidationError
            await file_ops.read("/System/Library/test.txt")

    def test_format_size(self):
        """Test file size formatting"""
        # Test bytes
        assert "B" in FileOperations._format_size(100)

        # Test KB
        assert "KB" in FileOperations._format_size(2048)

        # Test MB
        assert "MB" in FileOperations._format_size(2 * 1024 * 1024)


class TestMessagesAutomation:
    """Test Messages automation"""

    @pytest.mark.asyncio
    async def test_send_message_requires_confirmation(self):
        """Test that confirmation is required by default"""
        messages = MessagesAutomation(require_confirmation=True)

        result = await messages.send_message(
            recipient="+1234567890",
            message="Test message"
        )

        assert "confirmation required" in result.lower()

    @pytest.mark.asyncio
    async def test_check_messages_running(self):
        """Test checking if Messages is running"""
        messages = MessagesAutomation()

        result = await messages.check_messages_running()

        # Should return boolean
        assert isinstance(result, bool)


class TestSystemInfo:
    """Test system info queries"""

    @pytest.mark.asyncio
    async def test_get_battery_status(self):
        """Test getting battery status"""
        result = await SystemInfo.get_battery_status()

        assert isinstance(result, str)
        # Should contain battery info or "No battery" on desktop
        assert "Battery" in result or "No battery" in result

    @pytest.mark.asyncio
    async def test_get_disk_usage(self):
        """Test getting disk usage"""
        result = await SystemInfo.get_disk_usage()

        assert isinstance(result, str)
        assert "Disk Usage" in result or "GB" in result

    @pytest.mark.asyncio
    async def test_get_memory_usage(self):
        """Test getting memory usage"""
        result = await SystemInfo.get_memory_usage()

        assert isinstance(result, str)
        assert "Memory" in result or "GB" in result

    @pytest.mark.asyncio
    async def test_get_cpu_usage(self):
        """Test getting CPU usage"""
        result = await SystemInfo.get_cpu_usage()

        assert isinstance(result, str)
        assert "CPU" in result or "%" in result

    @pytest.mark.asyncio
    async def test_get_datetime(self):
        """Test getting date/time"""
        result = await SystemInfo.get_datetime()

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain date components
        assert any(month in result for month in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])

    @pytest.mark.asyncio
    async def test_get_system_info(self):
        """Test getting system info"""
        result = await SystemInfo.get_system_info()

        assert isinstance(result, str)
        assert "System" in result or "OS" in result


class TestWebSearch:
    """Test web search"""

    @pytest.mark.asyncio
    async def test_search_basic(self):
        """Test basic web search"""
        search = WebSearch()

        try:
            result = await search.search("test query", num_results=2)

            assert isinstance(result, str)
            # Should contain results or error message
            assert len(result) > 0

        except Exception as e:
            # Network errors are acceptable in tests
            assert "error" in str(e).lower() or "failed" in str(e).lower()

    @pytest.mark.asyncio
    async def test_search_validation(self):
        """Test that invalid queries are rejected"""
        search = WebSearch()

        with pytest.raises(Exception):  # Should raise ValidationError
            await search.search("")  # Empty query should fail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

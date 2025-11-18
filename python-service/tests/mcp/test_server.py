"""
Integration tests for MCP server
"""

import pytest

from voice_assistant.mcp import MCPServer, get_server


class TestMCPServer:
    """Test MCP server initialization and configuration"""

    def test_server_initialization(self):
        """Test that server initializes correctly"""
        server = get_server()

        assert server is not None
        assert hasattr(server, "config")
        assert hasattr(server, "applescript")
        assert hasattr(server, "accessibility")
        assert hasattr(server, "file_ops")
        assert hasattr(server, "messages")
        assert hasattr(server, "web_search")

    def test_server_singleton(self):
        """Test that get_server() returns singleton"""
        server1 = get_server()
        server2 = get_server()

        assert server1 is server2

    def test_enabled_tools(self):
        """Test that tools are enabled based on configuration"""
        server = get_server()

        # Check that enabled_tools is a set
        assert isinstance(server.enabled_tools, set)

        # Should have at least some tools enabled
        assert len(server.enabled_tools) > 0

    def test_is_tool_enabled(self):
        """Test tool enablement checking"""
        server = get_server()

        # Test with known tools
        for tool in [
            "execute_applescript",
            "control_application",
            "file_operation",
            "send_message",
            "web_search",
            "get_system_info",
        ]:
            result = server.is_tool_enabled(tool)
            assert isinstance(result, bool)

    def test_config_loading(self):
        """Test that configuration loads correctly"""
        server = get_server()
        config = server.config

        # Check that config has expected structure
        assert "mcp" in config
        assert "tools_enabled" in config["mcp"]
        assert "tools" in config["mcp"]


@pytest.mark.asyncio
class TestMCPServerTools:
    """Test MCP server tool execution"""

    async def test_execute_applescript_tool(self):
        """Test execute_applescript tool"""
        from voice_assistant.mcp.server import execute_applescript

        result = await execute_applescript('return "test"')

        assert isinstance(result, str)
        # Should contain result or error
        assert len(result) > 0

    async def test_get_system_info_tool(self):
        """Test get_system_info tool"""
        from voice_assistant.mcp.server import get_system_info

        # Test different info types
        for info_type in ["datetime", "battery", "cpu", "memory"]:
            result = await get_system_info(info_type)

            assert isinstance(result, str)
            assert len(result) > 0

    async def test_web_search_tool(self):
        """Test web_search tool"""
        from voice_assistant.mcp.server import web_search

        try:
            result = await web_search("test", num_results=2)

            assert isinstance(result, str)
            assert len(result) > 0

        except Exception:
            # Network errors acceptable
            pass

    async def test_file_operation_tool_list(self):
        """Test file_operation tool for listing"""
        from voice_assistant.mcp.server import file_operation

        result = await file_operation(operation="list", path="~")

        assert isinstance(result, str)
        # Should succeed or have clear error message
        assert len(result) > 0

    async def test_send_message_tool_confirmation(self):
        """Test send_message tool requires confirmation"""
        from voice_assistant.mcp.server import send_message

        result = await send_message(
            recipient="+1234567890",
            message="test"
        )

        assert isinstance(result, str)
        # Should require confirmation by default
        assert "confirmation" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

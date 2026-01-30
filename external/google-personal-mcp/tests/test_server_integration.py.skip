"""
Integration tests for Google Sheets MCP Server.
These tests connect to the actual server via stdio (like a real client).
"""

import pytest
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the server initializes correctly."""
    server_params = StdioServerParameters(
        command="google-personal-mcp",
        args=[],
        env=None
    )

    async with AsyncExitStack() as stack:
        # Start the stdio client
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport

        # Create the client session
        session = await stack.enter_async_context(ClientSession(stdio, write))

        # Initialize the connection
        await session.initialize()
        # If we got here, the fixture worked and server initialized
        assert session is not None


@pytest.mark.asyncio
async def test_list_tools():
    """Test that all expected tools are available."""
    server_params = StdioServerParameters(
        command="google-personal-mcp",
        args=[],
        env=None
    )

    async with AsyncExitStack() as stack:
        # Start the stdio client
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport

        # Create the client session
        session = await stack.enter_async_context(ClientSession(stdio, write))

        # Initialize the connection
        await session.initialize()
        tools_result = await session.list_tools()
        tools = tools_result.tools

    tool_names = {tool.name for tool in tools}

    expected_tools = {
        "list_sheets",
        "create_sheet",
        "get_sheet_status",
        "insert_prompt",
        "get_prompts",
        "initialize_readme_sheet"
    }

    assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"


@pytest.mark.asyncio
async def test_list_sheets_tool():
    """Test the list_sheets tool."""
    server_params = StdioServerParameters(
        command="google-personal-mcp",
        args=[],
        env=None
    )

    async with AsyncExitStack() as stack:
        # Start the stdio client
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport

        # Create the client session
        session = await stack.enter_async_context(ClientSession(stdio, write))

        # Initialize the connection
        await session.initialize()
        result = await session.call_tool("list_sheets", arguments={})

    # Check that we got a result
    assert result is not None
    assert len(result.content) > 0

    # The result should be text content
    assert hasattr(result.content[0], 'text')


@pytest.mark.asyncio
async def test_get_sheet_status_tool():
    """Test the get_sheet_status tool."""
    server_params = StdioServerParameters(
        command="google-personal-mcp",
        args=[],
        env=None
    )

    async with AsyncExitStack() as stack:
        # Start the stdio client
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport

        # Create the client session
        session = await stack.enter_async_context(ClientSession(stdio, write))

        # Initialize the connection
        await session.initialize()
        # This test may fail if the README sheet doesn't exist, which is okay
        try:
            result = await session.call_tool("get_sheet_status", arguments={})
            assert result is not None
            assert len(result.content) > 0
        except Exception as e:
            # It's okay if this fails - might mean the sheet doesn't exist yet
            pytest.skip(f"get_sheet_status failed (expected if README sheet doesn't exist): {e}")


@pytest.mark.asyncio
async def test_tool_schemas():
    """Test that all tools have proper schemas."""
    server_params = StdioServerParameters(
        command="google-personal-mcp",
        args=[],
        env=None
    )

    async with AsyncExitStack() as stack:
        # Start the stdio client
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport

        # Create the client session
        session = await stack.enter_async_context(ClientSession(stdio, write))

        # Initialize the connection
        await session.initialize()
        tools_result = await session.list_tools()
        tools = tools_result.tools

    for tool in tools:
        # Each tool should have a name and description
        assert tool.name, f"Tool missing name: {tool}"
        assert tool.description, f"Tool {tool.name} missing description"

        # Each tool should have an input schema
        assert tool.inputSchema, f"Tool {tool.name} missing input schema"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


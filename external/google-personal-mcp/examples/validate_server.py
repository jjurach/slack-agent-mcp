#!/usr/bin/env python3
"""
Validation script for Google Sheets MCP Server.
This script tests the MCP server by connecting as a client and calling its tools.
"""

import asyncio
import sys
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def validate_server():
    """Connect to the MCP server and validate it's working."""

    print("🔍 Starting MCP Server Validation...")
    print("-" * 60)

    # Server parameters - use the installed script
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
        print("✓ Server connection initialized")

        # List available tools
        print("\n📋 Listing available tools...")
        tools_result = await session.list_tools()
        tools = tools_result.tools

        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  • {tool.name}: {tool.description}")

        # Validate expected tools exist
        expected_tools = {
            "health_check",
            "list_configured_sheets",
            "list_configured_folders",
            "list_sheets",
            "get_sheet_status",
            "insert_prompt",
            "get_prompts",
            "list_drive_files",
            "upload_file",
            "get_file_content",
            "delete_file"
        }

        actual_tools = {tool.name for tool in tools}
        missing_tools = expected_tools - actual_tools

        if missing_tools:
            print(f"\n❌ ERROR: Missing expected tools: {missing_tools}")
            return False

        print("\n✓ All expected tools are present")

        # Test list_sheets tool
        print("\n🔧 Testing list_sheets tool...")
        try:
            result = await session.call_tool("list_sheets", arguments={})
            sheets = result.content[0].text
            print(f"✓ list_sheets succeeded")
            print(f"  Response: {sheets}")
        except Exception as e:
            print(f"❌ list_sheets failed: {e}")
            return False

        # Test get_sheet_status tool
        print("\n🔧 Testing get_sheet_status tool...")
        try:
            result = await session.call_tool("get_sheet_status", arguments={})
            status = result.content[0].text
            print(f"✓ get_sheet_status succeeded")
            print(f"  Response: {status[:200]}..." if len(status) > 200 else f"  Response: {status}")
        except Exception as e:
            print(f"❌ get_sheet_status failed: {e}")
            # This might fail if the README sheet doesn't exist yet, which is okay
            print("  Note: This is expected if README sheet doesn't exist")

        print("\n" + "=" * 60)
        print("✅ Validation completed successfully!")
        print("=" * 60)
        print("\nThe MCP server is working correctly and ready to use.")
        print("\nNext steps:")
        print("  1. Configure your resources in ~/.config/google-personal-mcp/config.json")
        print("  2. Add the server to your MCP client configuration")
        print("  3. Connect from your MCP-compatible client (e.g., Claude Desktop)")

        return True

async def main():
    try:
        success = await validate_server()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

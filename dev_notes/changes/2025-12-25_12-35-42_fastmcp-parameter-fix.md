# Trivial Change: FastMCP Parameter Fix

**Date:** 2025-12-25 12:35:42
**Type:** Trivial Bug Fix
**Status:** Completed

## Change Made
Fixed FastMCP constructor parameter from `description` to `instructions` to match FastMCP v2.x API.

## Files Modified
- `src/slack_notifications/mcp_server.py` - Changed parameter name in FastMCP instantiation
- `tests/test_mcp_server.py` - Updated test expectation to match new parameter name

## Notes
FastMCP v2.14.1 uses `instructions` parameter instead of `description`. This fixes the TypeError that prevented the MCP server from starting.
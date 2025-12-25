# Project Plan: Slack Agent MCP Extensions

**Date:** 2025-12-25_10-52-29
**Estimated Duration:** 10-14 hours
**Complexity:** High
**Status:** Completed

## Objective
Extend the slack-agent project in two directions: (1) Add FastMCP module and implement an MCP service allowing AI agents to send descriptive messages to selected Slack channels, and (2) Create a slack-agent script that connects to Slack using RTM, runs in foreground, outputs timestamped interactions to stdout, and can answer "what time is it?" by citing local CST time.

## Requirements
- [ ] Research and integrate FastMCP framework (v2.0, actively maintained Python MCP framework)
- [ ] Set up FastMCP server with Slack notification capabilities
- [ ] Implement MCP tools for AI agents to send messages to channels
- [ ] Create slack-agent script with Slack RTM connection using slack-sdk
- [ ] Implement time query response functionality (CST timezone using pytz)
- [ ] Add comprehensive timestamped stdout logging for all interactions
- [ ] Document technologies involved and setup instructions
- [ ] Document usage instructions for the slack-agent script
- [ ] Test MCP service integration with AI agents
- [ ] Test slack-agent script functionality with mocked RTM connections
- [ ] Ensure compatibility with existing slack_notifications library

## Implementation Steps
1. **Research and Install FastMCP**
   - Files to modify: requirements.txt, pyproject.toml
   - Files to create: None
   - Dependencies: fastmcp>=2.0.0,<3.0.0 (to avoid breaking changes in v3)
   - Estimated time: 1 hour
   - Status: [ ] Not Started

2. **Create MCP Server Module**
   - Files to modify: None
   - Files to create: slack_notifications/mcp_server.py
   - Dependencies: fastmcp, existing slack_notifications
   - Estimated time: 3 hours
   - Status: [ ] Not Started

3. **Implement MCP Tools for Message Sending**
   - Files to modify: slack_notifications/mcp_server.py
   - Files to create: None
   - Dependencies: Slack API integration via existing slack_notifications
   - Estimated time: 2 hours
   - Status: [ ] Not Started

4. **Add MCP Server Entry Point**
   - Files to modify: None
   - Files to create: slack_mcp_server.py (main entry point)
   - Dependencies: slack_notifications.mcp_server
   - Estimated time: 1 hour
   - Status: [ ] Not Started

5. **Create Slack Agent Script**
   - Files to modify: None
   - Files to create: slack_agent.py
   - Dependencies: slack-sdk, pytz, logging, datetime
   - Estimated time: 3 hours
   - Status: [ ] Not Started

6. **Implement Time Query Response**
   - Files to modify: slack_agent.py
   - Files to create: None
   - Dependencies: pytz for CST timezone handling
   - Estimated time: 1.5 hours
   - Status: [ ] Not Started

7. **Add Timestamped Logging System**
   - Files to modify: slack_agent.py
   - Files to create: None
   - Dependencies: logging, datetime, sys (stdout)
   - Estimated time: 1.5 hours
   - Status: [ ] Not Started

8. **Create Documentation for MCP Service**
   - Files to modify: README.md
   - Files to create: doc/mcp-service-setup.md
   - Dependencies: None
   - Estimated time: 2 hours
   - Status: [ ] Not Started

9. **Create Documentation for Slack Agent**
   - Files to modify: None
   - Files to create: doc/slack-agent-usage.md
   - Dependencies: None
   - Estimated time: 1.5 hours
   - Status: [ ] Not Started

10. **Test MCP Service**
    - Files to modify: None
    - Files to create: tests/test_mcp_server.py
    - Dependencies: pytest, fastmcp client for testing
    - Estimated time: 2 hours
    - Status: [ ] Not Started

11. **Test Slack Agent Script**
    - Files to modify: None
    - Files to create: tests/test_slack_agent.py
    - Dependencies: pytest, mock slack connections
    - Estimated time: 2 hours
    - Status: [ ] Not Started

12. **Integration Testing**
    - Files to modify: None
    - Files to create: None
    - Dependencies: Manual testing of both components
    - Estimated time: 1 hour
    - Status: [ ] Not Started

## Success Criteria
- [ ] FastMCP server can be started and exposes tools for sending Slack messages
- [ ] AI agents can use MCP tools to send descriptive messages to specified channels
- [ ] Slack agent script connects to Slack via RTM and processes messages
- [ ] Script responds to "what time is it?" with accurate CST time
- [ ] All Slack interactions are logged with timestamps to stdout
- [ ] Comprehensive documentation provided for setup and usage of both components
- [ ] All unit and integration tests pass
- [ ] No breaking changes to existing slack_notifications library functionality
- [ ] Both components work independently and can be run simultaneously

## Testing Strategy
- [ ] Unit tests for MCP server tools and message sending
- [ ] Unit tests for slack agent message parsing and time responses
- [ ] Integration tests for MCP server with FastMCP client
- [ ] Mocked RTM connection tests for slack agent
- [ ] Manual testing of MCP service with AI agent integration
- [ ] Manual testing of slack agent script with test Slack workspace
- [ ] End-to-end testing of both components working together
- [ ] Documentation validation and setup verification

## Risk Assessment
- **High Risk:** FastMCP version compatibility issues - Mitigation: Pin to v2.x and test thoroughly
- **Medium Risk:** Slack RTM API deprecation or changes - Mitigation: Use official slack-sdk and monitor API status
- **Medium Risk:** Timezone handling complexity - Mitigation: Use established pytz library with comprehensive testing
- **Medium Risk:** MCP server authentication requirements - Mitigation: Research FastMCP auth patterns and implement as needed
- **Low Risk:** Documentation clarity - Mitigation: Peer review and user testing of setup instructions

## Dependencies
- [ ] fastmcp>=2.0.0,<3.0.0 (new dependency)
- [ ] pytz (for timezone handling, new dependency)
- [ ] slack-sdk>=3.25.0 (already in requirements)
- [ ] python-dotenv>=1.0.0 (already in requirements)
- [ ] pydantic>=2.5.0 (already in requirements)
- [ ] Existing slack_notifications library components

## Database Changes (if applicable)
- [ ] None required

## API Changes (if applicable)
- [ ] New MCP endpoints for AI agent integration via FastMCP tools
- [ ] Slack RTM API integration for real-time messaging in slack_agent.py
- [ ] New slack_mcp_server.py entry point for running MCP service

## Notes
- This plan extends the existing slack-notifications library with two complementary capabilities
- MCP service enables AI agents to integrate with Slack messaging via standardized protocol
- Slack agent script provides interactive bot functionality with real-time responses
- Both components leverage existing Slack integration but serve different use cases
- FastMCP v2.0 chosen for stability (v3 in development with potential breaking changes)
- Documentation should clearly separate setup for MCP service vs slack agent
- Consider adding example configurations for both components
- Ensure environment variable naming consistency with existing library
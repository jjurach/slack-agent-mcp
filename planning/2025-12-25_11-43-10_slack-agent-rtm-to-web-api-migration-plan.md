# Project Plan: Fix Slack Agent RTM to Web API Migration

**Date:** 2025-12-25 11:43:10
**Estimated Duration:** 4-6 hours
**Complexity:** Medium
**Status:** Completed

## Objective
Migrate the Slack Agent from the deprecated RTM (Real Time Messaging) API to the Web API to resolve the "not_allowed_token_type" error. The RTM API does not support bot tokens (xoxb-), while the Web API does. This will enable the bot to respond to time queries in Slack channels using polling-based message monitoring.

## Requirements
- [ ] Replace RTM client with Web API polling mechanism
- [ ] Implement channel monitoring configuration
- [ ] Maintain existing time query response functionality
- [ ] Preserve logging and error handling patterns
- [ ] Update tests to work with new architecture
- [ ] Add configuration for polling interval and monitored channels

## Implementation Steps
1. **Analyze Current RTM Implementation**
   - Files to modify: `slack_agent.py`
   - Files to create: None
   - Dependencies: None
   - Estimated time: 30 minutes
   - Status: [x] Completed

2. **Design Web API Polling Architecture**
   - Files to modify: `slack_agent.py`
   - Files to create: None
   - Dependencies: slack-sdk WebClient
   - Estimated time: 45 minutes
   - Status: [x] Completed

3. **Implement Message Polling System**
   - Files to modify: `slack_agent.py`
   - Files to create: None
   - Dependencies: conversations.history API
   - Estimated time: 2 hours
   - Status: [x] Completed

4. **Add Channel Configuration**
   - Files to modify: `slack_agent.py`, `.env.example`
   - Files to create: None
   - Dependencies: Environment variables
   - Estimated time: 30 minutes
   - Status: [x] Completed

5. **Update Logging and Error Handling**
   - Files to modify: `slack_agent.py`
   - Files to create: None
   - Dependencies: None
   - Estimated time: 30 minutes
   - Status: [x] Completed

6. **Update Unit Tests**
   - Files to modify: `tests/test_slack_agent.py`
   - Files to create: None
   - Dependencies: pytest, unittest.mock
   - Estimated time: 1.5 hours
   - Status: [x] Completed

7. **Update Documentation**
   - Files to modify: `slack_agent.py`, `README.md`
   - Files to create: None
   - Dependencies: None
   - Estimated time: 30 minutes
   - Status: [x] Completed

## Success Criteria
- [ ] Slack Agent starts without RTM connection errors
- [ ] Bot responds to "what time is it?" queries in configured channels
- [ ] All existing logging functionality preserved
- [ ] Tests pass with new implementation
- [ ] No breaking changes to public API

## Testing Strategy
- [ ] Unit tests for new polling mechanism
- [ ] Integration tests with mock Slack API responses
- [ ] Manual testing with real Slack workspace
- [ ] Load testing with multiple channels
- [ ] Error handling verification (network issues, API limits)

## Risk Assessment
- **High Risk:** Polling implementation may miss messages during polling intervals
  - **Mitigation:** Implement proper timestamp tracking and duplicate detection
- **Medium Risk:** conversations.history API rate limits
  - **Mitigation:** Implement exponential backoff and respect rate limits
- **Low Risk:** Changes to existing functionality
  - **Mitigation:** Comprehensive test coverage before/after changes

## Dependencies
- [ ] slack-sdk >= 3.0.0 (already in requirements.txt)
- [ ] Environment variable: SLACK_AGENT_CHANNELS (comma-separated channel IDs)
- [ ] Environment variable: SLACK_AGENT_POLL_INTERVAL (seconds, default 5)

## Database Changes (if applicable)
- [ ] None

## API Changes (if applicable)
- [ ] Migrate from RTM API to Web API
- [ ] Add conversations.history permission scope requirement
- [ ] Remove RTM connection scope requirement

## Notes
- RTM API deprecation is the root cause - Web API is the recommended approach
- Polling interval of 5 seconds provides near real-time responsiveness
- Bot will need "channels:history" OAuth scope for private channels
- Implementation will maintain backward compatibility with existing environment variables
- Consider future migration to Events API with webhooks for truly real-time operation
# Project Workflows

This document describes development workflows specific to the Slack Notifications project.

## Core Agent Workflow

All AI agents working on this project must follow the **A-E workflow** defined in [AGENTS.md](../AGENTS.md):

- **A: Analyze** - Understand the request and declare intent
- **B: Build** - Create project plan
- **C: Code** - Implement the plan
- **D: Document** - Update documentation
- **E: Evaluate** - Verify against Definition of Done

For complete workflow documentation, see the [Agent Kernel Workflows](system-prompts/workflows/README.md).

## Project-Specific Workflows

### Testing Workflow

Always run tests before committing any changes.

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=slack_notifications

# Run integration tests (requires SLACK_TEST_BOT_TOKEN)
pytest tests/integration/
```

### Documentation Workflow

When adding new features:
1. Update `src/` code with type hints and docstrings.
2. Update `docs/architecture.md` if the design changed.
3. Add implementation examples to `docs/implementation-reference.md`.
4. Create a change log in `dev_notes/changes/`.

### MCP Tool Development Workflow

When adding a new MCP tool:
1. Implement the tool in `src/slack_notifications/mcp_server.py`.
2. Test the tool manually using an MCP inspector or client.
3. Update `docs/mcp-service-setup.md` or `docs/architecture.md` if necessary.

## See Also

- [AGENTS.md](../AGENTS.md) - Core A-E workflow
- [Definition of Done](definition-of-done.md) - Quality checklist
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Code patterns
- [Agent Kernel Workflows](system-prompts/workflows/README.md) - Complete workflow documentation

---
Last Updated: 2026-02-01
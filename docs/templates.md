# Planning Document Templates

This document provides templates for planning documents used in the Slack Notifications project.

## Agent Kernel Templates

The project follows the Agent Kernel template system. For complete template documentation, see:

- **[Template Structure Guide](system-prompts/templates/structure.md)** - Standard templates for project plans, architecture decisions, and investigation reports

## Project-Specific Conventions

### Development Notes Directory

Development notes and session transcripts are stored in `dev_notes/` using the format:

```
dev_notes/[subdir]/YYYY-MM-DD_HH-MM-SS_description.md
```

Subdirectories:
- `specs/` - User intentions and requirements
- `project_plans/` - Detailed implementation strategies
- `changes/` - Change documentation and proof of work

### Planning Documents

When creating project plans, follow the structure from the Agent Kernel:

1. **Executive Summary** - Overview and objectives
2. **Issues Summary** - Problems being addressed
3. **Implementation Phases** - Step-by-step breakdown
4. **Critical Files Summary** - Files to create, modify, or delete
5. **Verification Steps** - Testing and validation
6. **Success Criteria** - Measurable outcomes
7. **Risk Mitigation** - Known risks and mitigation strategies

### Slack Notification Specifics

When implementing features that involve Slack notifications, include the following in your plan:
- **Notification Type:** Sync, Async, or Logging Handler
- **Trigger Condition:** What specific event triggers the notification
- **Message Content:** Format and content of the message
- **Target Channel:** Which channel(s) will receive the notification
- **Error Handling:** How failures to notify will be handled

## See Also

- [AGENTS.md](../AGENTS.md) - Core workflow for AI agents
- [Definition of Done](definition-of-done.md) - Quality standards
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Implementation patterns

---
Last Updated: 2026-02-01

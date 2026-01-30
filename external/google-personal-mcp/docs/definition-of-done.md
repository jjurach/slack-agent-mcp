# Definition of Done - Google Personal MCP Server

**Referenced from:** [AGENTS.md](../AGENTS.md)

This document defines the "Done" criteria for the Google Personal MCP Server project. It extends the universal Agent Kernel Definition of Done with project-specific requirements.

## Agent Kernel Definition of Done

This project follows the Agent Kernel Definition of Done. **You MUST review these documents first:**

### Universal Requirements

See **[Universal Definition of Done](system-prompts/principles/definition-of-done.md)** for:
- Plan vs Reality Protocol
- Verification as Data
- Codebase State Integrity
- Agent Handoff
- Status tracking in project plans
- dev_notes/ change documentation requirements

### Python Requirements

See **[Python Definition of Done](system-prompts/languages/python/definition-of-done.md)** for:
- Python environment & dependencies
- pytest testing requirements
- Code quality standards (PEP 8, type hints, docstrings)
- File organization
- Coverage requirements

## Project-Specific Extensions

The following requirements are specific to the Google Personal MCP Server and extend the Agent Kernel DoD:

### 1. MCP Tool Development Requirements

All MCP tools must follow the [Standard Tool Template](implementation-reference.md#standard-tool-template).

**Mandatory Checks:**
- [ ] Tool follows standard template pattern (see Implementation Reference)
- [ ] Request ID management implemented (`set_request_id` / `clear_request_id`)
- [ ] Structured response format used (`{"status": "...", "result": ...}`)
- [ ] Exceptions handled and NOT raised to MCP layer
- [ ] Credential masking applied to error messages
- [ ] Audit logging implemented for tool calls
- [ ] Service locator used for Google Services
- [ ] `@mcp.tool()` decorator applied

### 2. Google API Integration Requirements

When adding support for new Google APIs, follow the [Google API Integration Pattern](implementation-reference.md#google-api-integration-pattern).

**Mandatory Checks:**
- [ ] OAuth scopes updated in `src/google_mcp_core/auth.py`
- [ ] Service class follows `GoogleContext` pattern
- [ ] API version explicitly specified (no "latest")
- [ ] Retry logic applied (`@retry_on_rate_limit`)
- [ ] README.md updated with re-authentication instructions

### 3. Testing Requirements for Google APIs

Follow the [Testing Patterns](implementation-reference.md#testing-patterns).

**Mandatory Checks:**
- [ ] **NO real API calls in unit tests** (Must use mocks)
- [ ] Integration tests marked with `@pytest.mark.integration`
- [ ] Integration tests skip gracefully if credentials missing
- [ ] Mocks use realistic Google API response structures

### 4. Configuration & Security

**Mandatory Checks:**
- [ ] New resources added to `AppConfig` model
- [ ] **NO credentials in committed code**
- [ ] **NO hardcoded resource IDs** (Use aliases)
- [ ] Credential masking verified in tests (`mask_credentials`)

### 5. Documentation

**Mandatory Checks:**
- [ ] Tool added to README.md tool list
- [ ] Tool parameters and returns documented in docstrings
- [ ] New architecture components added to [Architecture](architecture.md)
- [ ] New patterns added to [Implementation Reference](implementation-reference.md)

## Pre-Commit Checklist

Before committing, verify:

**Code Quality:**
- [ ] Black formatting applied: `black src/ tests/`
- [ ] Ruff checks pass: `ruff check src/ tests/`
- [ ] Type hints present

**Testing:**
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] Integration tests pass (or skipped): `pytest tests/integration/ -v -m integration`
- [ ] Coverage checked: `pytest tests/ --cov=src/google_mcp_core`

**Security:**
- [ ] No credentials in git diff
- [ ] Credential masking active

**Documentation:**
- [ ] README updated
- [ ] Architecture/Implementation Reference updated

## See Also

- [AGENTS.md](../AGENTS.md) - Core A-E workflow
- [Universal DoD](system-prompts/principles/definition-of-done.md) - Agent Kernel universal requirements
- [Python DoD](system-prompts/languages/python/definition-of-done.md) - Agent Kernel Python requirements
- [Implementation Reference](implementation-reference.md) - Code patterns and templates

---
Last Updated: 2026-01-28
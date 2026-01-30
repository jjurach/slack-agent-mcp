# MCP Project Synchronization Guide

This guide explains how to keep documentation and patterns consistent across multiple MCP projects (slack-agent, google-personal-mcp, etc.).

## Philosophy

Each MCP project has its own:
- Service layer implementation (Slack, Google Sheets, AWS, etc.)
- Authentication mechanism (tokens, OAuth, API keys, etc.)
- Specific tools and capabilities
- Tool-specific documentation

But all MCP projects **share**:
- Technology stack (FastMCP, Pydantic, cyclopts, pytest)
- Directory structure
- Testing patterns
- Logging and audit trail patterns
- Configuration patterns
- Documentation structure
- CLI framework and patterns

## Files to Sync

### Always Sync (No Project Changes Needed)

These files are identical across all projects:

- `docs/system-prompts/mcp-standards.md` - Copy as-is, no changes
- `pytest.ini` - Copy as-is, no changes
- `.coveragerc` - Copy as-is, no changes
- `CONTRIBUTING.md` - Copy as-is (or create symbolic link)

### Sync with Minor Changes

These files are copied and adapted for the specific service:

- `docs/mcp-implementation-guide.md` - Copy structure, update service sections
- `docs/development-guide.md` - Copy structure, update setup instructions
- `docs/troubleshooting.md` - Copy structure, add project-specific issues
- `tests/conftest.py` - Copy structure, update service fixtures

### Project-Specific (Don't Sync)

- `docs/system-prompts/agent-instructions.md` - Project's own tools
- `README.md` - Project's own feature set
- All source code files (service implementation)

## Step-by-Step Sync for New Project

### Step 1: Choose Template

Select an existing MCP project as template (e.g., google-personal-mcp):
- Review its `docs/system-prompts/mcp-standards.md`
- Review its `docs/mcp-implementation-guide.md`

### Step 2: Copy Shared Files

Copy files that are identical across all projects:

```bash
# Assuming working in new-project directory

# Copy shared documentation
mkdir -p docs/system-prompts
cp ../template-project/docs/system-prompts/mcp-standards.md docs/system-prompts/

# Copy testing config
cp ../template-project/pytest.ini .
cp ../template-project/.coveragerc .

# Copy contribution guidelines
cp ../template-project/CONTRIBUTING.md .
```

### Step 3: Copy and Adapt Implementation Guide

Copy the implementation guide structure and adapt for your service:

```bash
cp ../template-project/docs/mcp-implementation-guide.md docs/

# Then edit to reflect your service's:
# - Service type (Slack vs. Google vs. AWS)
# - Authentication mechanism
# - API libraries
# - Directory structure paths
# - Specific tools and capabilities
# - Configuration examples
```

Key sections to customize:
1. **Architecture** - Your service layer design
2. **Technology Stack** - API libraries for your service
3. **Configuration System** - Profile structure for your tokens
4. **Authentication & Secrets** - Your auth mechanisms
5. **CLI Integration** - Your service-specific commands
6. **Best Practices** - Patterns for your service

### Step 4: Copy Development Guide

```bash
cp ../template-project/docs/development-guide.md docs/

# Edit:
# - Setup instructions (how to get service credentials)
# - Adding new tools (service-specific pattern)
# - Testing with service (service-specific setup)
# - Running the server (service-specific)
```

### Step 5: Copy Test Structure

```bash
cp ../template-project/tests/conftest.py tests/

# Edit fixtures:
# - Mock service objects for your service
# - Service-specific configurations
# - Integration test setup
```

### Step 6: Copy Utility Modules

Copy the core utility patterns (these are mostly generic):

```bash
# Create directories
mkdir -p src/yourservice_core/logging
mkdir -p src/yourservice_core/utils

# Copy patterns
cp ../template-project/src/template_core/logging/*.py src/yourservice_core/logging/
cp ../template-project/src/template_core/utils/*.py src/yourservice_core/utils/

# These need minimal changes - mostly copy as-is
```

### Step 7: Create Project-Specific Documentation

Create files unique to your project:

1. **`docs/system-prompts/agent-instructions.md`**
   - Tool descriptions for your service
   - Domain-specific context
   - Usage patterns
   - Error handling for your service

2. **`docs/troubleshooting.md`** (service-specific additions)
   - Add project-specific issues
   - Extend with auth troubleshooting for your service
   - Service-specific permission issues

3. **`README.md`**
   - Your service's feature set
   - Your specific tools
   - Getting started for your service

## Keeping Projects in Sync

### When Standards Document Changes

If `docs/system-prompts/mcp-standards.md` is updated in one project:

1. Update the source project (decision point)
2. Copy updated file to all other MCP projects (no local changes)
3. Each project may add service-specific notes after standard sections

### When Pattern Emerges

If a new pattern is discovered in one project:

1. Document the pattern in that project
2. Add it to `docs/system-prompts/mcp-standards.md`
3. Sync the standard to all projects
4. Each project implements in its codebase

### When Bug Fix Found

If a bug is fixed in shared code (e.g., sanitizer.py):

1. Fix in source project
2. Create pull request
3. Apply same fix to all projects
4. Document in CHANGELOG

## Tools for Sync Management

### Option 1: Git Submodules

Maintain shared patterns in submodule:

```bash
# In each project:
git submodule add https://github.com/user/mcp-standards.git docs/standards

# Then link:
cd docs && ln -s standards/mcp-standards.md mcp-standards.md
```

### Option 2: Manual Copy Script

Create sync script for your repo group:

```bash
#!/bin/bash
# sync-standards.sh

TEMPLATE_PROJECT=/path/to/google-personal-mcp
PROJECTS=(slack-agent another-mcp project-x)

for project in "${PROJECTS[@]}"; do
    echo "Syncing $project..."
    
    # Copy exact files
    cp "$TEMPLATE_PROJECT/docs/system-prompts/mcp-standards.md" \
       "$project/docs/system-prompts/"
    cp "$TEMPLATE_PROJECT/pytest.ini" "$project/"
    cp "$TEMPLATE_PROJECT/.coveragerc" "$project/"
    cp "$TEMPLATE_PROJECT/CONTRIBUTING.md" "$project/"
    
    echo "✓ $project synced"
done
```

### Option 3: GitHub Template Repository

Use GitHub template feature:

1. Create template repo with all shared files
2. When creating new project: "Use this template"
3. Delete service-specific docs, customize

## Checklist for New MCP Project

When onboarding a new service, verify:

- [ ] `docs/system-prompts/mcp-standards.md` copied (no changes)
- [ ] `docs/mcp-implementation-guide.md` copied and adapted
- [ ] `docs/development-guide.md` copied and customized
- [ ] `docs/troubleshooting.md` copied and extended
- [ ] `docs/system-prompts/agent-instructions.md` created (new)
- [ ] Directory structure matches template
- [ ] `pytest.ini`, `.coveragerc`, `CONTRIBUTING.md` copied
- [ ] `pyproject.toml` updated with service dependencies
- [ ] `conftest.py` adapted for service mocks
- [ ] `context.py`, `logging/`, `utils/` modules copied
- [ ] `README.md` updated with service features
- [ ] All imports use correct package names
- [ ] Tests run: `pytest`
- [ ] CLI works: `service-agent-cli config list-profiles`
- [ ] Coverage targets met: `pytest --cov --cov-report=html`

## Version Tracking

Each project's `docs/system-prompts/mcp-standards.md` should include:

```markdown
# MCP Technology Standards

**Version:** 1.0
**Last Updated:** 2026-01-30
**Synced from:** google-personal-mcp (or slack-agent, etc.)
**Local adaptations:** None (exact copy)
```

Update when syncing:
- Synced from: source project name
- Last synced: current date
- Local adaptations: any customizations (usually none)

## Expected Outcome

After syncing, each MCP project has:

- ✅ Identical technology stack (FastMCP, Pydantic, cyclopts, pytest)
- ✅ Identical directory structure
- ✅ Identical testing approach
- ✅ Identical logging/auditing setup
- ✅ Identical configuration pattern
- ✅ Identical CLI framework
- ✅ Identical documentation structure
- ✅ Project-specific tools and features
- ✅ Service-specific guides

Result: Engineers can move between projects with familiar patterns, agents can apply learned strategies to new services, patterns can evolve consistently.

## Maintaining Source of Truth

**Designate one project as source of truth** for shared files:

- All shared files live there first
- Other projects pull from this one
- When updating standards, update there first
- Run sync script to distribute

Current: `google-personal-mcp` (may change)

## Common Gotchas

1. **Don't customize mcp-standards.md** - Keep it exact copy
2. **Do customize implementation guide** - That's the point
3. **Test after syncing** - Ensure imports are correct
4. **Update dependencies** - Service needs different libs
5. **Update environment variables** - Service uses different names
6. **Review CLI patterns** - Adapt to your service

## Questions?

When syncing a new project:
1. Check template project's implementation guide
2. Look at existing project examples
3. Follow directory structure exactly
4. Customize only project-specific docs
5. Run full test suite to verify

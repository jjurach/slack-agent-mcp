#!/bin/bash
# Auto-generated migration script - REVIEW BEFORE EXECUTION
# Project: slack-agent-mcp

set -e

# Create safety tag before migration
git tag -a -m 'pre-dev_notes-cleanup' pre-dev_notes-cleanup

# Move untracked files to tmp/ for review
mkdir -p tmp
mv dev_notes/project_plans/2025-12-24_19-54-39_python-slack-notification-library.md tmp/2025-12-24_19-54-39_python-slack-notification-library.md.untracked
mv dev_notes/project_plans/2026-01-29_23-54-58_adopt-standards.md tmp/2026-01-29_23-54-58_adopt-standards.md.untracked
mv dev_notes/project_plans/2025-12-25_10-52-29_slack-agent-mcp-extensions.md tmp/2025-12-25_10-52-29_slack-agent-mcp-extensions.md.untracked
mv dev_notes/project_plans/2025-12-25_10-17-24_humorous-demo-script.md tmp/2025-12-25_10-17-24_humorous-demo-script.md.untracked
mv dev_notes/project_plans/2025-12-25_11-22-05_env-file-setup.md tmp/2025-12-25_11-22-05_env-file-setup.md.untracked
mv dev_notes/project_plans/2025-12-25_11-29-18_slack-agent-dotenv-support.md tmp/2025-12-25_11-29-18_slack-agent-dotenv-support.md.untracked
mv dev_notes/project_plans/2025-12-25_11-43-10_slack-agent-rtm-to-web-api-migration.md tmp/2025-12-25_11-43-10_slack-agent-rtm-to-web-api-migration.md.untracked
mv dev_notes/project_plans/2025-12-25_22-48-06_model-backend-mapping-conceptual-change.md tmp/2025-12-25_22-48-06_model-backend-mapping-conceptual-change.md.untracked
mv dev_notes/project_plans/2025-12-25_12-23-20_slack-agent-migration-completion.md tmp/2025-12-25_12-23-20_slack-agent-migration-completion.md.untracked

# Create planning directory structure
mkdir -p planning/inbox

# Migrate project_plans → planning/*-plan.md
git mv dev_notes/project_plans/2025-12-24_19-54-39_python-slack-notification-library.md planning/2025-12-24_19-54-39_python-slack-notification-library-plan.md
git mv dev_notes/project_plans/2025-12-25_10-17-24_humorous-demo-script.md planning/2025-12-25_10-17-24_humorous-demo-script-plan.md
git mv dev_notes/project_plans/2025-12-25_10-52-29_slack-agent-mcp-extensions.md planning/2025-12-25_10-52-29_slack-agent-mcp-extensions-plan.md
git mv dev_notes/project_plans/2025-12-25_11-22-05_env-file-setup.md planning/2025-12-25_11-22-05_env-file-setup-plan.md
git mv dev_notes/project_plans/2025-12-25_11-29-18_slack-agent-dotenv-support.md planning/2025-12-25_11-29-18_slack-agent-dotenv-support-plan.md
git mv dev_notes/project_plans/2025-12-25_11-43-10_slack-agent-rtm-to-web-api-migration.md planning/2025-12-25_11-43-10_slack-agent-rtm-to-web-api-migration-plan.md
git mv dev_notes/project_plans/2025-12-25_12-23-20_slack-agent-migration-completion.md planning/2025-12-25_12-23-20_slack-agent-migration-completion-plan.md
git mv dev_notes/project_plans/2025-12-25_22-48-06_model-backend-mapping-conceptual-change.md planning/2025-12-25_22-48-06_model-backend-mapping-conceptual-change-plan.md
git mv dev_notes/project_plans/2026-01-29_23-54-58_adopt-standards.md planning/2026-01-29_23-54-58_adopt-standards-plan.md

# Remove empty directories
rmdir dev_notes/specs 2>/dev/null || true
rmdir dev_notes/project_plans 2>/dev/null || true
rmdir dev_notes/inbox 2>/dev/null || true

echo '✓ Migration complete for slack-agent-mcp'
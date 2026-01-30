# Change Log: Docscan Ignore Special Files

**Date:** 2026-01-28
**Agent:** Gemini
**Status:** Complete

## Description
Added a feature to `docs/system-prompts/docscan.py` to ignore plain-text file reference warnings for specific special files (`README.md`, `AGENTS.md`, etc.).

## Changes
- Modified `docs/system-prompts/docscan.py`: Added `ignored_files` check in `_check_reference_formatting`.

## Verification
- Ran `python3 docs/system-prompts/docscan.py`
- Confirmed warnings reduced from 98 to 36.
- Confirmed warnings for `README.md`, `AGENTS.md`, etc. are gone.

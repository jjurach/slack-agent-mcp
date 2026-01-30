# Definition of Done

This project adheres to the Agent Kernel standards.

## Universal Principles
**File:** [docs/system-prompts/principles/definition-of-done.md](system-prompts/principles/definition-of-done.md)

## Language-Specific Requirements (Python)
**File:** [docs/system-prompts/languages/python/definition-of-done.md](system-prompts/languages/python/definition-of-done.md)

## Project-Specific Extensions

### Dependency Management
- All dependencies must be defined in `pyproject.toml` (or `setup.py` if applicable) AND `requirements.txt`.
- Pin versions to ensure reproducibility.

### Testing
- Run tests using `pytest`.
- Ensure new features have corresponding test coverage.

### Configuration
- Do not commit secrets. Use `.env` files (added to `.gitignore`).
- Update `examples/model_config_example.yaml` or relevant example files if configuration structure changes.
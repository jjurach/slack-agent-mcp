# Contributing to google-personal-mcp

Thank you for your interest in contributing to google-personal-mcp! We welcome contributions from the community, including bug reports, feature requests, and code improvements.

## Getting Started

### Prerequisites

- Python 3.8 or later
- pip and virtualenv
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/google-personal-mcp.git
   cd google-personal-mcp
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies in development mode**
   ```bash
   pip install -e ".[dev]"
   pip install -r requirements.txt
   ```

4. **Run tests to verify setup**
   ```bash
   pytest -v
   ```

## Making Changes

### Code Style

This project follows the **Agent Kernel** code quality standards. See:

- **[Python Definition of Done](system-prompts/languages/python/definition-of-done.md)** - Python coding standards
- **[Definition of Done](definition-of-done.md)** - Project-specific requirements

**Automated Tools:**

- **black** - Code formatting
- **ruff** - Linting and quick fixes
- **mypy** - Type checking

Run code quality checks before committing:

```bash
# Check code
black --check src/
ruff check src/
mypy src/

# Auto-fix issues
black src/ tests/
ruff check --fix src/ tests/
```

**Project-Specific Patterns:**

When adding MCP tools, follow the standard template (see [Implementation Reference](implementation-reference.md)):

- Use `set_request_id()` at start, `clear_request_id()` in finally block
- Return structured responses: `{"status": "success|error", "result"/"message": ..., "request_id": ...}`
- Apply credential masking: `mask_credentials()` for all errors
- Add audit logging: `audit_logger.log_tool_call()`
- Use service locators: `get_sheets_service()`, `get_drive_service()`
- Never raise exceptions to MCP layer (return error responses instead)

### Commit Messages

Use clear, descriptive commit messages following these guidelines:

- Start with a verb (Add, Fix, Update, Refactor, etc.)
- Keep the first line under 50 characters
- Add detailed explanation in the body if needed
- Reference issue numbers when applicable

Examples:
```
Add support for batch sheet operations
Fix credential search in XDG config directory
Update documentation for profile-based authentication
```

### Testing

- Write tests for new features
- Ensure all tests pass before submitting a PR
- Run the full test suite:
  ```bash
  pytest tests/ -v
  ```

### Documentation

- Update README.md for user-facing changes
- Update CHANGELOG.md with new features and fixes
- Add docstrings to new functions and classes
- Update docs/overview.md for architectural changes

## Submitting Changes

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, tested code
   - Update documentation as needed
   - Keep commits logical and atomic

3. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request**
   - Provide a clear title and description
   - Reference any related issues
   - Explain why the change is needed
   - Include testing and usage examples

5. **Respond to review feedback**
   - Address any requested changes
   - Maintain a respectful, collaborative tone
   - Ask for clarification if needed

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- A clear title and description
- Steps to reproduce the issue
- Expected vs actual behavior
- Python version and OS
- Error messages and stack traces
- Relevant code snippets

### Feature Requests

For feature requests, include:

- A clear description of the desired functionality
- Use case and motivation
- Proposed API or implementation (if you have ideas)
- Any related issues or discussions

## Code of Conduct

Please treat all contributors with respect and maintain a professional, collaborative tone in all interactions.

## Licensing

By contributing to google-personal-mcp, you agree that your contributions will be licensed under its MIT License.

## Questions?

Feel free to open an issue for questions or discussions about the project. We're here to help!

---

Thank you for helping make google-personal-mcp better! 🎉

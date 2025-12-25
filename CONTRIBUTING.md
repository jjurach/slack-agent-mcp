# Contributing to Slack Notifications

Thank you for your interest in contributing to the Slack Notifications library! We welcome contributions from the community.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/slack-notifications.git
   cd slack-notifications
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev,test]"
   ```

4. **Run tests:**
   ```bash
   pytest
   ```

## Code Style

This project uses several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

### Pre-commit Hooks

We recommend setting up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=slack_notifications --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

### Writing Tests

- Tests should be placed in the `tests/` directory
- Use descriptive test names and docstrings
- Follow the existing patterns for mocking and fixtures
- Aim for high test coverage

## Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run the full test suite** and ensure all tests pass
6. **Submit a pull request** with a clear description of the changes

## Issues

- Use GitHub issues to report bugs or request features
- Provide detailed information including:
  - Python version
  - Operating system
  - Steps to reproduce
  - Expected vs actual behavior

## License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to foster an inclusive and welcoming community.
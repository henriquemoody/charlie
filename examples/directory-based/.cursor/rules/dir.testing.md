---
description: Testing Requirements
---

## Test Coverage

- Maintain **minimum 80% code coverage**
- All new features require unit tests
- Critical paths require integration tests

## Test Organization

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- E2E tests: `tests/e2e/`

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py
```

## Test Guidelines

- Use **descriptive test names** that explain what is being tested
- Follow **Arrange-Act-Assert** pattern
- Use **fixtures** for common setup
- Mock external dependencies
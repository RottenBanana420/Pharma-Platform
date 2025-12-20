# Contributing Guidelines

Thank you for your interest in contributing to the Pharma Platform!

## 🛠 Development Workflow

1. **Environment Setup**: Ensure you have Python 3.12 and PostgreSQL installed.
2. **Branching**: Create a new branch for every feature or bugfix (`feat/`, `fix/`, `docs/`).
3. **Coding Standards**:
   - Follow PEP 8 for Python code.
   - Use meaningful variable and function names.
   - Write docstrings for all classes and functions.
4. **Testing**:
   - Write tests for all new features.
   - Ensure all tests pass before submitting a PR.
   - Run tests with `DJANGO_ENVIRONMENT=testing pytest`.

## 🧪 Test-Driven Development (TDD)

We encourage TDD. If you're adding a new feature:

1. Write a failing test.
2. Implement the minimum code to make it pass.
3. Refactor and ensure all tests still pass.

## 📝 Commit Messages

We use conventional commit messages:

- `feat: add new feature`
- `fix: resolve bug`
- `docs: update documentation`
- `test: add tests`
- `refactor: code cleanup`

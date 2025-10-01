# Contributing to Vesper

Thank you for your interest in contributing to Vesper! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/vesper.git
   cd vesper
   ```

2. **Set up the development environment**
   ```bash
   ./dev.sh setup
   ```

3. **Activate the virtual environment**
   ```bash
   source .venv/bin/activate
   ```

## Development Workflow

### Before Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Install pre-commit hooks**
   ```bash
   ./dev.sh precommit-install
   ```

### Making Changes

1. **Write your code** following the project's style guidelines
2. **Add tests** for new functionality
3. **Update documentation** if needed

### Before Committing

1. **Run code formatting**
   ```bash
   ./dev.sh format
   ```

2. **Run linting checks**
   ```bash
   ./dev.sh lint
   ```

3. **Run all tests**
   ```bash
   ./dev.sh test
   ```

4. **Run pre-commit hooks**
   ```bash
   ./dev.sh precommit-run
   ```

### Committing

Pre-commit hooks will automatically run when you commit. If they fail, fix the issues and commit again.

```bash
git add .
git commit -m "feat: add new feature description"
```

## Code Style

- We use [Black](https://black.readthedocs.io/) for code formatting
- We use [isort](https://pycqa.github.io/isort/) for import sorting
- We use [flake8](https://flake8.pycqa.org/) for linting
- We use [mypy](https://mypy.readthedocs.io/) for type checking

All style checks are enforced by pre-commit hooks and CI.

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `style:` code style changes (formatting, etc.)
- `refactor:` code refactoring
- `test:` adding or updating tests
- `chore:` maintenance tasks

## Testing

- Write tests for all new functionality
- Ensure all existing tests pass
- Aim for good test coverage
- Use descriptive test names

## Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update type hints

## Pull Requests

1. **Push your branch** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a pull request** from your fork to the main repository
3. **Fill out the PR template** completely
4. **Wait for review** and address any feedback

## Development Commands

Use the `./dev.sh` script for common development tasks:

- `./dev.sh format` - Format code
- `./dev.sh lint` - Run linting
- `./dev.sh test` - Run tests
- `./dev.sh run` - Start the application
- `./dev.sh precommit-run` - Run pre-commit hooks

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues and PRs first

## Code of Conduct

Please be respectful and inclusive in all interactions. We want to maintain a welcoming environment for all contributors.

Thank you for contributing to Vesper! 🚀

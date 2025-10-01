#!/bin/bash
# Development utility script for Vesper

set -e

case "$1" in
    "activate")
        echo "🔧 To activate the virtual environment, run:"
        echo "   source .venv/bin/activate"
        echo ""
        echo "Note: You cannot activate a virtual environment from a script."
        echo "You must source the activation script directly in your shell."
        ;;
    "format")
        echo "🎨 Auto-fixing code formatting and common issues..."
        source .venv/bin/activate
        # Run the auto-fixing pre-commit hooks
        echo "  Fixing trailing whitespace..."
        pre-commit run trailing-whitespace --all-files || true
        echo "  Fixing end-of-file issues..."
        pre-commit run end-of-file-fixer --all-files || true
        # Run autopep8 first for basic PEP8 fixes
        echo "  Running autopep8 for PEP8 fixes..."
        autopep8 --in-place --aggressive --max-line-length=88 --recursive src/ tests/ || true
        # Run code formatters
        echo "  Running black..."
        black src/ tests/
        echo "  Running isort..."
        isort src/ tests/
        echo "✅ All auto-fixes complete!"
        ;;
    "lint")
        echo "🔍 Running linter checks..."
        source .venv/bin/activate
        echo "  Running flake8..."
        flake8 src/ tests/
        # echo "  Running mypy..."
        # mypy src/
        # echo "✅ Linting complete!"
        ;;
    "check")
        echo "🔧 Running full code quality check..."
        source .venv/bin/activate
        echo "  Running black (check only)..."
        black --check src/ tests/
        echo "  Running isort (check only)..."
        isort --check-only src/ tests/
        echo "  Running flake8..."
        flake8 src/ tests/
        echo "  Running mypy..."
        mypy src/
        echo "✅ All checks passed!"
        ;;
    "run")
        echo "🚀 Starting Vesper..."
        source .venv/bin/activate
        python src/vesper/app.py
        ;;
    "cli")
        echo "🚀 Starting Vesper CLI..."
        source .venv/bin/activate
        PYTHONPATH=src python src/vesper/main.py "${@:2}"
        ;;
    "test")
        echo "🧪 Running tests with pytest..."
        source .venv/bin/activate
        pytest tests/ -v
        echo "✅ Tests complete!"
        ;;
    "amend")
        echo "🔧 Adding auto-fixed files to last commit..."
        # Check if there are any changes
        if git diff --quiet && git diff --staged --quiet; then
            echo "ℹ️  No changes to add"
        else
            # Add all changes and amend the last commit
            git add -A
            git commit --amend --no-edit
            echo "✅ Files added to last commit!"
        fi
        ;;
    "install")
        echo "📦 Installing Vesper in development mode..."
        source .venv/bin/activate
        pip install -e .
        echo "✅ Development installation complete!"
        ;;
    "precommit-install")
        echo "🔧 Installing pre-commit hooks..."
        source .venv/bin/activate
        pre-commit install
        echo "✅ Pre-commit hooks installed!"
        ;;
    "precommit-run")
        echo "🔍 Running pre-commit hooks on all files..."
        source .venv/bin/activate
        pre-commit run --all-files
        echo "✅ Pre-commit checks complete!"
        ;;
    "precommit-update")
        echo "🔄 Updating pre-commit hooks..."
        source .venv/bin/activate
        pre-commit autoupdate
        echo "✅ Pre-commit hooks updated!"
        ;;
    "setup")
        echo "📦 Setting up development environment..."
        python -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        pip install -e .
        echo "🔧 Installing pre-commit hooks..."
        pre-commit install
        echo "✅ Development environment setup complete!"
        ;;
    "clean")
        echo "🧹 Cleaning up build artifacts..."
        rm -rf build/
        rm -rf dist/
        rm -rf *.egg-info/
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete
        echo "✅ Cleanup complete!"
        ;;
    *)
        echo "Vesper Development Script"
        echo "Usage: $0 {activate|format|lint|check|run|cli|test|install|precommit-install|precommit-run|precommit-update|setup|clean}"
        echo ""
        echo "Commands:"
        echo "  activate         - Show how to activate virtual environment"
        echo "  format           - Format code with black and isort"
        echo "  lint             - Run flake8 and mypy linting"
        echo "  check            - Run all checks (black, isort, flake8, mypy)"
        echo "  run              - Start Vesper application"
        echo "  cli              - Run Vesper CLI with arguments"
        echo "  test             - Run tests with pytest"
        echo "  install          - Install in development mode"
        echo "  precommit-install - Install pre-commit hooks"
        echo "  precommit-run    - Run pre-commit hooks on all files"
        echo "  precommit-update - Update pre-commit hooks"
        echo "  setup            - Setup complete development environment"
        echo "  clean            - Clean build artifacts and cache files"
        echo ""
        echo "Examples:"
        echo "  ./dev.sh format              # Format all code"
        echo "  ./dev.sh run                 # Start the app"
        echo "  ./dev.sh cli --help          # Show CLI help"
        echo "  ./dev.sh cli -f example.md   # Open a file"
        exit 1
        ;;
esac

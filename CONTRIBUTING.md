# Contributing (Solo workflow cheatsheet)

This project uses a simple, low-drama Git workflow designed for a solo developer—and it plays nicely with Dependabot PRs and GitHub merges.

## Golden rules

- Never commit directly to `main` (treat it as protected).
- Always create a feature branch off an up-to-date `main`.
- Prefer rebase over merge to keep history linear.
- Use `--force-with-lease` only on your own feature branches (never on `main`).

## One-time helpful defaults

Configure these once to reduce surprises:

```sh
git config --global pull.rebase true       # pull uses rebase instead of merge
git config --global pull.ff only           # fail if pull can't fast-forward
git config --global rebase.autoStash true  # stash/unstash automatically for rebase
git config --global push.default current   # push current branch to same name
```

## Create a feature branch

```sh
git fetch origin
git switch main
git pull --ff-only              # ensure local main is exactly origin/main
git switch -c feature/xyz       # create your branch from current main
```

## Keep your branch up to date

Rebase your branch on the latest `origin/main` periodically:

```sh
git fetch origin
git rebase origin/main
```

If you have already pushed your branch and then rebased locally, update the remote branch with:

```sh
git push --force-with-lease
```

## Open a PR and merge

- Push your branch: `git push -u origin feature/xyz`
- Open a PR on GitHub. Prefer "Squash and merge" or "Rebase and merge" to keep main linear.
- After merge, delete the branch on GitHub and locally.

## Update local main after merges (including Dependabot)

Dependabot or GitHub merges advance `origin/main`. Update your local `main` with fast-forward only:

```sh
git fetch origin
git switch main
git pull --ff-only
```

## Fixing the non-fast-forward push error

If you see:

```
error: failed to push some refs
hint: Updates were rejected because the tip of your current branch is behind
```

Use the appropriate fix:

- If you did NOT rebase/amend locally (remote just moved ahead):

  ```sh
  git pull --rebase
  git push
  ```

- If you DID rebase or amend locally after pushing (your history changed):

  ```sh
  git push --force-with-lease
  ```

## Quick recap

1. `main` stays clean: `git pull --ff-only`
2. Branch from main: `git switch -c feature/xyz`
3. Rebase to catch up: `git rebase origin/main`
4. Push safely: `git push` (or `--force-with-lease` after rebase)

## Project-only commits from the app

Vesper can stage, commit, push, and open a PR for only the files inside your current project (e.g., `projects/my-book`). This keeps unrelated content out of a writing commit.

What the in-app "Commit Project" does:

- Pre-syncs `main` safely
   - If `origin` exists, it fetches and then fast-forwards local `main` from `origin/main`.
   - If fast-forward is not possible, it stops and asks you to resolve manually (e.g., `git pull --rebase`), keeping `main` clean.
- Creates a timestamped branch
   - New branch named `vesper/<project-label>/YYYY-MM-DD-hh-mm-ss` off `main`.
- Stages only your project
   - `git add -A -- <project-path>` so only files under your current project (including `.md` and `.json`) are included.
- Generates a helpful commit message
   - Imperative subject per https://cbea.ms/git-commit/
   - Body includes total diff stats, added/edited markdown headings, outline title changes, and a short file list.
- Commits and pushes the branch
   - Pushes to `origin` and sets upstream.
- Creates a GitHub PR (if `gh` is installed)
   - Opens a PR targeting `main` using the generated subject/body.
   - Attempts to enable auto-merge (squash) if allowed by repo settings.

Troubleshooting:

- "Could not fast-forward 'main'" → Switch to `main` and run `git pull --rebase` (or follow the “Fixing the non-fast-forward” section above), then retry the commit.
- PR creation requires the GitHub CLI (`gh`) and auth (`gh auth login`). If unavailable, the app still commits and pushes; open a PR manually from GitHub.

## Optional: LLM-generated commit messages (future)

The app supports a high-quality local message today. We may add an optional LLM provider to elevate commit messages further. Proposed approach:

- Toggle via a setting (e.g., `~/.vesper/settings.json`) or env vars.
- Providers: OpenAI (ChatGPT) or GitHub Copilot (if an API is available for commits).
- Inputs: project-scoped diff summary, markdown headings, outline changes.
- Output: subject (imperative) + body per cbea.ms, with a strict length cap.
- Privacy & safety: send only what’s needed (no secrets), fall back to local message on errors/timeouts.

Until then, the built-in message is deterministic, readable, and purpose-built for writing.
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

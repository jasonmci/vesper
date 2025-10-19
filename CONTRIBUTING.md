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

## Commit All + PR from the app

Vesper can stage, commit, push, and open a PR for all changes in the repository (a "flush" commit). Use the in-app shortcut:

- Commit All: press `Ctrl+Shift+G`

What the in-app Commit All does:

- Pre-syncs `main` safely
   - If `origin` exists, it fetches and attempts to fast-forward local `main` from `origin/main`.
   - If fast-forward is not possible, it stops and asks you to resolve manually (e.g., `git pull --rebase`), keeping `main` clean and linear.
- Creates a timestamped branch
   - New branch named `vesper/YYYY-MM-DD-hh-mm-ss` (or `vesper/<scope>/...` when scoped) off `main`.
- Stages all changes
   - Uses `git add -A` to include tracked and untracked changes across the repo.
- Generates a helpful commit message
   - Imperative subject per https://cbea.ms/git-commit/
   - Body includes total diff stats, added/edited markdown headings, outline title changes, and a short file list.
   - Optionally refines the message with an LLM (see “LLM commit messages” below).
- Commits and pushes the branch
   - Pushes to `origin` and sets upstream.
- Creates a GitHub PR (if `gh` is installed and authed)
   - Opens a PR targeting `main` using the generated subject/body.
   - Auto-merge is optional; controlled by a setting (default disabled).
   - Saves the branch name to settings as `last_branch` for later cleanup.

Troubleshooting:

- "Could not fast-forward 'main'" → Switch to `main` and run:

   ```sh
   git pull --rebase
   ```

   Then retry the commit.

- PR creation requires the GitHub CLI (`gh`) and authentication. If unavailable, the app still commits and pushes; open a PR manually from GitHub.

   ```sh
   gh auth login
   ```

Logs: toast notifications are mirrored to `~/.vesper/vesper.log` to help diagnose issues.

### LLM commit messages (optional)

Commit messages are generated locally by default. To enable optional LLM refinement (OpenAI):

- Press `Ctrl+Shift+L` in the app to open LLM settings, or edit `~/.vesper/settings.json`:

```json
{
   "llm.enabled": true,
   "llm.provider": "openai",
   "openai.api_key": "sk-...",
   "openai.model": "gpt-4o-mini",
   "openai.max_tokens": 512,
   "openai.timeout_secs": 12,
   "openai.base_url": "https://api.openai.com/v1"
}
```

Notes:

- The prompt is editorial only and follows cbea.ms guidance. If the LLM call fails or is disabled, the app falls back to the local message.
- API key is stored in `~/.vesper/settings.json`.

### Optional PR auto-merge

Control auto-merge behavior (off by default) via `~/.vesper/settings.json`:

```json
{
   "gh.auto_merge": false
}
```

When enabled and supported by repo permissions, the app attempts `gh pr merge --auto --squash` after PR creation.

## Sync Main & Cleanup (post-PR)

After your PR is merged on GitHub, you can sync `main` locally and clean up the merged branch right from the app:

- Sync Main & Cleanup: press `Ctrl+Shift+Y`

What it does:

- Fast-forwards local `main` from `origin/main` (if available)
- Determines the branch to remove using `last_branch` in settings (or you can pass one programmatically)
- Verifies that the branch is already merged into `main`
- Deletes the local branch, and optionally deletes the remote branch on `origin`

If the branch isn’t merged yet, or isn’t found locally, it leaves a clear warning and does not delete anything.

<!-- The previous "future" LLM section has been implemented; see LLM commit messages above. -->
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

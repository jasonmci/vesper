from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _ensure_repo(root: Path) -> None:
    if not (root / ".git").exists():
        _run(["git", "init"], root)
        # Default to main if no HEAD
        _run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], root)


def _changed_files(root: Path, scope: Optional[Path] = None) -> List[str]:
    # Porcelain status gives two-letter code + path
    args = ["git", "status", "--porcelain"]
    if scope is not None:
        args += ["--", str(scope)]
    proc = _run(args, root)
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    files: List[str] = []
    for ln in lines:
        # format: 'XY path'
        parts = ln.split(maxsplit=1)
        if len(parts) == 2:
            files.append(parts[1])
    return files


def _timestamp_branch_name(project_label: Optional[str] = None) -> str:
    ts = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    base = f"vesper-{ts}"
    if project_label:
        # sanitize path-like label into simple token
        label = re.sub(r"[^a-zA-Z0-9_-]+", "-", project_label).strip("-")
        base = f"vesper/{label}/{ts}"
    return base


def _create_branch(root: Path, name: str) -> Tuple[bool, str]:
    """Create and switch to a new branch. Returns (ok, branch_name)."""
    proc = _run(["git", "switch", "-c", name], root)
    if proc.returncode == 0:
        return True, name
    # Fall back with a suffix to avoid collisions
    alt = f"{name}-1"
    proc2 = _run(["git", "switch", "-c", alt], root)
    return (proc2.returncode == 0), (alt if proc2.returncode == 0 else name)


def _has_remote_origin(root: Path) -> bool:
    proc = _run(["git", "remote", "get-url", "origin"], root)
    return proc.returncode == 0 and proc.stdout.strip() != ""


def _fetch_origin(root: Path) -> None:
    _run(["git", "fetch", "origin"], root)


def _ff_update_main(root: Path) -> Tuple[bool, str]:
    """Fast-forward local main from origin/main if possible.

    Returns (ok, detail). If branch doesn't exist or no remote, returns (True, "").
    """
    has_main = _run(["git", "rev-parse", "--verify", "main"], root).returncode == 0
    if not has_main:
        return True, ""
    if _has_remote_origin(root):
        _fetch_origin(root)
        _run(["git", "switch", "main"], root)
        pull = _run(["git", "pull", "--ff-only", "origin", "main"], root)
        if pull.returncode != 0:
            detail = pull.stderr.strip() or pull.stdout.strip()
            return False, detail
    else:
        _run(["git", "switch", "main"], root)
    return True, ""


def _staged_numstat(
    root: Path, scope: Optional[Path] = None
) -> List[Tuple[int, int, str]]:
    """Return list of (added_lines, deleted_lines, path) for staged changes."""
    args = ["git", "diff", "--cached", "--numstat"]
    if scope is not None:
        args += ["--", str(scope)]
    proc = _run(args, root)
    stats: List[Tuple[int, int, str]] = []
    for ln in proc.stdout.splitlines():
        parts = ln.split("\t")
        if len(parts) >= 3:
            try:
                add = int(parts[0]) if parts[0] != "-" else 0
                delete = int(parts[1]) if parts[1] != "-" else 0
            except ValueError:
                add, delete = 0, 0
            stats.append((add, delete, parts[2]))
    return stats


def _staged_patch(root: Path, scope: Optional[Path] = None) -> str:
    args = ["git", "diff", "--cached", "-U0"]
    if scope is not None:
        args += ["--", str(scope)]
    return _run(args, root).stdout


def _extract_added_md_headings(patch: str) -> List[str]:
    """Extract added markdown headings (#+ lines) from a unified diff patch."""
    headings: List[str] = []
    for ln in patch.splitlines():
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln.startswith("+") and not ln.startswith("+++"):
            text = ln[1:]
            if text.lstrip().startswith("#"):
                # capture up to first 80 chars
                headings.append(text.strip()[:80])
    return headings


def _summarize_outline_changes(patch: str) -> Dict[str, int]:
    """Heuristic: count added json outline 'title' keys and bullets."""
    added_titles = 0
    for ln in patch.splitlines():
        if ln.startswith('+"') and '"title"' in ln:
            added_titles += 1
    return {"titles_added": added_titles}


def _build_commit_message(
    files: List[str],
    project_label: Optional[str],
    numstat: List[Tuple[int, int, str]],
    patch: str,
) -> str:
    """Generate a readable message per https://cbea.ms/git-commit/ guidance.

    Subject in imperative mood; body explains what changed. Includes a brief
    summary of markdown headings added and outline changes.
    """
    if not files:
        return "No changes"

    # Aggregate totals
    add_total = sum(a for a, _, _ in numstat)
    del_total = sum(d for _, d, _ in numstat)
    md_files = [f for f in files if f.endswith(".md")]
    json_files = [f for f in files if f.endswith(".json")]

    # Headings and outline deltas from patch
    headings = [h for h in _extract_added_md_headings(patch) if h]
    outline_info = _summarize_outline_changes(patch)

    # Subject line
    if md_files and json_files:
        subject = "Update chapters and outline"
    elif md_files:
        subject = "Write chapter updates"
    elif json_files:
        subject = "Revise outline"
    else:
        subject = "Update project files"
    if project_label:
        subject = f"{subject} ({project_label})"

    # Body
    lines: List[str] = []
    lines.append(f"Total changes: +{add_total} −{del_total} lines")
    if headings:
        lines.append("")
        lines.append("New/edited headings:")
        # cap to 10 for readability
        for h in headings[:10]:
            lines.append(f"- {h}")
        if len(headings) > 10:
            lines.append("- …")

    if json_files:
        t_added = outline_info.get("titles_added", 0)
        lines.append("")
        lines.append(f"Outline changes: +{t_added} titles detected")

    # File list (short)
    lines.append("")
    lines.append("Files:")
    for p in files[:12]:
        lines.append(f"- {p}")
    if len(files) > 12:
        lines.append("- …")

    return subject + "\n\n" + "\n".join(lines)


def _split_subject_body(msg: str) -> Tuple[str, str]:
    parts = msg.split("\n\n", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    # Fallback: first line as subject
    lines = msg.splitlines()
    if not lines:
        return "Update project", ""
    return lines[0].strip(), "\n".join(lines[1:]).strip()


def _gh_available(root: Path) -> bool:
    return _run(["gh", "--version"], root).returncode == 0


def _gh_create_pr(
    root: Path,
    head_branch: str,
    title: str,
    body: str,
    base: str = "main",
) -> Tuple[bool, str]:
    """Create a GitHub PR via gh. Returns (ok, url_or_detail)."""
    args = [
        "gh",
        "pr",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--base",
        base,
        "--head",
        head_branch,
    ]
    proc = _run(args, root)
    if proc.returncode != 0:
        return False, (proc.stderr.strip() or proc.stdout.strip())
    out = proc.stdout.strip()
    # Try to find PR URL in output
    import re as _re

    m = _re.search(r"https?://\S+/pull/\d+", out)
    return (True, m.group(0) if m else out)


def _gh_enable_auto_merge(root: Path, pr_url: str) -> Tuple[bool, str]:
    """Enable auto-merge (squash) on the PR if perms allow."""
    proc = _run(["gh", "pr", "merge", "--auto", "--squash", pr_url], root)
    if proc.returncode != 0:
        return False, (proc.stderr.strip() or proc.stdout.strip())
    return True, "enabled"


# ---- Optional LLM commit message support ---------------------------------
def _maybe_llm_commit_message(
    settings: Dict[str, str],
    local_message: str,
    project_label: Optional[str],
) -> Optional[str]:
    """Return an LLM-generated message if configured, else None."""
    provider = str(settings.get("llm.provider", "")).lower()
    if str(settings.get("llm.enabled", "false")).lower() not in ("1", "true", "yes"):
        return None
    if provider != "openai":
        return None
    api_key = settings.get("openai.api_key")
    if not api_key:
        return None

    # Build a compact prompt that instructs editorial tone only
    subject, body = _split_subject_body(local_message)
    sys = (
        "You generate concise, high-quality git commit messages per "
        "https://cbea.ms/git-commit/. Provide: a subject in imperative mood "
        "(<=72 chars) and a short body explaining what changed."
    )
    user = (
        f"Project: {project_label or '(none)'}\n\n"
        f"Candidate message:\n{subject}\n\n{body}\n"
    )

    # Lazy import to avoid hard dependency
    try:
        import requests

        model = settings.get("openai.model", "gpt-4o-mini")
        timeout = int(settings.get("openai.timeout_secs", 12))
        base_url = settings.get("openai.base_url", "https://api.openai.com/v1")
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": int(settings.get("openai.max_tokens", 512)),
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        content = (
            data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        )
        if not content:
            return None
        # Try to split first blank line as subject/body; fallback to single line
        parts = content.split("\n\n", 1)
        if len(parts) == 2:
            subj = parts[0].strip()
            bod = parts[1].strip()
        else:
            lines = content.splitlines()
            subj = lines[0].strip()
            bod = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        # Enforce subject length limit
        if len(subj) > 72:
            subj = subj[:72].rstrip()
        return subj + ("\n\n" + bod if bod else "")
    except Exception:
        return None


def commit_project_changes(
    repo_root: Path, project_path: Optional[Path] = None
) -> Dict[str, str]:
    """Stage, commit, and push changes.

    If project_path is provided, only stage changes under that path (relative to
    repo_root). Otherwise, stage all changes in the repository. Returns a dict
    with 'message' and optional 'severity'.
    """
    root = Path(repo_root)
    _ensure_repo(root)

    rel_scope: Optional[Path] = None
    if project_path is not None:
        try:
            rel_scope = Path(project_path).relative_to(root)
        except Exception:
            # Not relative; fallback to staging all
            rel_scope = None

    changed = _changed_files(root, rel_scope)
    if not changed:
        return {"message": "No changes to commit."}

    # Ensure main is up-to-date (fast-forward only) before branching
    ok_ff, detail_ff = _ff_update_main(root)
    if not ok_ff:
        return {
            "message": (
                "Could not fast-forward 'main'. Pull/rebase manually: " f"{detail_ff}"
            ),
            "severity": "warning",
        }

    # Create a short-lived branch for this commit (timestamped)
    project_label = str(rel_scope) if rel_scope is not None else None
    branch_name = _timestamp_branch_name(project_label)
    ok, used_branch = _create_branch(root, branch_name)
    if not ok:
        return {
            "message": f"Failed to create branch '{branch_name}'. Aborting commit.",
            "severity": "error",
        }

    # Stage all tracked/untracked changes
    if rel_scope is not None:
        _run(["git", "add", "-A", "--", str(rel_scope)], root)
    else:
        _run(["git", "add", "-A"], root)

    # Build message and commit using staged content
    status_after_add = _changed_files(root, rel_scope)
    numstat = _staged_numstat(root, rel_scope)
    patch = _staged_patch(root, rel_scope)
    local_msg = _build_commit_message(status_after_add, project_label, numstat, patch)
    # Optionally enhance with LLM commit message
    from .settings import load_settings  # local import to avoid cycles

    cfg = load_settings()
    llm_msg = _maybe_llm_commit_message(cfg, local_msg, project_label)
    msg = llm_msg or local_msg
    proc = _run(["git", "commit", "-m", msg], root)
    if proc.returncode != 0:
        return {
            "message": f"Commit failed: {proc.stderr.strip() or proc.stdout.strip()}",
            "severity": "error",
        }

    # Try to push if a remote exists
    remotes = _run(["git", "remote"], root).stdout.split()
    if remotes:
        # Push the new branch and set upstream
        push = _run(["git", "push", "-u", "origin", used_branch], root)
        if push.returncode != 0:
            # Surface as warning but keep commit
            detail = push.stderr.strip() or push.stdout.strip()
            return {
                "message": f"Committed on '{used_branch}'. Push failed: {detail}",
                "severity": "warning",
            }

        # Auto-create PR if GitHub CLI is available
        if _gh_available(root):
            subj, body = _split_subject_body(msg)
            ok_pr, pr_info = _gh_create_pr(root, used_branch, subj, body)
            if ok_pr:
                # Try to enable auto-merge (squash)
                ok_am, _ = _gh_enable_auto_merge(root, pr_info)
                auto = " and auto-merge enabled" if ok_am else ""
                return {
                    "message": f"Committed, pushed, PR created at {pr_info}{auto}.",
                }
            else:
                return {
                    "message": (
                        f"Committed and pushed branch '{used_branch}'. "
                        f"PR creation failed: {pr_info}"
                    ),
                    "severity": "warning",
                }

    return {
        "message": (f"Committed on '{used_branch}' (and pushed if remote configured).")
    }

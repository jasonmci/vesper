from __future__ import annotations

from pathlib import Path


def preferred_content_dir(root: Path | None) -> Path:
    """Return the directory to use for content files.

    Uses 'chapters' exclusively.
    """
    base = Path(root) if root else Path(".")
    chapters = base / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    return chapters

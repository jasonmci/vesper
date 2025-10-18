from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Static

# Reuse settings fallback so we load from the active/last project
SETTINGS_FILE = Path.home() / ".vesper" / "settings.json"

# Target wrap widths (tweak to taste)
COL_WIDTHS = {
    "chap_ms": 32,  # Chapter/Milestone combined
    "plot": 36,
    "subplot": 36,
    "character": 36,
    "theme": 36,
}

LINES_PER_ROW = 6

SEP_CHAR = "─"


def _sep_row_cells() -> tuple[str, str, str, str, str]:
    return (
        SEP_CHAR * COL_WIDTHS["chap_ms"],
        SEP_CHAR * COL_WIDTHS["plot"],
        SEP_CHAR * COL_WIDTHS["subplot"],
        SEP_CHAR * COL_WIDTHS["character"],
        SEP_CHAR * COL_WIDTHS["theme"],
    )


def _wrap_to_exact_lines(text: str, width: int, lines: int) -> list[str]:
    """Wrap text to width and return exactly `lines` lines (pad/crop)."""
    if not text:
        return [""] * lines
    out: list[str] = []
    for raw in text.splitlines() or [""]:
        if raw:
            out.extend(textwrap.wrap(raw, width=width, break_long_words=False))
        else:
            out.append("")
    # pad or crop
    if len(out) < lines:
        out += [""] * (lines - len(out))
    else:
        out = out[:lines]
    return out


def _last_project_from_settings() -> Optional[Path]:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        p = Path(data.get("last_project", "")).expanduser()
        return p if p.is_dir() else None
    except Exception:
        return None


def _outline_path(app: Widget) -> Path:
    root = (
        getattr(app.app, "project_root", None)
        or _last_project_from_settings()
        or Path(".")
    )
    return (Path(root) / "outline.json").expanduser()


def _load_outline(app: Widget) -> Optional[List[Dict[str, Any]]]:
    path = _outline_path(app)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _flatten_milestones(
    outline_root: List[Dict[str, Any]],
) -> Iterable[Tuple[str, Dict[str, Any]]]:
    """
    Yield (chapter_title, milestone_dict) in document order.
    outline_root = [beat, beat, ...], each has children chapters,
    each has children milestones.
    """
    for beat in outline_root:
        for chapter in beat.get("children", []) or []:
            chap_title = chapter.get("title", "Untitled Chapter")
            for ms in chapter.get("children", []) or []:
                if ms.get("kind") == "milestone":
                    yield chap_title, ms


class BoardView(Vertical):
    """
    Serialized milestone board view:
    Chapter | Milestone | Plot | Subplot | Character | Theme
    """

    BINDINGS = [Binding("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        yield Static("Story Board", classes="screen-title")
        self._grid = DataTable(id="board-grid")
        # Add columns ONCE (do not add again when rebuilding rows)
        self._grid.add_columns(
            "Chapter/Milestone", "Plot", "Subplot", "Character", "Theme"
        )
        self._grid.cursor_type = "row"
        yield self._grid

    def on_mount(self) -> None:
        self._rebuild()

    def on_show(self) -> None:
        """Rebuild whenever the tab becomes visible."""
        self._rebuild()

    def action_refresh(self) -> None:
        self._rebuild()

    # ---- internals ----

    def _rebuild(self) -> None:
        # Clear rows only; keep headers
        try:
            self._grid.clear(columns=False)
        except TypeError:
            self._grid.clear()
            if not getattr(self._grid, "columns", None):
                self._grid.add_columns(
                    "Chapter/Milestone", "Plot", "Subplot", "Character", "Theme"
                )

        data = _load_outline(self) or []

        w = COL_WIDTHS
        L = LINES_PER_ROW

        for chapter_title, ms in _flatten_milestones(data):
            chap_ms = f"{chapter_title} — {ms.get('title', '')}"
            col0 = _wrap_to_exact_lines(chap_ms, w["chap_ms"], L)
            col1 = _wrap_to_exact_lines(ms.get("plot", ""), w["plot"], L)
            col2 = _wrap_to_exact_lines(ms.get("subplot", ""), w["subplot"], L)
            col3 = _wrap_to_exact_lines(ms.get("character", ""), w["character"], L)
            col4 = _wrap_to_exact_lines(ms.get("theme", ""), w["theme"], L)

            for i in range(L):
                self._grid.add_row(col0[i], col1[i], col2[i], col3[i], col4[i])

            # add a thin separator row after each milestone block
            self._grid.add_row(*_sep_row_cells())

        # Position cursor at the top (best-effort)
        try:
            from textual.coordinate import Coordinate
        except Exception as e:
            # Older/newer Textual versions may differ; log and continue
            if hasattr(self, "app") and hasattr(self.app, "log"):
                self.app.log(f"BoardView: Coordinate import failed: {e}")
            return

        if getattr(self._grid, "row_count", 0):
            try:
                self._grid.cursor_coordinate = Coordinate(0, 0)
            except Exception as e:
                if hasattr(self, "app") and hasattr(self.app, "log"):
                    self.app.log(f"BoardView: setting cursor failed: {e}")

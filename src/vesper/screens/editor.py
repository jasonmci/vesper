# src/vesper/editor.py
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, TextArea

from vesper.components.file_list import FileListView
from vesper.components.quick_open_panel import QuickOpenPanel
from vesper.services.paths import preferred_content_dir


class EditorView(Container):
    """Text editor panel with load/save helpers + live counter."""

    current_path: Optional[Path] = None
    dirty: bool = False
    _last_edit_ts: float = 0.0

    def compose(self) -> ComposeResult:
        with Horizontal(id="editor-container"):
            # left spacer to keep center column centered when right panels show
            yield Vertical(id="editor-left-spacer")
            with Vertical(id="editor-wrapper"):
                yield TextArea(
                    text=(
                        "# Welcome to Vesper Editor\n\n"
                        "Start typing your content here..."
                    ),
                    language="markdown",
                    theme="monokai",
                    show_line_numbers=True,
                    id="editor-textarea",
                )
                yield Static("", id="editor-status")  # words/lines/chars
            # Right sidebar hosts Files + Quick Open panels
            yield Vertical(id="editor-sidebar")
            # right spacer used when sidebar is hidden to center the editor
            yield Vertical(id="editor-right-spacer")

    def on_mount(self) -> None:
        ta = self.query_one(TextArea)
        ta.focus()
        self._update_counts()
        self._update_app_title()
        # hide sidebar initially; show both spacers to center editor
        sb = self.query_one("#editor-sidebar", Vertical)
        sb.display = False
        ls = self.query_one("#editor-left-spacer", Vertical)
        rs = self.query_one("#editor-right-spacer", Vertical)
        ls.display = True
        rs.display = True

    # ---- Editing feedback -------------------------------------------------

    def on_text_area_changed(self, _: TextArea.Changed) -> None:
        if not self.dirty:
            self.dirty = True
            self._update_app_title()
        self._update_counts()
        self._last_edit_ts = time.time()

    def _update_counts(self) -> None:
        ta = self.query_one(TextArea)
        text = ta.text
        chars = len(text)
        lines = text.count("\n") + (0 if (chars == 0 or text.endswith("\n")) else 1)
        words = len([w for w in text.split() if w.strip()])
        self.query_one("#editor-status", Static).update(
            f"Words: {words}   Lines: {lines}   Chars: {chars}"
        )

    def _update_app_title(self) -> None:
        name = self.current_path.name if self.current_path else "untitled"
        star = " •" if self.dirty else ""
        self.app.title = f"Vesper — {name}{star}"

    # ---- File helpers -----------------------------------------------------

    def new_file(self) -> None:
        self.query_one(TextArea).text = ""
        self.current_path = None
        self.dirty = False
        self._update_counts()
        self._update_app_title()

    def load_file(self, path: str | Path) -> None:
        p = Path(path).expanduser()
        text = p.read_text(encoding="utf-8")
        self.query_one(TextArea).text = text
        self.current_path = p
        self.dirty = False
        self._update_counts()
        self._update_app_title()

    def save_file(
        self, path: str | Path | None = None, *, mark_clean: bool = True
    ) -> None:
        p = Path(path).expanduser() if path else self.current_path
        if p is None:
            # let caller handle prompting for Save As
            raise FileNotFoundError("No path set for save()")
        p.write_text(self.query_one(TextArea).text, encoding="utf-8")
        self.current_path = p
        if mark_clean:
            self.dirty = False
        self._update_app_title()

    # ---- Autosave support ----------------------------------------------

    def should_autosave(self, idle_seconds: float = 15.0) -> bool:
        """Return True if the buffer is dirty and has been idle >= idle_seconds."""
        if not self.dirty:
            return False
        if self._last_edit_ts == 0:
            return False
        return (time.time() - self._last_edit_ts) >= idle_seconds

    # ---- Sidebar ---------------------------------------------------------

    def toggle_file_list(self) -> None:
        sb = self.query_one("#editor-sidebar", Vertical)
        ls = self.query_one("#editor-left-spacer", Vertical)
        rs = self.query_one("#editor-right-spacer", Vertical)
        if sb.display:
            # hide and clear
            sb.display = False
            # show both spacers to center editor
            ls.display = True
            rs.display = True
            sb.remove_children()
            return
        # show and populate
        base = preferred_content_dir(getattr(self.app, "project_root", None))
        sb.display = True
        ls.display = True
        rs.display = False
        sb.remove_children()
        # mount Files and Quick Open panel stacked
        sb.mount(FileListView(base, id="file-list-view"))
        sb.mount(QuickOpenPanel(base, id="quick-open-panel"))

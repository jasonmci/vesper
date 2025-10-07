# src/vesper/editor.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, TextArea


class EditorView(Container):
    """Text editor panel with load/save helpers + live counter."""

    current_path: Optional[Path] = None
    dirty: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="editor-wrapper"):
            yield TextArea(
                text="# Welcome to Vesper Editor\n\nStart typing your content here...",
                language="markdown",
                theme="monokai",
                show_line_numbers=True,
                id="editor-textarea",
            )
            yield Static("", id="editor-status")  # words/lines/chars

    def on_mount(self) -> None:
        ta = self.query_one(TextArea)
        ta.focus()
        self._update_counts()
        self._update_app_title()

    # ---- Editing feedback -------------------------------------------------

    def on_text_area_changed(self, _: TextArea.Changed) -> None:
        if not self.dirty:
            self.dirty = True
            self._update_app_title()
        self._update_counts()

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

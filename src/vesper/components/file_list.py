from __future__ import annotations

from pathlib import Path
from typing import Iterable

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, ListItem, ListView


def _iter_files(base: Path) -> Iterable[Path]:
    for p in base.rglob("*"):
        if p.is_file():
            yield p


class FileListView(Vertical):
    def __init__(self, base: Path, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self._base = base

    def compose(self) -> ComposeResult:
        yield Label("Files", classes="panel-title")
        self._lv = ListView(id="file-list")
        yield self._lv

    def on_mount(self) -> None:
        self.refresh_files()

    def refresh_files(self) -> None:
        lv = self._lv
        lv.clear()
        for p in sorted(_iter_files(self._base)):
            it = ListItem(Label(str(p.relative_to(self._base))))
            setattr(it, "path", p)
            lv.append(it)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        p = getattr(event.item, "path", None)
        if p:
            # Ask the editor to open this file via the registered view
            try:
                from vesper.screens.editor import EditorView

                ed = self.app.query_one("#editor-view", EditorView)
                ed.load_file(p)
            except Exception as e:
                # Surface a warning toast so the user sees the failure
                self.app.notify(f"Open failed: {e}", severity="warning")

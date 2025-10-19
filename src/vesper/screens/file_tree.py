from __future__ import annotations

from pathlib import Path
from typing import Iterable

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView


def _walk_files(base: Path) -> Iterable[Path]:
    for p in base.rglob("*"):
        if p.is_file():
            yield p


class FileTreePicker(ModalScreen[str | None]):
    def __init__(self, base: Path) -> None:
        super().__init__()
        self._base = base

    def compose(self) -> ComposeResult:
        with Vertical(id="file-tree-picker"):
            yield Label("Open file (Esc to cancel)")
            yield ListView(id="file-list")

    def on_mount(self) -> None:
        lv = self.query_one(ListView)
        for p in sorted(_walk_files(self._base)):
            rel = str(p.relative_to(self._base))
            item = ListItem(Label(rel))
            setattr(item, "path", p)
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        p = getattr(event.item, "path", None)
        self.dismiss(str(p) if p else None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)

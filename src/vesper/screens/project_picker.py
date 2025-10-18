from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView


class ProjectPicker(ModalScreen[Path | None]):
    def __init__(self, base: Path) -> None:
        super().__init__()
        self._base = base

    def compose(self) -> ComposeResult:
        with Vertical(id="project-picker"):
            yield Label("Choose a project (Esc to cancel)")
            yield ListView(id="project-list")

    def on_mount(self) -> None:
        lv = self.query_one(ListView)
        for p in sorted([p for p in self._base.iterdir() if p.is_dir()]):
            item = ListItem(Label(p.name))
            setattr(item, "path", p)
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        p = getattr(event.item, "path", None)
        self.dismiss(p if isinstance(p, Path) else None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)

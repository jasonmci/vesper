from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Label, ListItem, ListView


def _walk_files(base: Path) -> Iterable[Path]:
    for p in base.rglob("*"):
        if p.is_file():
            yield p


def _score_subsequence(needle: str, hay: str) -> int:
    if not needle:
        return 0
    i = 0
    score = 0
    last = -2
    for j, ch in enumerate(hay):
        if i < len(needle) and ch.lower() == needle[i].lower():
            score += 1
            if j == 0 or hay[j - 1] in ("/", "-", "_", " "):
                score += 2
            if j == last + 1:
                score += 1
            last = j
            i += 1
            if i == len(needle):
                return score
    return -1


class QuickOpenPanel(Vertical):
    def __init__(self, base: Path, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self._base = base
        self._all: List[Tuple[int, Path]] = []

    def compose(self) -> ComposeResult:
        yield Label("Quick Open", classes="panel-title")
        yield Input(placeholder="Type to filter…", id="qo-panel-input")
        yield ListView(id="qo-panel-list")

    def on_mount(self) -> None:
        self._reindex()
        self.query_one(Input).focus()

    def refresh_base(self, base: Path) -> None:
        self._base = base
        self._reindex()
        self._refresh_list("")

    def _reindex(self) -> None:
        self._all = [(0, p) for p in sorted(_walk_files(self._base))]

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh_list(event.value or "")

    def _refresh_list(self, needle: str) -> None:
        lv = self.query_one(ListView)
        lv.clear()
        ranked: List[Tuple[int, Path]] = []
        for _, p in self._all:
            rel = str(p.relative_to(self._base))
            s = _score_subsequence(needle, rel)
            if s >= 0:
                ranked.append((s, p))
        ranked.sort(key=lambda t: (-t[0], str(t[1])))
        for _, p in ranked[:200]:
            it = ListItem(Label(str(p.relative_to(self._base))))
            setattr(it, "path", p)
            lv.append(it)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        p = getattr(event.item, "path", None)
        if p:
            # Ask editor to open the file
            try:
                from vesper.screens.editor import EditorView

                ed = self.app.query_one("#editor-view", EditorView)
                ed.load_file(p)
            except Exception:
                pass

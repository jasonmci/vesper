# src/vesper/app.py
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from vesper.screens.editor import EditorView
from vesper.screens.outliner import OutlinerView
from vesper.screens.stats import StatsView
from vesper.screens.tasks import TasksView

from .screens import PathPrompt


class VesperApp(App):
    BINDINGS = [
        Binding("ctrl+n", "new_file", "New"),
        Binding("ctrl+o", "open_file", "Open"),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("ctrl+shift+s", "save_file_as", "Save As"),
    ]

    # Inline CSS (could be moved to external .tcss later)
    CSS = """
    TabbedContent { height: 1fr; }
    TabPane { padding: 1; }

    /* Center the editor column */
    #editor-view {
        width: 100%;
        height: 1fr;
        align: center top;
        overflow: auto;
    }

    /* Wrapper inside editor for constraining width */
    #editor-wrapper {
        width: auto;              /* shrink to contents (Textual will min-fit) */
        max-width: 90;            /* safety cap if terminal is tiny */
        height: 1fr;
        margin: 1;           /* horizontal centering */
        padding: 0 1;             /* a little breathing room */
    }

    /* The actual text area width: 88 chars target + gutter for line numbers */
    #editor-textarea {
        width: 88;                /* content width (characters) */
        max-width: 88;
        min-width: 88;
        height: 1fr;
        border: solid $surface-lighten-2;
        background: $surface-darken-1;
    }

    /* Line numbers dimmed */
    TextArea .text-area--line-number {
        color: $text-muted;
        text-style: dim;
    }

    .screen-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $primary;
    }

    #editor-status {
        dock: bottom;
        height: auto;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="editor"):
            with TabPane("Editor", id="editor"):
                yield EditorView(id="editor-view")
            with TabPane("Outliner", id="outliner"):
                yield OutlinerView()
            with TabPane("Tasks", id="tasks"):
                yield TasksView()
            with TabPane("Stats", id="stats"):
                yield StatsView()
        yield Footer(show_command_palette=True)

    def on_mount(self) -> None:
        # fire every 15s; keep a handle if you ever want to pause/cancel
        self._autosave_timer = self.set_interval(
            15, self._autosave_tick, name="autosave"
        )
        self._autosave_inflight = False

    # Helper to grab the editor widget
    def editor(self) -> EditorView:
        return self.query_one("#editor-view", EditorView)

    # ---------------- Actions (sync) ----------------

    def action_new_file(self) -> None:
        self.editor().new_file()

    def action_open_file(self) -> None:
        # Kick off a worker that awaits the modal and then loads the file
        self.run_worker(self._open_file_worker())

    def action_save_file(self) -> None:
        try:
            self.editor().save_file()  # uses current_path; raises if None
            self.notify("Saved")
        except FileNotFoundError:
            # No current path → fall back to Save As via worker
            self.run_worker(self._save_file_as_worker())
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def action_save_file_as(self) -> None:
        # Start a worker that awaits the modal and saves to the chosen path
        self.run_worker(self._save_file_as_worker())

    def _autosave_tick(self) -> None:
        # Skip if a previous autosave is still running
        if self._autosave_inflight:
            return
        self._autosave_inflight = True
        self.run_worker(self._autosave_worker(), name="autosave")

    async def _autosave_worker(self) -> None:
        try:
            ed = self.editor()
            # Only autosave when there are changes AND we know where to save
            if getattr(ed, "dirty", False) and getattr(ed, "current_path", None):
                try:
                    ed.save_file(mark_clean=False)  # don’t clear the “dirty” dot
                    # optional: subtle feedback (avoid spamming notifications)
                    # self.sub_title = f"Auto-saved"
                except Exception as e:
                    self.notify(f"Auto-save failed: {e}", severity="warning")
        finally:
            self._autosave_inflight = False

    # ---------------- Workers (async) ----------------

    async def _open_file_worker(self) -> None:
        default = str(self.editor().current_path) if self.editor().current_path else ""
        path = await self.push_screen_wait(
            PathPrompt("Open file…", "Enter path to open", default)
        )
        if not path:
            return
        try:
            self.editor().load_file(path)
            self.notify(f"Opened {path}")
        except Exception as e:
            self.notify(f"Open failed: {e}", severity="error")

    async def _save_file_as_worker(self) -> None:
        default = str(self.editor().current_path) if self.editor().current_path else ""
        path = await self.push_screen_wait(
            PathPrompt("Save file as…", "Enter path to save", default)
        )
        if not path:
            return
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            self.editor().save_file(p)
            self.notify(f"Saved to {p}")
        except Exception as e:
            self.notify(f"Save As failed: {e}", severity="error")

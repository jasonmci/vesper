# src/vesper/app.py
from __future__ import annotations

import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from vesper.screens.editor import EditorView
from vesper.screens.outliner import OutlinerView
from vesper.screens.stats import StatsView
from vesper.screens.tasks import TasksView

from .screens import PathPrompt

SETTINGS_DIR = Path.home() / ".vesper"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def _load_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_settings(data: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ensure_project_skeleton(root: Path) -> None:
    # Create a simple structure you can grow later
    for sub in ("chapters", "notes", "characters", "research"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    # Optional README so the folder isn’t empty in git:
    (root / "README.md").touch(exist_ok=True)


class VesperApp(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+n", "new_file", "New"),
        Binding("ctrl+o", "open_file", "Open"),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("ctrl+shift+s", "save_file_as", "Save As"),
        Binding("ctrl+shift+p", "set_project", "Set Project"),
        Binding("ctrl+shift+n", "new_project_file", "New File in Project"),
    ]

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str).expanduser()
        if not p.is_absolute() and self.project_root:
            p = self.project_root / p
        return p

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

        self.project_root: Path | None = None

        settings = _load_settings()
        last = settings.get("last_project")
        if last:
            p = Path(last).expanduser()
            if p.is_dir():
                self.project_root = p
                self.sub_title = f"Project: {p}"

    # Helper to grab the editor widget
    def editor(self) -> EditorView:
        return self.query_one("#editor-view", EditorView)

    # ---------------- Actions (sync) ----------------

    def action_set_project(self) -> None:
        self.run_worker(self._set_project_worker())

    async def _set_project_worker(self) -> None:
        default = str(self.project_root) if self.project_root else ""
        # Reuse PathPrompt for a folder path
        root_str = await self.push_screen_wait(
            PathPrompt("Select project folder…", "Enter folder path", default)
        )
        if not root_str:
            return
        root = Path(root_str).expanduser()
        try:
            root.mkdir(parents=True, exist_ok=True)
            _ensure_project_skeleton(root)
            self.project_root = root
            self.sub_title = f"Project: {root}"
            s = _load_settings()
            s["last_project"] = str(root)
            _save_settings(s)
            self.notify(f"Project set to {root}")
        except Exception as e:
            self.notify(f"Set Project failed: {e}", severity="error")

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
        # default directory
        if self.editor().current_path:
            default = str(self.editor().current_path)
        elif self.project_root:
            default = str(self.project_root / "chapters")
        else:
            default = ""
        path = await self.push_screen_wait(
            PathPrompt("Open file…", "Enter path to open", default)
        )
        if not path:
            return
        try:
            self.editor().load_file(self._resolve_path(path))
            self.notify(f"Opened {path}")
        except Exception as e:
            self.notify(f"Open failed: {e}", severity="error")

    async def _save_file_as_worker(self) -> None:
        # default filename suggestion
        if self.editor().current_path:
            default = str(self.editor().current_path)
        elif self.project_root:
            default = str(self.project_root / "chapters/untitled.md")
        else:
            default = "untitled.md"

        path = await self.push_screen_wait(
            PathPrompt("Save file as…", "Enter path to save", default)
        )
        if not path:
            return
        try:
            p = self._resolve_path(path)
            # add .md if you forgot an extension
            if p.suffix == "":
                p = p.with_suffix(".md")
            p.parent.mkdir(parents=True, exist_ok=True)
            self.editor().save_file(p)
            self.notify(f"Saved to {p}")
        except Exception as e:
            self.notify(f"Save As failed: {e}", severity="error")

    def action_new_project_file(self) -> None:
        self.run_worker(self._new_project_file_worker())

    async def _new_project_file_worker(self) -> None:
        base = self.project_root / "chapters" if self.project_root else Path(".")
        default = str(base / "untitled.md")
        path = await self.push_screen_wait(
            PathPrompt(
                "New file in project…",
                "Enter relative or absolute path",
                default,
            )
        )
        if not path:
            return
        p = self._resolve_path(path)
        if p.suffix == "":
            p = p.with_suffix(".md")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(exist_ok=True)
            self.editor().new_file()
            self.editor().current_path = p
            self.editor().save_file(p)  # create on disk immediately
            self.notify(f"Created {p}")
        except Exception as e:
            self.notify(f"New file failed: {e}", severity="error")

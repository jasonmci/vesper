# src/vesper/app.py
from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from vesper.screens.board import BoardView
from vesper.screens.editor import EditorView
from vesper.screens.outliner import OutlinerView
from vesper.screens.stats import StatsView
from vesper.screens.tasks import TasksView
from vesper.services.paths import preferred_content_dir

from .screens import PathPrompt

SETTINGS_DIR = Path.home() / ".vesper"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
LOG_FILE = SETTINGS_DIR / "vesper.log"


def _load_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_settings(data: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# Basic rotating file logger so toasts are captured for troubleshooting
_LOGGER = logging.getLogger("vesper")
if not _LOGGER.handlers:
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        _handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        _handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        _LOGGER.setLevel(logging.INFO)
        _LOGGER.addHandler(_handler)
        _LOGGER.propagate = False
    except Exception as e:
        # Fall back to basic stderr logging; record why file logging is disabled.
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("vesper").warning("File logging disabled: %s", str(e))


def _ensure_project_skeleton(root: Path) -> None:
    # Create a simple structure you can grow later
    for sub in (
        "chapters",  # preferred content dir
        "background",
        "balderdash",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    # Optional README so the folder isn’t empty in git:
    (root / "README.md").touch(exist_ok=True)


def _preferred_content_dir(root: Path | None) -> Path:
    # Temporary shim to avoid breaking imports; use shared helper
    return preferred_content_dir(root)


class VesperApp(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+n", "new_file", "New"),
        Binding("ctrl+o", "open_file", "Open"),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("ctrl+shift+s", "save_file_as", "Save As"),
        Binding("ctrl+shift+p", "set_project", "Set Project"),
        Binding("ctrl+shift+n", "new_project_file", "New File in Project"),
        Binding("ctrl+b", "toggle_file_list", "Files"),
        Binding("ctrl+shift+g", "commit_project", "Commit All"),
        Binding("ctrl+shift+r", "set_projects_root", "Set Projects Root"),
        Binding("ctrl+shift+j", "choose_project", "Choose Project"),
        Binding("ctrl+shift+l", "configure_llm", "LLM Settings"),
    ]

    # Mirror toast notifications to a local logfile for later inspection
    def notify(self, message: str, *args, **kwargs) -> None:  # type: ignore[override]
        severity = kwargs.get("severity", "information")
        super().notify(message, *args, **kwargs)
        lvl = (
            logging.ERROR
            if severity == "error"
            else logging.WARNING
            if severity == "warning"
            else logging.INFO
        )
        _LOGGER.log(lvl, message)

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str).expanduser()
        if not p.is_absolute() and self.project_root:
            # If user includes the project folder at the start, drop it
            if p.parts and p.parts[0] == self.project_root.name:
                p = Path(*p.parts[1:])
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
            with TabPane("Board", id="board"):
                yield BoardView()
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
        settings = _load_settings()
        projects_root = settings.get("projects_root")
        pr_path = Path(projects_root).expanduser() if projects_root else None
        default = (
            str(self.project_root)
            if self.project_root
            else (str(pr_path) if pr_path else "")
        )
        # Reuse PathPrompt for a folder path
        root_str = await self.push_screen_wait(
            PathPrompt("Select project folder…", "Enter folder path", default)
        )
        if not root_str:
            return
        entered = Path(root_str).expanduser()
        # If user entered a relative path and a Projects Root is configured,
        # create the project inside Projects Root; otherwise use as-is.
        if not entered.is_absolute() and pr_path and pr_path.is_dir():
            root = pr_path / entered
        else:
            root = entered
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
        # Safely notify views without raising if they are missing
        outliner = next(iter(self.query(OutlinerView)), None)
        if outliner:
            outliner.reload_outline_from_disk()
        board = next(iter(self.query(BoardView)), None)
        if board:
            board.action_refresh()

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
            # Only autosave when there are changes, we know where to save,
            # and the editor has been idle for at least 15 seconds.
            if (
                getattr(ed, "current_path", None)
                and getattr(ed, "should_autosave", None)
                and ed.should_autosave(15.0)
            ):
                try:
                    ed.save_file(mark_clean=True)
                except Exception as e:
                    self.notify(f"Auto-save failed: {e}", severity="warning")
        finally:
            self._autosave_inflight = False

    # ---------------- Workers (async) ----------------

    async def _open_file_worker(self) -> None:
        base = self.project_root or Path(".")
        try:
            from vesper.screens.file_tree import FileTreePicker

            selected = await self.push_screen_wait(FileTreePicker(base))
            if not selected:
                return
            self.editor().load_file(selected)
            self.notify(f"Opened {selected}")
        except Exception as e:
            self.notify(f"Open failed: {e}", severity="error")

    async def _save_file_as_worker(self) -> None:
        # default filename suggestion
        if self.editor().current_path:
            default = str(self.editor().current_path)
        elif self.project_root:
            default = str(_preferred_content_dir(self.project_root) / "untitled.md")
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
        base = (
            preferred_content_dir(self.project_root) if self.project_root else Path(".")
        )
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

    # -------- Optional integrations --------

    def action_toggle_file_list(self) -> None:
        ed = self.editor()
        toggle = getattr(ed, "toggle_file_list", None)
        if callable(toggle):
            toggle()

    # ---- Projects root & chooser ----

    def action_set_projects_root(self) -> None:
        self.run_worker(self._set_projects_root_worker())

    async def _set_projects_root_worker(self) -> None:
        current = _load_settings().get("projects_root", "")
        root_str = await self.push_screen_wait(
            PathPrompt("Set projects root…", "Enter folder path", current)
        )
        if not root_str:
            return
        root = Path(root_str).expanduser()
        try:
            root.mkdir(parents=True, exist_ok=True)
            s = _load_settings()
            s["projects_root"] = str(root)
            _save_settings(s)
            self.notify(f"Projects root set to {root}")
        except Exception as e:
            self.notify(f"Set projects root failed: {e}", severity="error")

    def action_choose_project(self) -> None:
        self.run_worker(self._choose_project_worker())

    async def _choose_project_worker(self) -> None:
        settings = _load_settings()
        base = Path(settings.get("projects_root", "")).expanduser()
        if not base.exists() or not base.is_dir():
            self.notify("Set projects root first (Ctrl+Shift+R)", severity="warning")
            return
        try:
            from vesper.screens.project_picker import ProjectPicker

            chosen = await self.push_screen_wait(ProjectPicker(base))
            if not chosen:
                return
            # update and load
            s = _load_settings()
            s["last_project"] = str(chosen)
            _save_settings(s)
            self.project_root = chosen
            self.sub_title = f"Project: {chosen}"
            # nudge views
            outliner = next(iter(self.query(OutlinerView)), None)
            if outliner:
                outliner.reload_outline_from_disk()
            board = next(iter(self.query(BoardView)), None)
            if board:
                board.action_refresh()
        except Exception as e:
            self.notify(f"Choose project failed: {e}", severity="error")

    def action_commit_project(self) -> None:
        # Commit all changes in the repo; no project required.
        self.run_worker(self._commit_project_worker())

    async def _commit_project_worker(self) -> None:
        try:
            from vesper.services.git import commit_project_changes

            settings = _load_settings()
            projects_root = settings.get("projects_root")
            repo_root: Path
            if projects_root:
                candidate = Path(projects_root).expanduser()
                if candidate.exists() and candidate.is_dir():
                    repo_root = candidate
                elif self.project_root and self.project_root.exists():
                    repo_root = self.project_root
                else:
                    repo_root = Path.cwd()
            else:
                repo_root = self.project_root if self.project_root else Path.cwd()

            # Flush: commit all changes in repo (no project scoping)
            res = commit_project_changes(repo_root, project_path=None)
            sev = res.get("severity", "information")
            # type: ignore[arg-type] for textual notify
            self.notify(res["message"], severity=sev)  # type: ignore[arg-type]
        except Exception as e:
            self.notify(f"Commit failed: {e}", severity="error")

    # ---- LLM Settings ---------------------------------------------------

    def action_configure_llm(self) -> None:
        self.run_worker(self._configure_llm_worker())

    async def _configure_llm_worker(self) -> None:
        try:
            s = _load_settings()
            # Provider (fixed to openai for now)
            provider = "openai"
            # API key prompt
            current_key = s.get("openai.api_key", "")
            key = await self.push_screen_wait(
                PathPrompt(
                    "Set OpenAI API key…",
                    "Enter API key (stored in ~/.vesper/settings.json)",
                    current_key,
                )
            )
            if key is None:
                self.notify("OpenAI key unchanged")
                return
            # Model prompt
            current_model = s.get("openai.model", "gpt-4o-mini")
            model = await self.push_screen_wait(
                PathPrompt(
                    "Set OpenAI model…",
                    "e.g., gpt-4o-mini",
                    current_model,
                )
            )
            if model is None:
                self.notify("Model unchanged; keeping existing")
                model = current_model

            # Persist
            s["llm.enabled"] = bool(key.strip())
            s["llm.provider"] = provider
            s["openai.api_key"] = key.strip()
            s["openai.model"] = model.strip() or current_model
            _save_settings(s)
            state = "enabled" if s["llm.enabled"] else "disabled"
            self.notify(f"LLM settings saved ({state})")
        except Exception as e:
            self.notify(f"LLM settings failed: {e}", severity="error")

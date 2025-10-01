"""Main Vesper application using Textual."""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, TabbedContent, TabPane

from vesper.screens.editor import EditorScreen
from vesper.screens.outliner import OutlinerScreen
from vesper.screens.stats import StatsScreen
from vesper.screens.tasks import TasksScreen


class VesperApp(App):
    """Main Vesper application."""

    CSS = """
    TabbedContent {
        height: 1fr;
    }

    TabPane {
        padding: 1;
    }

    /* Stats screen styling */
    .stats-cards {
        height: auto;
        margin-bottom: 1;
    }

    .stat-card {
        border: solid $primary;
        padding: 1;
        margin: 0 1;
        width: 1fr;
        height: auto;
    }

    .card-title {
        color: $text-muted;
        text-style: bold;
    }

    .card-value {
        text-style: bold;
        color: $primary;
        text-align: center;
    }

    .card-trend {
        color: $success;
        text-align: center;
    }

    .stats-grid {
        grid-size: 2 1;
        grid-gutter: 1 1;
        height: auto;
        margin-bottom: 1;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .progress-section, .activity-section {
        border: solid $surface-lighten-1;
        padding: 1;
    }

    .recent-activity {
        border: solid $surface-lighten-1;
        padding: 1;
        height: auto;
    }

    .activity-list {
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+n", "new_file", "New"),
        ("ctrl+o", "open_file", "Open"),
        ("ctrl+s", "save_file", "Save"),
        ("f1", "show_help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.initial_file: str | None = None
        self.initial_mode: str = "editor"

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header(show_clock=True)

        with TabbedContent(initial="editor"):
            with TabPane("Editor", id="editor"):
                yield EditorScreen()
            with TabPane("Outliner", id="outliner"):
                yield OutlinerScreen()
            with TabPane("Tasks", id="tasks"):
                yield TasksScreen()
            with TabPane("Stats", id="stats"):
                yield StatsScreen()

        yield Footer()

    def on_mount(self) -> None:
        """Handle application mount."""
        self.title = "Vesper"
        self.sub_title = "Text Editor • Outliner • Task Tracker • Dashboard"

    def action_new_file(self) -> None:
        """Create a new file."""
        # TODO: Implement new file functionality
        pass

    def action_open_file(self) -> None:
        """Open a file."""
        # TODO: Implement file opening functionality
        pass

    def action_save_file(self) -> None:
        """Save the current file."""
        # TODO: Implement file saving functionality
        pass

    def action_show_help(self) -> None:
        """Show help information."""
        # TODO: Implement help screen
        pass


if __name__ == "__main__":
    app = VesperApp()
    app.run()

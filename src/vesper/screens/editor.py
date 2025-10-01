"""
Editor screen for text editing functionality.
"""

from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static, TextArea


class EditorScreen(Widget):
    """Text editor screen component."""

    def compose(self):
        """Compose the editor layout."""
        with Vertical():
            yield Static("📝 Text Editor", classes="screen-title")
            yield TextArea(
                text="# Welcome to Vesper Editor\n\nStart typing your content here...",
                language="markdown",
                theme="monokai",
                show_line_numbers=True,
            )

    def on_mount(self) -> None:
        """Handle editor mount."""
        text_area = self.query_one(TextArea)
        text_area.focus()

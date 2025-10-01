"""
Outliner screen for hierarchical document organization.
"""

from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, TextArea, Tree


class OutlinerScreen(Widget):
    """Outliner screen component."""

    def compose(self):
        """Compose the outliner layout."""
        with Vertical():
            yield Static("🗂️ Outliner", classes="screen-title")
            with Horizontal():
                tree = Tree("Document Outline")
                tree.root.expand()

                # Add some sample outline items
                chapter1 = tree.root.add("Chapter 1: Introduction")
                chapter1.add("1.1 Overview")
                chapter1.add("1.2 Goals")

                chapter2 = tree.root.add("Chapter 2: Implementation")
                chapter2.add("2.1 Architecture")
                chapter2.add("2.2 Components")

                yield tree
                yield TextArea(
                    text="Select an item from the outline to edit...",
                    language="markdown",
                )

    def on_mount(self) -> None:
        """Handle outliner mount."""
        tree = self.query_one(Tree)
        tree.focus()

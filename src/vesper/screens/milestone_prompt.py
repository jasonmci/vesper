from __future__ import annotations

from typing import Dict, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class MilestonePrompt(ModalScreen[Optional[Dict[str, str]]]):
    """Collect title + 4 fields for a milestone."""

    def __init__(
        self,
        heading: str = "New Milestone",
        *,
        default_title: str = "",
        default_plot: str = "",
        default_subplot: str = "",
        default_character: str = "",
        default_theme: str = "",
    ) -> None:
        super().__init__()
        self._heading = heading
        self._defaults = {
            "title": default_title,
            "plot": default_plot,
            "subplot": default_subplot,
            "character": default_character,
            "theme": default_theme,
        }

    def compose(self) -> ComposeResult:
        with Container(id="milestone-modal"):
            yield Label(self._heading, id="milestone-title")
            with Vertical(id="milestone-fields"):
                yield Input(
                    value=self._defaults["title"], placeholder="Title", id="ms-title"
                )
                yield Input(
                    value=self._defaults["plot"], placeholder="Plot", id="ms-plot"
                )
                yield Input(
                    value=self._defaults["subplot"],
                    placeholder="Subplot",
                    id="ms-subplot",
                )
                yield Input(
                    value=self._defaults["character"],
                    placeholder="Character",
                    id="ms-character",
                )
                yield Input(
                    value=self._defaults["theme"], placeholder="Theme", id="ms-theme"
                )
            with Horizontal(id="milestone-buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#ms-title", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self._collect())
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Pressing Enter on any field will submit
        self.dismiss(self._collect())

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)

    def _collect(self) -> Dict[str, str]:
        return {
            "title": self.query_one("#ms-title", Input).value.strip(),
            "plot": self.query_one("#ms-plot", Input).value.strip(),
            "subplot": self.query_one("#ms-subplot", Input).value.strip(),
            "character": self.query_one("#ms-character", Input).value.strip(),
            "theme": self.query_one("#ms-theme", Input).value.strip(),
        }

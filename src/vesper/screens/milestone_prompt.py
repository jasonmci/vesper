# src/vesper/screens/milestone_prompt.py
from __future__ import annotations

from typing import Dict, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea


class MilestonePrompt(ModalScreen[Optional[Dict[str, str]]]):
    """Collect title + 4 multiline fields for a milestone."""

    def __init__(
        self,
        heading: str = "Milestone",
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

            # fields area (no nested scroll)
            with Vertical(id="milestone-fields"):
                yield Label("Title", classes="field-label")
                yield Input(
                    value=self._defaults["title"], placeholder="Title", id="ms-title"
                )

                yield Label("Plot", classes="field-label")
                yield TextArea(text=self._defaults["plot"], id="ms-plot")

                yield Label("Subplot", classes="field-label")
                yield TextArea(text=self._defaults["subplot"], id="ms-subplot")

                yield Label("Character", classes="field-label")
                yield TextArea(text=self._defaults["character"], id="ms-character")

                yield Label("Theme", classes="field-label")
                yield TextArea(text=self._defaults["theme"], id="ms-theme")

            with Horizontal(id="milestone-buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        # Focus title first
        self.query_one("#ms-title", Input).focus()

        # Enable wrapping on TextAreas where supported by your Textual version
        for field_id in ("#ms-plot", "#ms-subplot", "#ms-character", "#ms-theme"):
            ta = self.query_one(field_id, TextArea)
            # Some Textual versions expose .wrap, others .soft_wrap; prefer
            # capability checks
            if hasattr(ta, "wrap"):
                setattr(ta, "wrap", True)
            elif hasattr(ta, "soft_wrap"):
                setattr(ta, "soft_wrap", True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(self._collect() if event.button.id == "ok" else None)

    def on_key(self, event) -> None:
        # Esc cancels; Ctrl/Cmd+Enter confirms from any field
        if event.key == "escape":
            self.dismiss(None)
        if event.key == "enter" and (event.ctrl or getattr(event, "meta", False)):
            self.dismiss(self._collect())

    def _collect(self) -> Dict[str, str]:
        return {
            "title": self.query_one("#ms-title", Input).value.strip(),
            "plot": self.query_one("#ms-plot", TextArea).text.rstrip(),
            "subplot": self.query_one("#ms-subplot", TextArea).text.rstrip(),
            "character": self.query_one("#ms-character", TextArea).text.rstrip(),
            "theme": self.query_one("#ms-theme", TextArea).text.rstrip(),
        }

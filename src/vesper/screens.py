# src/vesper/screens.py
from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class PathPrompt(ModalScreen[Optional[str]]):
    """Simple modal to capture a file path; returns the string or None."""

    def __init__(self, title: str, placeholder: str = "", default: str = "") -> None:
        super().__init__()
        self._title = title
        self._placeholder = placeholder
        self._default = default

    def compose(self) -> ComposeResult:
        with Container(id="path-modal"):
            yield Label(self._title, id="path-title")
            yield Input(
                placeholder=self._placeholder, value=self._default, id="path-input"
            )
            with Horizontal(id="path-buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self.query_one(Input).value.strip() or None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)

    def on_key(self, event) -> None:  # Esc to cancel
        if event.key == "escape":
            self.dismiss(None)
